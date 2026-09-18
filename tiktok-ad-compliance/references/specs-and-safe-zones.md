# Specs and Safe Zones

Technical requirements for export, and where TikTok's interface covers the frame.

**Contents:** [Video specs](#video-ad-specs-auction-in-feed) · [Duration](#duration-the-one-conflict-worth-knowing) · [Image specs](#image-ad-specs) · [Text limits](#text-field-limits) · [Safe zones](#safe-zones) · [Export recipe](#a-working-export-recipe) · [Sources](#sources)

## Video ad specs (auction In-Feed)

| Property | Requirement |
|---|---|
| Aspect ratio | 9:16 vertical **(recommended)**, 1:1 square, or 16:9 horizontal |
| Minimum resolution | 9:16 ≥ 540×960 · 1:1 ≥ 640×640 · 16:9 ≥ 960×540 |
| Recommended resolution | **1080×1920** for 9:16 |
| File formats | .mp4, .mov, .mpeg, .3gp, .avi |
| File size | ≤ 500 MB |
| Bitrate | ≥ 516 kbps |
| Audio | Required — a silent video is a policy rejection, not just a weak ad |
| Profile image | 98×98 px, 1:1; keep the key element within the central 66×66 px |

**Spark Ads** (boosting an organic post) accept .mp4 or .mov with no duration restriction; the caption is pulled from the organic video's caption, up to 4 lines. The organic post's music must be commercially cleared — see `music-and-ip.md`.

**Pangle** placements have their own separate creative specs and industry-entry policies; don't assume In-Feed specs carry over.

## Duration — the one conflict worth knowing

TikTok's published numbers don't agree, and both are real:

- The **Ad Format and Functionality policy** states a minimum of **5 seconds** and a maximum of **60 seconds**.
- The **auction In-Feed spec sheet** states videos are accepted **up to 10 minutes**.

The platform will accept a long file; the policy bar is 5–60s. Deliver inside **5–60 seconds** unless the user has a specific reason to go longer and accepts the review risk. In practice 9–15 seconds is where most direct-response creative lands, and the first 2 seconds carry the hook.

## Image ad specs

For image placements (Global App Bundle / CapCut / Fizzo surfaces):

| Property | Requirement |
|---|---|
| Aspect ratio | 9:16 vertical **(recommended)**, 16:9 horizontal, 1:1 square |
| Minimum resolution | 9:16 ≥ 720×1280 · 16:9 ≥ 1280×720 · 1:1 ≥ 640×640 |
| File formats | JPG, JPEG, PNG |
| File size | ≤ 100 MB |

Composition must accommodate the elements TikTok overlays: image creative, brand/app name and logo, skip-ad button, landing-page URL, and CTA button (all except App Open Ad).

## Text field limits

| Field | Limit |
|---|---|
| Brand name | 2–20 Latin characters · 1–10 Asian characters · **no emoji** |
| App name | 4–40 Latin characters · 2–20 Asian characters · **no emoji** |
| Ad description | 1–100 Latin characters · 1–50 Asian characters · no emoji, no `{ }` or `#` |
| Display account name | ≤ 20 characters (≤ 10 for CN/JP/KR) |
| Ad caption | One line shown, ~20 characters (10 for CN/JP/KR) before truncation; keep under 100 (50 for CN/JP/KR) to avoid the "See more" cut |

Punctuation and spaces count. Captions don't support clickable links, `@` mentions, or hashtags in non-Spark formats. Front-load the meaningful words — most of the caption is truncated on first view.

## Safe zones

TikTok's interface sits on top of the video: status bar and logo at the top; caption block, account name, sound rail, and CTA button across the bottom; like/comment/share/profile icons down the right edge. Anything underneath is unreadable.

**TikTok publishes official downloadable safe-zone template files** through Ads Manager, in a standard version and an Arabic-region version, plus variants for ads using anchors. Exact dimensions vary with orientation, caption length, and which additional formats are enabled. Use the official template for the specific format when the stakes are high — it's authoritative in a way the numbers below are not.

**Working envelope for 9:16 at 1080×1920**, conservative enough to survive across placements. These are widely-used practitioner figures, not published TikTok values — treat them as a safe default, not gospel:

```
┌──────────────────────────────┐  ← 1080 × 1920
│         top: 200 px          │  status bar, TikTok logo
│  ┌────────────────────────┐  │
│  │                        │  │
│  │      SAFE FOR TEXT     │  │  left 64 px · right 140 px
│  │       AND LOGOS        │  │  (right widens to ~300 px
│  │                        │  │   below the midpoint, for
│  │                        │  │   the icon rail)
│  └────────────────────────┘  │
│       bottom: 500 px         │  caption, sound rail, CTA button
└──────────────────────────────┘
```

Reported figures range from 150–240 px at the top and 440–660 px at the bottom depending on placement and caption length; the bottom danger zone expands furthest on In-Feed ads because of the CTA button. When in doubt, go tighter — a subtitle 80 px higher costs nothing, an unreadable one costs the conversion.

Rules of thumb that hold across the variants: keep critical text out of the **top ~10%**, the **bottom ~25%**, and the **right ~12%** of the frame. Centre-weight key messaging vertically. Never place a logo bottom-right.

`scripts/preflight_media.py --overlay` renders these bounds over a frame of the actual cut so placement can be checked by eye, which is the only reliable way to check it.

## A working export recipe

For a standard 9:16 In-Feed ad:

```
1080×1920 · H.264 High profile · 8–12 Mbps · 30fps (or source fps)
AAC audio, 128 kbps+, stereo, present for the full duration
.mp4 container · under 500 MB · 9–15 s
No black bars, no letterboxing, no pillarboxing
```

Then run `scripts/preflight_media.py` before handover.

## Sources

- Video ad specs: https://ads.tiktok.com/help/article/video-ads-specifications
- Image ad specs: https://ads.tiktok.com/help/article/image-ads-specification
- Ad format and functionality policy: https://ads.tiktok.com/help/article/tiktok-ads-policy-ad-format-and-functionality
- Official safe-zone templates: download from TikTok Ads Manager (standard and Arabic-region versions)
