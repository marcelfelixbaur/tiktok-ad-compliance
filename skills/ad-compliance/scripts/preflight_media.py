#!/usr/bin/env python3
"""Preflight a rendered ad asset against the ad platform's technical specs.

Checks what a parser can check better than a person: resolution, aspect ratio,
duration, bitrate, file size, audio presence, and how much of the runtime is
effectively frozen (TikTok requires motion and caps static content at 50%).

It also renders a safe-zone overlay onto a real frame, because text placement is
the one thing that genuinely needs a human eye — TikTok's caption block, CTA
button and icon rail cover more of the frame than people expect.

--platform is required and has no default: specs differ by platform. Only TikTok's
specs are bundled today.

Requires ffmpeg and ffprobe on PATH.

Usage:
    preflight_media.py ad.mp4 --platform tiktok
    preflight_media.py ad.mp4 --platform tiktok --format in-feed --overlay out/safezone.png
    preflight_media.py banner.jpg --platform tiktok --format image
    preflight_media.py ad.mp4 --platform tiktok --json
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

VIDEO_EXT = {".mp4", ".mov", ".mpeg", ".mpg", ".3gp", ".avi", ".m4v", ".webm", ".mkv"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}

# Specs per platform, from references/platforms/<platform>/specs-and-safe-zones.md.
# The first format is the default.
SPECS = {
    "tiktok": dict(
        name="TikTok",
        formats=["in-feed", "spark", "topview", "image"],
        video_containers=["mp4", "mov", "mpeg", "3gp", "avi"],
        image_formats=["jpg", "jpeg", "png"],
        ratios={"9:16": 9 / 16, "1:1": 1.0, "16:9": 16 / 9},
        recommended=("9:16", 1080, 1920),
        min_dims={"9:16": (540, 960), "1:1": (640, 640), "16:9": (960, 540)},
        min_dims_image={"9:16": (720, 1280), "1:1": (640, 640), "16:9": (1280, 720)},
        # Policy says 5–60s; the spec sheet accepts up to 10 minutes.
        duration=(5, 60),
        over_duration="The spec sheet accepts up to 10 min, so it will upload, but it carries review risk",
        uncapped_formats={"spark": "Spark Ads have no duration restriction"},
        max_video_mb=500,
        max_image_mb=100,
        min_bitrate_kbps=516,
        min_audio_kbps=64,
        max_frozen=0.5,
        # Safe-zone margins as fractions of frame, from the 1080x1920 working envelope.
        # Practitioner figures, deliberately conservative; TikTok's own downloadable
        # templates are authoritative when the stakes are high.
        safe=dict(top=200 / 1920, bottom=500 / 1920, left=64 / 1080,
                  right=140 / 1080, right_lower=300 / 1080),
        policy=dict(video="Video ad specs", image="Image ad specs", format="Ad format and functionality"),
    ),
}


def listing(items, last="or"):
    """['9:16', '1:1', '16:9'] -> '9:16, 1:1 or 16:9'."""
    items = list(items)
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} {last} {items[-1]}"


class Check:
    def __init__(self):
        self.items = []

    def add(self, status, name, detail, policy=""):
        self.items.append(dict(status=status, name=name, detail=detail, policy=policy))

    ok = lambda self, n, d, p="": self.add("PASS", n, d, p)
    fail = lambda self, n, d, p="": self.add("FAIL", n, d, p)
    warn = lambda self, n, d, p="": self.add("WARN", n, d, p)
    info = lambda self, n, d, p="": self.add("INFO", n, d, p)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", path])
    if r.returncode != 0:
        raise SystemExit(f"ffprobe failed on {path}:\n{r.stderr.strip()}")
    return json.loads(r.stdout)


def classify_ratio(w, h, ratios):
    """Return (label, actual_ratio, deviation) for the closest standard ratio."""
    actual = w / h
    label, dev = min(((k, abs(actual - v) / v) for k, v in ratios.items()), key=lambda t: t[1])
    return label, actual, dev


def freeze_ratio(path, duration):
    """Fraction of runtime ffmpeg considers frozen. None if it can't be measured.

    freezedetect emits freeze_start when a freeze begins and freeze_duration when it
    ends. A freeze that runs to end-of-file never gets a duration line -- which is
    exactly the fully-static slideshow case we most need to catch -- so an unclosed
    freeze_start is credited with the remaining runtime.
    """
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
             "-vf", "freezedetect=n=-60dB:d=0.5", "-map", "0:v:0", "-f", "null", "-"])
    events = re.findall(r"freeze_(start|duration):\s*([\d.]+)", r.stderr)
    if duration is None or duration <= 0:
        return None

    frozen, open_start = 0.0, None
    for kind, value in events:
        if kind == "start":
            open_start = float(value)
        elif kind == "duration":
            frozen += float(value)
            open_start = None
    if open_start is not None:
        frozen += max(duration - open_start, 0.0)

    return min(frozen / duration, 1.0)


def audio_peak_db(path):
    """Loudest sample on the first audio stream, in dBFS. None if it can't be measured.

    An audio stream can be present and still carry nothing but silence, which review
    treats the same as no audio at all.
    """
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
             "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-"])
    m = re.search(r"max_volume:\s*(-?[\d.]+|-inf) dB", r.stderr)
    if not m:
        return None
    return float("-inf") if m.group(1) == "-inf" else float(m.group(1))


def check_video(path, info, fmt, spec, c):
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    f = info["format"]
    pol = spec["policy"]

    if not v:
        c.fail("video stream", "no video stream found")
        return None

    w, h = int(v["width"]), int(v["height"])
    duration = float(f.get("duration") or v.get("duration") or 0)
    size_mb = int(f.get("size", 0)) / 1_048_576
    bitrate_kbps = int(f.get("bit_rate", 0)) / 1000 if f.get("bit_rate") else 0
    containers = set(f.get("format_name", "").split(","))

    # Container
    if containers & set(spec["video_containers"]) or containers & {"mov", "m4a", "3gp", "mj2"}:
        c.ok("container", f.get("format_name", "?"))
    else:
        accepted = ", ".join("." + x for x in spec["video_containers"])
        c.fail("container", f"{f.get('format_name')} — accepted: {accepted}", pol["video"])

    # Resolution and aspect ratio
    rec_label, rec_w, rec_h = spec["recommended"]
    label, actual, dev = classify_ratio(w, h, spec["ratios"])
    if dev <= 0.02:
        note = " (recommended)" if label == rec_label else ""
        c.ok("aspect ratio", f"{w}×{h} ≈ {label}{note}")
        if label != rec_label:
            c.warn("orientation", f"{label} is accepted but {rec_label} vertical is recommended and "
                                  "performs better in feed", pol["video"])
        mw, mh = spec["min_dims"][label]
        if w >= mw and h >= mh:
            c.ok("resolution", f"{w}×{h} (minimum {mw}×{mh})")
        else:
            c.fail("resolution", f"{w}×{h} is below the {mw}×{mh} minimum for {label}", pol["video"])
        if label == rec_label and (w < rec_w or h < rec_h):
            c.warn("resolution", f"{w}×{h} meets the minimum but {rec_w}×{rec_h} is recommended")
    else:
        c.fail("aspect ratio", f"{w}×{h} ({actual:.3f}) is not {listing(spec['ratios'])} — "
                               "non-standard ratios get letterboxed or rejected", pol["format"])

    # Duration
    lo, hi = spec["duration"]
    if duration == 0:
        c.warn("duration", "could not be determined")
    elif duration < lo:
        c.fail("duration", f"{duration:.1f}s — policy minimum is {lo}s", pol["format"])
    elif duration <= hi:
        c.ok("duration", f"{duration:.1f}s (policy window {lo}–{hi}s)")
    elif fmt in spec["uncapped_formats"]:
        c.info("duration", f"{duration:.1f}s — {spec['uncapped_formats'][fmt]}")
    else:
        c.warn("duration", f"{duration:.1f}s exceeds the {hi}s stated in the Ad Format policy. "
                           f"{spec['over_duration']}", pol["format"])

    # File size and bitrate
    max_mb = spec["max_video_mb"]
    if size_mb <= max_mb:
        c.ok("file size", f"{size_mb:.1f} MB (limit {max_mb} MB)")
    else:
        c.fail("file size", f"{size_mb:.1f} MB exceeds the {max_mb} MB limit", pol["video"])

    min_kbps = spec["min_bitrate_kbps"]
    if bitrate_kbps == 0:
        c.warn("bitrate", "could not be determined")
    elif bitrate_kbps >= min_kbps:
        c.ok("bitrate", f"{bitrate_kbps:.0f} kbps (minimum {min_kbps} kbps)")
    else:
        c.fail("bitrate", f"{bitrate_kbps:.0f} kbps is below the {min_kbps} kbps minimum", pol["video"])

    # Audio is mandatory
    if a:
        abr = int(a.get("bit_rate", 0)) / 1000 if a.get("bit_rate") else 0
        detail = f"{a.get('codec_name')} " + (f"{abr:.0f} kbps" if abr else "(bitrate unknown)")
        c.ok("audio present", detail)
        if abr and abr < spec["min_audio_kbps"]:
            c.warn("audio quality", f"{abr:.0f} kbps is low — policy rejects unclear or muffled sound",
                   pol["format"])
        peak = audio_peak_db(path)
        if peak is None:
            c.warn("audio level", "could not measure loudness")
        elif peak <= -50:
            c.fail("audio level", f"peak {peak:.0f} dBFS — the audio track is silent, which review "
                                  "treats as no audio", pol["format"])
        elif peak < -30:
            c.warn("audio level", f"peak {peak:.0f} dBFS is very quiet — policy rejects unclear sound",
                   pol["format"])
        else:
            c.ok("audio level", f"peak {peak:.0f} dBFS")
    else:
        c.fail("audio present", f"no audio stream — {spec['name']} requires audio and rejects silent ads",
               pol["format"])

    # Motion requirement
    cap = spec["max_frozen"]
    fr = freeze_ratio(path, duration)
    if fr is None:
        c.warn("motion", "could not measure frozen runtime")
    elif fr > cap:
        c.fail("motion", f"~{fr * 100:.0f}% of the runtime is frozen — static content may not "
                         f"exceed {cap * 100:.0f}% and the ad cannot be motionless", pol["format"])
    elif fr > cap / 2:
        c.warn("motion", f"~{fr * 100:.0f}% of the runtime is frozen — under the {cap * 100:.0f}% cap but "
                         "worth adding movement")
    else:
        c.ok("motion", f"~{fr * 100:.0f}% of runtime frozen (cap is {cap * 100:.0f}%)")

    return dict(width=w, height=h, duration=duration, size_mb=size_mb,
                bitrate_kbps=bitrate_kbps, has_audio=bool(a), freeze_ratio=fr)


def check_image(path, info, spec, c):
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    f = info["format"]
    pol = spec["policy"]
    if not v:
        c.fail("image stream", "could not read image")
        return None

    w, h = int(v["width"]), int(v["height"])
    size_mb = int(f.get("size", 0)) / 1_048_576
    ext = os.path.splitext(path)[1].lower().lstrip(".")

    if ext in spec["image_formats"]:
        c.ok("format", f".{ext}")
    else:
        accepted = ", ".join("." + x for x in spec["image_formats"])
        c.fail("format", f".{ext} — accepted: {accepted}", pol["image"])

    rec_label = spec["recommended"][0]
    label, actual, dev = classify_ratio(w, h, spec["ratios"])
    if dev <= 0.02:
        c.ok("aspect ratio", f"{w}×{h} ≈ {label}" + (" (recommended)" if label == rec_label else ""))
        mw, mh = spec["min_dims_image"][label]
        if w >= mw and h >= mh:
            c.ok("resolution", f"{w}×{h} (minimum {mw}×{mh})")
        else:
            c.fail("resolution", f"{w}×{h} is below the {mw}×{mh} minimum for {label}", pol["image"])
    else:
        c.fail("aspect ratio", f"{w}×{h} ({actual:.3f}) is not {listing(spec['ratios'])}", pol["image"])

    max_mb = spec["max_image_mb"]
    if size_mb <= max_mb:
        c.ok("file size", f"{size_mb:.1f} MB (limit {max_mb} MB)")
    else:
        c.fail("file size", f"{size_mb:.1f} MB exceeds the {max_mb} MB limit", pol["image"])

    c.info("overlaid elements", "Leave room for brand/app name, logo, skip button and CTA — "
                                f"{spec['name']} composites these over image ads")
    return dict(width=w, height=h, size_mb=size_mb)


def render_overlay(path, out, w, h, is_video, seek, safe):
    """Shade the UI-covered regions over a real frame and outline what's safe."""
    T, B = round(h * safe["top"]), round(h * safe["bottom"])
    L, R = round(w * safe["left"]), round(w * safe["right"])
    RW = round(w * safe["right_lower"])
    mid = h // 2
    shade, line = "red@0.35", "lime@0.9"

    boxes = [
        f"drawbox=x=0:y=0:w={w}:h={T}:color={shade}:t=fill",
        f"drawbox=x=0:y={h - B}:w={w}:h={B}:color={shade}:t=fill",
        f"drawbox=x=0:y={T}:w={L}:h={h - T - B}:color={shade}:t=fill",
        f"drawbox=x={w - R}:y={T}:w={R}:h={mid - T}:color={shade}:t=fill",
        f"drawbox=x={w - RW}:y={mid}:w={RW}:h={h - B - mid}:color={shade}:t=fill",
        f"drawbox=x={L}:y={T}:w={w - L - R}:h={mid - T}:color={line}:t=3",
        f"drawbox=x={L}:y={mid}:w={w - L - RW}:h={h - B - mid}:color={line}:t=3",
    ]
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if is_video:
        cmd += ["-ss", str(seek)]
    cmd += ["-i", path, "-vf", ",".join(boxes), "-frames:v", "1", out]
    r = run(cmd)
    if r.returncode != 0:
        return None, r.stderr.strip()
    return dict(top=T, bottom=B, left=L, right=R, right_lower=RW), None


