# TikTok Ad Compliance Skill

A Claude skill for making TikTok ads (video, image, animated, and Spark Ads) that pass TikTok's ad review in any market. For campaigns in the EU and EEA, it also checks the ads against EU and national advertising law. For other markets, it checks TikTok's rules only and says so.

TikTok approving an ad doesn't make it lawful. Ad review checks TikTok's own policies. It doesn't check the EU's Unfair Commercial Practices Directive, the 30-day price-reduction rule, AI Act disclosure duties, or national rules like Germany's pharmaceutical advertising law. This skill checks both layers before anything is produced.

## Install

You need Claude Code or a Claude app with code execution turned on. The checker scripts need Python 3.8 or later (standard library only). The video check also needs `ffmpeg` and `ffprobe`; without them, everything else still works.

### Claude Code

Clone the repository and link the skill into your skills folder. With a link, `git pull` is all it takes to update later.

```bash
git clone https://github.com/marcelfelixbaur/tiktok-ad-compliance.git ~/tiktok-ad-compliance
```

```bash
mkdir -p ~/.claude/skills && ln -s ~/tiktok-ad-compliance/tiktok-ad-compliance ~/.claude/skills/tiktok-ad-compliance
```

This makes the skill available in every project. To use it in one project only, link it into that project's `.claude/skills/` folder instead.

If you'd rather not keep a clone, or you're on Windows without symlinks, copy the folder instead. A copy is a snapshot, so you'll repeat the copy for every update.

```bash
cp -r ~/tiktok-ad-compliance/tiktok-ad-compliance ~/.claude/skills/
```

### Claude apps (claude.ai and desktop)

1. In **Settings → Capabilities**, turn on **Code execution and file creation**. Skills don't run without it.
2. Zip the inner `tiktok-ad-compliance` folder, the one that contains `SKILL.md`. From your clone:

   ```bash
   cd ~/tiktok-ad-compliance && zip -r ~/tiktok-ad-compliance.zip tiktok-ad-compliance
   ```

   Don't use GitHub's "Download ZIP" button for this. It nests the skill one folder too deep.
3. In **Settings → Capabilities**, under Skills, click **Upload skill** and choose the zip.

Skills you upload are only available to you.

### Check that it works

Ask something without naming a market, for example "Make me a TikTok ad for my protein powder". The skill should ask which countries the ad will run in and confirm the product category before writing anything:

> **You:** Make me a TikTok ad for my protein powder.
>
> **Claude:** Before I write anything: which countries will this run in? And should I treat the protein powder as a food supplement or as a sports food? The rules differ. Also, is this a regular In-Feed ad or a Spark Ad boosting one of your posts?

## Updating

An installed skill doesn't update when this repository changes. Your copy stays on the version you installed until you update it:

| How you installed | How to update |
|---|---|
| Claude Code, linked | `git -C ~/tiktok-ad-compliance pull`. Claude Code picks up the change, at the latest in your next session |
| Claude Code, copied | `git -C ~/tiktok-ad-compliance pull`, then run the `cp -r` command from the install steps again |
| Claude apps | Make a new zip as in the install steps, remove the old skill in **Settings → Capabilities**, then upload the new zip |

To switch from a copied install to a linked one, delete the copy first (`rm -rf ~/.claude/skills/tiktok-ad-compliance`), then run the `ln -s` command.

## What it does

The skill runs three checks, cheapest first, so problems are caught before they get into a finished video:

1. **Eligibility.** It asks for the target countries, product category, ad format and the advertiser's licences before any script is written. It never assumes a market or category, and it doesn't guess them from the user's language or currency. Some product categories can't be advertised at all. Others need licences, age targeting or disclaimers.
2. **Creative.** It writes the script, on-screen text, visuals, music and specs to the rules for that product category and market. Common problem claims are rewritten to say what the product does rather than what the viewer will become.
3. **Preflight.** Two bundled scripts check the finished copy and media automatically.

It ends with a short compliance report: the verdict, the countries and category you confirmed, the conditions the advertiser has to meet outside the ad, and open questions.

It activates on requests like:

> Make a 15-second TikTok ad for our collagen supplement, targeting Germany and France.

> Is "eco-friendly packaging, 30% off" OK for a TikTok ad in the Netherlands?

> Our TikTok ad got rejected. Here's the script. Why?

## Coverage

