# TikTok Ad Compliance Skill

A Claude skill for making TikTok ads (video, image, animated, and Spark Ads) that pass TikTok's ad review and comply with EU advertising law.

TikTok approving an ad doesn't make it lawful. Ad review checks TikTok's own policies. It doesn't check the EU's Unfair Commercial Practices Directive, the 30-day price-reduction rule, AI Act disclosure duties, or national rules like Germany's pharmaceutical advertising law. This skill checks both layers before anything is produced.

## What it does

The skill runs three checks, cheapest first, so problems are caught before they get into a finished video:

1. **Eligibility.** It confirms the target market, product category, ad format and the advertiser's licences before any script is written. Some product categories can't be advertised at all. Others need licences, age targeting or disclaimers.
2. **Creative.** It writes the script, on-screen text, visuals, music and specs to the rules for that product category and market. Common problem claims are rewritten to say what the product does rather than what the viewer will become.
3. **Preflight.** Two bundled scripts check the finished copy and media automatically.

Output ends with a short compliance report covering the verdict, the assumptions made, the conditions the advertiser has to meet outside the ad, and open questions.

## Coverage

| Layer | Scope |
|---|---|
| TikTok platform policy | Global, with market-specific exceptions where TikTok publishes them |
| Legal layer | **EU and EEA only**: UCPD, green claims (Directive (EU) 2024/825), price-reduction rule (Art. 6a PID), AI Act Art. 50, DSA, GDPR/ePrivacy, EU health and cosmetics claim rules, TTPA, influencer disclosure, and notes for FR, DE, IT, SE, NO, GR and ES |

**Not covered:** the laws of the US, UK, and every market outside the EU and EEA. The skill says so when a campaign targets those markets instead of implying the platform check is enough. The UK is deliberately excluded because its rules (UK GDPR, the CAP/BCAP Codes, DMCCA 2024) are similar in spirit to the EU's but differ in detail.

## Contents

```
tiktok-ad-compliance/
├── SKILL.md                          workflow: eligibility → creative → preflight
├── references/
│   ├── restricted-verticals.md       prohibited and restricted categories, age limits, disclaimers
│   ├── claims-and-copy.md            misleading claims, clickbait, AI-content labels, rewrite patterns
│   ├── creative-and-format.md        quality and motion rules, on-screen content, landing pages
│   ├── music-and-ip.md               Commercial Music Library, licensing, likeness, trademarks
│   ├── specs-and-safe-zones.md       specs, character limits, safe zones
│   └── eu-law.md                     EU/EEA legal layer
├── scripts/
│   ├── lint_copy.py                  flags ad copy likely to be rejected or unlawful
│   └── preflight_media.py            checks technical specs and draws the safe-zone overlay
└── assets/
    └── compliance-report.md          handover template
```

## Install

**Claude Code:** copy the `tiktok-ad-compliance` folder into `~/.claude/skills/` to use it in every project, or into a project's `.claude/skills/` directory to use it in that project only.

```bash
git clone https://github.com/marcelfelixbaur/tiktok-ad-compliance.git
cp -r tiktok-ad-compliance/tiktok-ad-compliance ~/.claude/skills/
```

**Claude apps:** zip the `tiktok-ad-compliance` folder and upload it as a custom skill.

Once installed, the skill activates on requests like:

> Make a 15-second TikTok ad for our collagen supplement, targeting Germany and France.

> Is "eco-friendly packaging, 30% off" OK for a TikTok ad in the Netherlands?

> Our TikTok ad got rejected. Here's the script. Why?

## Using the scripts on their own

Both scripts run without Claude and exit non-zero when something blocks, so they can be used in CI.

```bash
# Copy lint. A --market with an EU/EEA country code turns on the EU legal checks.
python3 tiktok-ad-compliance/scripts/lint_copy.py --file script.txt --vertical health --market US
python3 tiktok-ad-compliance/scripts/lint_copy.py --file script.txt --market DE --creator --aigc

# Media preflight: resolution, aspect ratio, duration, bitrate, audio, static-frame share, safe zones
python3 tiktok-ad-compliance/scripts/preflight_media.py ad.mp4 --overlay safezone.png
```

The same copy can pass for `US` and fail for `DE`:

```
"Our eco-friendly serum is carbon neutral and boosts your immune
 system. 30% off, was €49. Sustainable and paraben-free."

--market US  →  0 block · 0 review
--market DE  →  3 block · 4 review   (green claims, EU health-claim wording, price rule)
```

**Requirements:** Python 3.8+ with the standard library only. `preflight_media.py` also needs `ffmpeg` and `ffprobe` on your PATH.

The linter matches known risky phrasings. It doesn't decide whether a claim is acceptable. Every flag needs a decision from a person, and a clean result doesn't mean the copy is compliant.

## Accuracy and limits

- **Not legal advice.** The legal layer is a best-effort review based on published regulation and guidance, current as of September 2026. EU directives are written into law differently in each member state. Regulated products and large campaigns need the advertiser's own lawyers.
- **Policies change.** TikTok revises its policies, and the exceptions by market change. Each reference file ends with source links. Check the live pages before a close call.
- **Safe-zone figures are estimates.** They are conservative figures used by practitioners, not numbers TikTok publishes. The downloadable safe-zone templates in TikTok Ads Manager are the authoritative source.
- **Passing every check makes approval likely, not certain.** TikTok's ad review makes its own judgment.

## Contributing

Contributions are welcome, especially:

- legal layers for other markets (US FTC, UK ASA/CAP, Australia, Brazil) as new `references/<market>-law.md` files with matching linter rule packs
- policy updates, each with a link to the TikTok or EUR-Lex source
- false positives and false negatives from the linter, with the copy that triggered them

## Disclaimer

This project is not affiliated with, endorsed by, or sponsored by TikTok or ByteDance. "TikTok" is a trademark of its owner and is used here only to describe what the skill is for.

## License

MIT