def main():
    p = argparse.ArgumentParser(description="Preflight an ad asset against the ad platform's specs.",
                                epilog="--platform is required. Ask the user which platform the asset "
                                       "is for; never guess.")
    p.add_argument("path", help="Rendered video or image file.")
    p.add_argument("--platform", choices=sorted(SPECS),
                   help="REQUIRED. Ad platform the asset is for. Specs are bundled for: "
                        + ", ".join(SPECS) + ".")
    p.add_argument("--format", choices=sorted({f for spec in SPECS.values() for f in spec["formats"]}),
                   help="Placement the asset is for (affects duration rules). Depends on the platform: "
                        + "; ".join(f"{k}: {', '.join(v['formats'])} (default {v['formats'][0]})"
                                    for k, v in SPECS.items()) + ".")
    p.add_argument("--overlay", metavar="OUT.png",
                   help="Write a safe-zone overlay frame here for visual review.")
    p.add_argument("--seek", type=float, default=1.0,
                   help="Timestamp (s) to grab for the overlay. Default 1.0.")
    p.add_argument("--json", action="store_true", help="Machine-readable output.")
    a = p.parse_args()

    if not a.platform:
        p.error("--platform required. Don't assume: ask the user which platform the asset is for. "
                f"Specs are bundled for: {', '.join(SPECS)}.")
    spec = SPECS[a.platform]
    a.format = a.format or spec["formats"][0]
    if a.format not in spec["formats"]:
        p.error(f"--format {a.format} isn't a {spec['name']} format. "
                f"Choose from: {', '.join(spec['formats'])}.")

    for tool in ("ffprobe", "ffmpeg"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} not found on PATH. Install ffmpeg to run preflight.")
    if not os.path.isfile(a.path):
        raise SystemExit(f"No such file: {a.path}")

    ext = os.path.splitext(a.path)[1].lower()
    is_video = a.format != "image" and ext not in IMAGE_EXT
    info = probe(a.path)
    c = Check()

    meta = (check_video(a.path, info, a.format, spec, c) if is_video
            else check_image(a.path, info, spec, c))

    overlay_info = None
    if a.overlay and meta:
        seek = min(a.seek, max(meta.get("duration", 1) - 0.1, 0)) if is_video else 0
        overlay_info, err = render_overlay(a.path, a.overlay, meta["width"], meta["height"],
                                           is_video, seek, spec["safe"])
        if err:
            c.warn("safe-zone overlay", f"could not render: {err}")
        else:
            c.info("safe-zone overlay", f"written to {a.overlay} — open it and confirm no text or "
                                        "logo sits in the shaded areas")

    if a.json:
        print(json.dumps(dict(file=a.path, platform=a.platform, format=a.format, metadata=meta,
                              safe_zone_px=overlay_info, checks=c.items), indent=2))
    else:
        counts = {s: sum(1 for i in c.items if i["status"] == s) for s in ("FAIL", "WARN", "PASS")}
        print(f"\n{spec['name']} media preflight — {os.path.basename(a.path)} · {a.format}")
        print(f"{counts['FAIL']} fail · {counts['WARN']} warn · {counts['PASS']} pass\n")
        glyph = {"PASS": "  ok  ", "FAIL": " FAIL ", "WARN": " WARN ", "INFO": " note "}
        for i in c.items:
            print(f"[{glyph[i['status']]}] {i['name']}: {i['detail']}")
            if i["policy"]:
                print(f"           ↳ {i['policy']}")
        print("\nSpecs are only part of review. Content, claims, music rights and the landing")
        print("page are judged separately — see the reference files in this skill.\n")

    return 1 if any(i["status"] == "FAIL" for i in c.items) else 0


if __name__ == "__main__":
    sys.exit(main())
