#!/usr/bin/env python3
"""Preflight a rendered TikTok ad asset against TikTok's technical specs.

Checks what a parser can check better than a person: resolution, aspect ratio,
duration, bitrate, file size, audio presence, and how much of the runtime is
effectively frozen (TikTok requires motion and caps static content at 50%).

It also renders a safe-zone overlay onto a real frame, because text placement is
the one thing that genuinely needs a human eye — TikTok's caption block, CTA
button and icon rail cover more of the frame than people expect.

Requires ffmpeg and ffprobe on PATH.

Usage:
    preflight_media.py ad.mp4
    preflight_media.py ad.mp4 --format in-feed --overlay out/safezone.png
    preflight_media.py banner.jpg --format image
    preflight_media.py ad.mp4 --json
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

# Safe-zone margins as fractions of frame, from the 1080x1920 working envelope in
# references/specs-and-safe-zones.md. Practitioner figures, deliberately conservative;
# TikTok's own downloadable templates are authoritative when the stakes are high.
SAFE = dict(top=200 / 1920, bottom=500 / 1920, left=64 / 1080,
            right=140 / 1080, right_lower=300 / 1080)

VIDEO_EXT = {".mp4", ".mov", ".mpeg", ".mpg", ".3gp", ".avi", ".m4v", ".webm", ".mkv"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}

ALLOWED_VIDEO_CONTAINERS = {"mp4", "mov", "mpeg", "3gp", "avi"}
ALLOWED_IMAGE_FORMATS = {"jpg", "jpeg", "png"}

RATIOS = {"9:16": 9 / 16, "1:1": 1.0, "16:9": 16 / 9}
MIN_DIMS = {"9:16": (540, 960), "1:1": (640, 640), "16:9": (960, 540)}
MIN_DIMS_IMAGE = {"9:16": (720, 1280), "1:1": (640, 640), "16:9": (1280, 720)}


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


def classify_ratio(w, h):
    """Return (label, actual_ratio, deviation) for the closest standard ratio."""
    actual = w / h
    label, dev = min(((k, abs(actual - v) / v) for k, v in RATIOS.items()), key=lambda t: t[1])
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


def check_video(path, info, fmt, c):
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    f = info["format"]

    if not v:
        c.fail("video stream", "no video stream found")
        return None

    w, h = int(v["width"]), int(v["height"])
    duration = float(f.get("duration") or v.get("duration") or 0)
    size_mb = int(f.get("size", 0)) / 1_048_576
    bitrate_kbps = int(f.get("bit_rate", 0)) / 1000 if f.get("bit_rate") else 0
    containers = set(f.get("format_name", "").split(","))

    # Container
    if containers & ALLOWED_VIDEO_CONTAINERS or containers & {"mov", "m4a", "3gp", "mj2"}:
        c.ok("container", f.get("format_name", "?"))
    else:
        c.fail("container", f"{f.get('format_name')} — accepted: .mp4, .mov, .mpeg, .3gp, .avi",
               "Video ad specs")

    # Resolution and aspect ratio
    label, actual, dev = classify_ratio(w, h)
    if dev <= 0.02:
        note = " (recommended)" if label == "9:16" else ""
        c.ok("aspect ratio", f"{w}×{h} ≈ {label}{note}")
        if label != "9:16":
            c.warn("orientation", f"{label} is accepted but 9:16 vertical is recommended and "
                                  "performs better in feed", "Video ad specs")
        mw, mh = MIN_DIMS[label]
        if w >= mw and h >= mh:
            c.ok("resolution", f"{w}×{h} (minimum {mw}×{mh})")
        else:
            c.fail("resolution", f"{w}×{h} is below the {mw}×{mh} minimum for {label}",
                   "Video ad specs")
        if label == "9:16" and (w < 1080 or h < 1920):
            c.warn("resolution", f"{w}×{h} meets the minimum but 1080×1920 is recommended")
    else:
        c.fail("aspect ratio", f"{w}×{h} ({actual:.3f}) is not 9:16, 1:1 or 16:9 — "
                               "non-standard ratios get letterboxed or rejected",
               "Ad format and functionality")

    # Duration — policy says 5–60s, the spec sheet accepts up to 10 minutes
    if duration == 0:
        c.warn("duration", "could not be determined")
    elif duration < 5:
        c.fail("duration", f"{duration:.1f}s — policy minimum is 5s",
               "Ad format and functionality")
    elif duration <= 60:
        c.ok("duration", f"{duration:.1f}s (policy window 5–60s)")
    elif fmt == "spark":
        c.info("duration", f"{duration:.1f}s — Spark Ads have no duration restriction")
    else:
        c.warn("duration", f"{duration:.1f}s exceeds the 60s stated in the Ad Format policy. "
                           "The spec sheet accepts up to 10 min, so it will upload, but it "
                           "carries review risk", "Ad format and functionality")

    # File size and bitrate
    if size_mb <= 500:
        c.ok("file size", f"{size_mb:.1f} MB (limit 500 MB)")
    else:
        c.fail("file size", f"{size_mb:.1f} MB exceeds the 500 MB limit", "Video ad specs")

    if bitrate_kbps == 0:
        c.warn("bitrate", "could not be determined")
    elif bitrate_kbps >= 516:
        c.ok("bitrate", f"{bitrate_kbps:.0f} kbps (minimum 516 kbps)")
    else:
        c.fail("bitrate", f"{bitrate_kbps:.0f} kbps is below the 516 kbps minimum",
               "Video ad specs")

    # Audio is mandatory
    if a:
        abr = int(a.get("bit_rate", 0)) / 1000 if a.get("bit_rate") else 0
        detail = f"{a.get('codec_name')} " + (f"{abr:.0f} kbps" if abr else "(bitrate unknown)")
        c.ok("audio present", detail)
        if abr and abr < 64:
            c.warn("audio quality", f"{abr:.0f} kbps is low — policy rejects unclear or muffled sound",
                   "Ad format and functionality")
    else:
        c.fail("audio present", "no audio stream — TikTok requires audio and rejects silent ads",
               "Ad format and functionality")

    # Motion requirement
    fr = freeze_ratio(path, duration)
    if fr is None:
        c.warn("motion", "could not measure frozen runtime")
    elif fr > 0.5:
        c.fail("motion", f"~{fr * 100:.0f}% of the runtime is frozen — static content may not "
                         "exceed 50% and the ad cannot be motionless",
               "Ad format and functionality")
    elif fr > 0.25:
        c.warn("motion", f"~{fr * 100:.0f}% of the runtime is frozen — under the 50% cap but "
                         "worth adding movement")
    else:
        c.ok("motion", f"~{fr * 100:.0f}% of runtime frozen (cap is 50%)")

    return dict(width=w, height=h, duration=duration, size_mb=size_mb,
                bitrate_kbps=bitrate_kbps, has_audio=bool(a), freeze_ratio=fr)


def check_image(path, info, c):
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    f = info["format"]
    if not v:
        c.fail("image stream", "could not read image")
        return None

    w, h = int(v["width"]), int(v["height"])
    size_mb = int(f.get("size", 0)) / 1_048_576
    ext = os.path.splitext(path)[1].lower().lstrip(".")

    if ext in ALLOWED_IMAGE_FORMATS:
        c.ok("format", f".{ext}")
    else:
        c.fail("format", f".{ext} — accepted: .jpg, .jpeg, .png", "Image ad specs")

    label, actual, dev = classify_ratio(w, h)
    if dev <= 0.02:
        c.ok("aspect ratio", f"{w}×{h} ≈ {label}" + (" (recommended)" if label == "9:16" else ""))
        mw, mh = MIN_DIMS_IMAGE[label]
        if w >= mw and h >= mh:
            c.ok("resolution", f"{w}×{h} (minimum {mw}×{mh})")
        else:
            c.fail("resolution", f"{w}×{h} is below the {mw}×{mh} minimum for {label}",
                   "Image ad specs")
    else:
        c.fail("aspect ratio", f"{w}×{h} ({actual:.3f}) is not 9:16, 1:1 or 16:9", "Image ad specs")

    if size_mb <= 100:
        c.ok("file size", f"{size_mb:.1f} MB (limit 100 MB)")
    else:
        c.fail("file size", f"{size_mb:.1f} MB exceeds the 100 MB limit", "Image ad specs")

    c.info("overlaid elements", "Leave room for brand/app name, logo, skip button and CTA — "
                                "TikTok composites these over image ads")
    return dict(width=w, height=h, size_mb=size_mb)


def render_overlay(path, out, w, h, is_video, seek):
    """Shade the UI-covered regions over a real frame and outline what's safe."""
    T, B = round(h * SAFE["top"]), round(h * SAFE["bottom"])
    L, R = round(w * SAFE["left"]), round(w * SAFE["right"])
    RW = round(w * SAFE["right_lower"])
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
    p = argparse.ArgumentParser(description="Preflight a TikTok ad asset against TikTok specs.")
    p.add_argument("path", help="Rendered video or image file.")
    p.add_argument("--format", default="in-feed",
                   choices=["in-feed", "spark", "topview", "image"],
                   help="Placement the asset is for (affects duration rules).")
    p.add_argument("--overlay", metavar="OUT.png",
                   help="Write a safe-zone overlay frame here for visual review.")
    p.add_argument("--seek", type=float, default=1.0,
                   help="Timestamp (s) to grab for the overlay. Default 1.0.")
    p.add_argument("--json", action="store_true", help="Machine-readable output.")
    a = p.parse_args()

    for tool in ("ffprobe", "ffmpeg"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} not found on PATH. Install ffmpeg to run preflight.")
    if not os.path.isfile(a.path):
        raise SystemExit(f"No such file: {a.path}")

    ext = os.path.splitext(a.path)[1].lower()
    is_video = a.format != "image" and ext not in IMAGE_EXT
    info = probe(a.path)
    c = Check()

    meta = check_video(a.path, info, a.format, c) if is_video else check_image(a.path, info, c)

    overlay_info = None
    if a.overlay and meta:
        seek = min(a.seek, max(meta.get("duration", 1) - 0.1, 0)) if is_video else 0
        overlay_info, err = render_overlay(a.path, a.overlay, meta["width"], meta["height"],
                                           is_video, seek)
        if err:
            c.warn("safe-zone overlay", f"could not render: {err}")
        else:
            c.info("safe-zone overlay", f"written to {a.overlay} — open it and confirm no text or "
                                        "logo sits in the shaded areas")

    if a.json:
        print(json.dumps(dict(file=a.path, format=a.format, metadata=meta,
                              safe_zone_px=overlay_info, checks=c.items), indent=2))
    else:
        counts = {s: sum(1 for i in c.items if i["status"] == s) for s in ("FAIL", "WARN", "PASS")}
        print(f"\nTikTok media preflight — {os.path.basename(a.path)} · {a.format}")
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