| Layer | Scope |
|---|---|
| TikTok platform policy | Global, including the market-by-market category changes in TikTok's 2026 policy change log (reviewed October 2026) |
| Legal layer | **EU and EEA only**: UCPD, green claims (Directive (EU) 2024/825), price-reduction rule (Art. 6a PID), AI Act Art. 50, DSA, GDPR/ePrivacy, EU health and cosmetics claim rules, TTPA, influencer disclosure, and notes for FR, DE, IT, SE, NO, GR, ES, LT, NL and BE |
| Copy checker languages | English, German, French. Copy in other languages is reported as unchecked, not passed |
| Product categories | health, pharmacy, supplements, weight, cosmetic procedures, beauty, food, alcohol, finance, crypto, gambling, prediction markets, gaming, dating, and "other" |

**Not covered:** the laws of the US, UK, and every market outside the EU and EEA. The skill and the checker say so when a campaign targets those markets instead of implying the platform check is enough. The UK is deliberately excluded because its rules (UK GDPR, the CAP/BCAP Codes, DMCCA 2024) are similar in spirit to the EU's but differ in detail.

## Using the scripts on their own

Both scripts run without Claude and exit non-zero when something blocks, so they can be used in CI.

```bash
# Copy check. --market and --vertical are required; there are no defaults.
# An EU/EEA country code turns on the EU legal checks.
python3 tiktok-ad-compliance/scripts/lint_copy.py --file script.txt --market US --vertical supplements
python3 tiktok-ad-compliance/scripts/lint_copy.py --file script.txt --market DE,AT --vertical beauty --creator --aigc

# Media check: resolution, aspect ratio, duration, bitrate, audible audio, static-frame share, safe zones
python3 tiktok-ad-compliance/scripts/preflight_media.py ad.mp4 --overlay safezone.png
```

`--market` takes ISO country codes (or `EU`/`EEA`) and rejects anything vaguer, such as "Europe". `--vertical` takes one or more categories (`supplements,beauty`). Together they also trigger checks that don't depend on wording: outright bans (pharmacy ads in France, alcohol in Norway and Lithuania, gambling in Italy and Brazil, prediction markets outside TikTok's 17 allowed markets) and the preconditions the advertiser owns.

The same copy can pass for `US` and fail for `DE`, in English or German:

```
"Our eco-friendly serum is carbon neutral and boosts your immune
 system. 30% off, was €49. Sustainable and paraben-free."

--market US --vertical beauty  →  0 block · 0 review   (+ "no legal rule pack for US")
--market DE --vertical beauty  →  3 block · 4 review   (green claims, EU health-claim wording, price rule)

"Unser umweltfreundliches Serum ist klimaneutral und stärkt dein
 Immunsystem. 30% Rabatt, statt 49 €. Nachhaltig und parabenfrei."

--market DE --vertical beauty  →  3 block · 4 review
```

The checker matches known risky phrasings. It doesn't decide whether a claim is acceptable. Every flag needs a decision from a person, and a clean result doesn't mean the copy is compliant.

## What's in the repository

```
tiktok-ad-compliance/                 the skill (this folder is what gets installed)
├── SKILL.md                          workflow: eligibility → creative → preflight
├── references/
│   ├── restricted-verticals.md       prohibited and restricted categories, 2026 market changes
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
tests/                                tests for both scripts (not part of the installed skill)
```

## Accuracy and limits

- **Not legal advice.** The legal layer is a best-effort review based on published regulation and guidance, current as of October 2026. EU directives are written into law differently in each member state. Regulated products and large campaigns need the advertiser's own lawyers.
- **Policies change.** TikTok revises its policies, and the exceptions by market change. Each reference file ends with source links. Check the live pages before a close call.
- **Safe-zone figures are estimates.** They are conservative figures used by practitioners, not numbers TikTok publishes. The downloadable safe-zone templates in TikTok Ads Manager are the authoritative source.
- **Passing every check makes approval likely, not certain.** TikTok's ad review makes its own judgment.

## Contributing

Contributions are welcome, especially:

- legal layers for other markets (US FTC, UK ASA/CAP, Australia, Brazil) as new `references/<market>-law.md` files with matching checker rule packs
- checker rule packs for more languages (Italian, Spanish, Dutch, Polish, ...), added as extra language keys on the existing rules
- policy updates, each with a link to the TikTok or EUR-Lex source
- false positives and false negatives from the checker, with the copy that triggered them, ideally as a test case

Run the tests with `python3 -m unittest discover tests`. They use the standard library only; the media tests are skipped when `ffmpeg` isn't installed.

## Disclaimer

This project is not affiliated with, endorsed by, or sponsored by TikTok or ByteDance. "TikTok" is a trademark of its owner and is used here only to describe what the skill is for.

## License

MIT
