# Online Ad Compliance

**Catch ad rejections before the platform does.**

Checks your ad against each platform's policies and the advertising law of your target markets before you produce it.

Online Ad Compliance is a plugin for Claude. Before writing any script or copy, it asks where the ad will run, in which countries, and what is being sold. It then checks eligibility, claims, creative and specs against that platform's ad policies and, for EU and EEA markets, against EU and national advertising law. A platform approving an ad doesn't make it lawful, so it checks both.

## Platforms

| Platform | Ad policy checks | Legal checks (EU/EEA markets) |
|---|---|---|
| TikTok | supported | yes |
| Meta (Facebook, Instagram) | planned | yes |
| Google Ads | planned | yes |
| YouTube | planned | yes |
| Any other platform | not covered | yes |

For a platform that isn't covered yet, Claude says so and runs only the legal checks and a general claim review. It never implies that platform's own rules were checked.

## Install

You need Claude Code, or a Claude app with code execution turned on. The checker scripts need Python 3.8 or later (standard library only). The video check also needs `ffmpeg` and `ffprobe`; without them, everything else still works.

### Claude Code

In Claude Code 2.1.275 or later, run this inside Claude Code:

```
/plugin install online-ad-compliance --marketplace marcelfelixbaur/online-ad-compliance
```

Or from your terminal, in two steps:

```bash
claude plugin marketplace add marcelfelixbaur/online-ad-compliance
```

```bash
claude plugin install online-ad-compliance@marcelfelixbaur
```

Then turn on automatic updates: run `/plugin`, open **Marketplaces**, choose `marcelfelixbaur`, and select **Enable auto-update**.

The skill is available as `/online-ad-compliance:ad-compliance`. Claude also uses it on its own whenever you work on an ad.

### Claude apps (claude.ai, desktop, Cowork)

A listing in Anthropic's plugin directory is coming. Installs from the directory will update automatically. Until then, upload the skill by hand:

1. In **Settings → Capabilities**, turn on **Code execution and file creation**. Skills don't run without it.
2. Zip the `skills/ad-compliance` folder:

   ```bash
   git clone https://github.com/marcelfelixbaur/online-ad-compliance.git && cd online-ad-compliance/skills && zip -r ~/ad-compliance.zip ad-compliance
   ```

3. In **Settings → Capabilities**, under Skills, click **Upload skill** and choose the zip.

An uploaded zip doesn't update itself.

### Upgrading from the standalone TikTok skill

If you installed the earlier `tiktok-ad-compliance` skill by linking or copying it into `~/.claude/skills/`, remove it before installing the plugin, so the old version doesn't keep loading:

```bash
rm -rf ~/.claude/skills/tiktok-ad-compliance
```

## Updating

| How you installed | How to update |
|---|---|
| Claude Code, auto-update on | Nothing to do. New versions download in the background and load the next time you start Claude Code, or after `/reload-plugins` |
| Claude Code, auto-update off | `claude plugin update online-ad-compliance@marcelfelixbaur` |
| Claude apps, uploaded zip | Make a new zip as above, remove the old skill in **Settings → Capabilities**, then upload the new zip |

## Check that it works

Ask for an ad without naming a platform or a market. Claude should ask for both, and confirm the product category, before writing anything:

> **You:** Make me an ad for my protein powder.
>
> **Claude:** Before I write anything: which platform will this run on, for example TikTok, Instagram or YouTube? Which countries? And should I treat the protein powder as a food supplement or as a sports food? The rules differ. Also, which ad format are you planning?

## What it does

It runs three checks, cheapest first, so problems are caught before they get into a finished video:

1. **Eligibility.** It asks for the ad platform, target countries, product category, ad format and the advertiser's licences before any script is written. It never assumes any of them, and it doesn't guess the market from the user's language or currency. Some product categories can't be advertised at all. Others need licences, age targeting or disclaimers.
2. **Creative.** It writes the script, on-screen text, visuals, music and specs to the rules for that platform, product category and market. Common problem claims are rewritten to say what the product does rather than what the viewer will become.
3. **Preflight.** Two bundled scripts check the finished copy and media automatically.

It ends with a short compliance report: the verdict, the platform, countries and category you confirmed, the conditions the advertiser has to meet outside the ad, and open questions.

It activates on requests like:

> Make a 15-second TikTok ad for our collagen supplement, targeting Germany and France.

> Is "eco-friendly packaging, 30% off" OK for a TikTok ad in the Netherlands?

> Our TikTok ad got rejected. Here's the script. Why?

> Can we say "carbon neutral" in an Instagram ad for Germany? *(Meta's policies aren't covered yet, so this gets the EU legal check and says so.)*

## Coverage

| Layer | Platform | Scope |
|---|---|---|
| Platform policy | TikTok | Global, including the market-by-market category changes in TikTok's 2026 policy change log (reviewed October 2026) |
| Platform policy | all others | Not covered yet, and the skill and the checker say so |
| Legal layer | any | **EU and EEA only**: UCPD, green claims (Directive (EU) 2024/825), price-reduction rule (Art. 6a PID), AI Act Art. 50, DSA, GDPR/ePrivacy, EU health and cosmetics claim rules, TTPA, influencer disclosure, and notes for FR, DE, IT, SE, NO, GR, ES, LT, NL and BE |
| Copy checker languages | any | English, German, French. Copy in other languages is reported as unchecked, not passed |
| Product categories | any | health, pharmacy, supplements, weight, cosmetic procedures, beauty, food, alcohol, finance, crypto, gambling, prediction markets, gaming, dating, and "other" |

**Not covered:** the laws of the US, UK, and every market outside the EU and EEA. The skill and the checker say so when a campaign targets those markets instead of implying the platform check is enough. The UK is deliberately excluded because its rules (UK GDPR, the CAP/BCAP Codes, DMCCA 2024) are similar in spirit to the EU's but differ in detail.

## What it runs

- **One skill** (`skills/ad-compliance`): instructions and reference files that Claude reads. No hooks, MCP servers, agents or background processes.
- **Two local Python scripts** in `skills/ad-compliance/scripts/`, using the standard library only. `lint_copy.py` reads the copy you pass it. `preflight_media.py` runs `ffmpeg` and `ffprobe` from your machine on the file you pass it, and writes a safe-zone overlay image only where you ask it to.
- **No network requests, and no data stored or sent.** The scripts print a report and exit.
- During a review, Claude may consult public policy pages, such as a platform's ad policies or EUR-Lex, with its own web tools. That is Claude's normal browsing, not something the plugin does.

## Using the scripts on their own

Both scripts run without Claude and exit non-zero when something blocks, so they can be used in CI.

```bash
# Copy check. --platform, --market and --vertical are required; there are no defaults.
# An EU/EEA country code turns on the EU legal checks.
python3 skills/ad-compliance/scripts/lint_copy.py --file script.txt --platform tiktok --market US --vertical supplements
python3 skills/ad-compliance/scripts/lint_copy.py --file script.txt --platform tiktok --market DE,AT --vertical beauty --creator --aigc

# A platform that isn't covered yet: legal checks only, and the output says platform policy wasn't checked.
python3 skills/ad-compliance/scripts/lint_copy.py --file script.txt --platform other --market DE --vertical food

# Media check: resolution, aspect ratio, duration, bitrate, audible audio, static-frame share, safe zones
python3 skills/ad-compliance/scripts/preflight_media.py ad.mp4 --platform tiktok --overlay safezone.png
```

`--platform` takes `tiktok`, or `other` for any platform not covered yet; comma-separate for multi-platform campaigns. `--market` takes ISO country codes (or `EU`/`EEA`) and rejects anything vaguer, such as "Europe". `--vertical` takes one or more categories (`supplements,beauty`). Together they also trigger checks that don't depend on wording: outright bans in law (alcohol in Norway and Lithuania, gambling in Italy), outright bans in TikTok's policy (pharmacy ads in France, gambling in Brazil, prediction markets outside TikTok's 17 allowed markets), and the preconditions the advertiser owns.

The same copy can pass for `US` and fail for `DE`, in English or German:

```
"Our eco-friendly serum is carbon neutral and boosts your immune
 system. 30% off, was €49. Sustainable and paraben-free."

--platform tiktok --market US --vertical beauty  →  0 block · 0 review   (+ "no legal rule pack for US")
--platform tiktok --market DE --vertical beauty  →  3 block · 4 review   (green claims, EU health-claim wording, price rule)

"Unser umweltfreundliches Serum ist klimaneutral und stärkt dein
 Immunsystem. 30% Rabatt, statt 49 €. Nachhaltig und parabenfrei."

--platform tiktok --market DE --vertical beauty  →  3 block · 4 review
```

The checker matches known risky phrasings. It doesn't decide whether a claim is acceptable. Every flag needs a decision from a person, and a clean result doesn't mean the copy is compliant.

## Repository layout

```
.claude-plugin/
├── plugin.json                       plugin manifest (name, version, description)
├── marketplace.json                  lets Claude Code install the plugin from this repository
└── icon.png
skills/ad-compliance/                 the skill
├── SKILL.md                          workflow: Step 0 questions → eligibility → creative → preflight → report
├── references/
│   ├── law/
│   │   └── eu-eea.md                 EU/EEA legal layer, any platform
│   └── platforms/
│       └── tiktok/
│           ├── restricted-verticals.md   prohibited and restricted categories, 2026 market changes
│           ├── claims-and-copy.md        misleading claims, clickbait, AI-content labels, rewrite patterns
│           ├── creative-and-format.md    quality and motion rules, on-screen content, landing pages
│           ├── music-and-ip.md           Commercial Music Library, licensing, likeness, trademarks
│           └── specs-and-safe-zones.md   specs, character limits, safe zones
├── scripts/
│   ├── lint_copy.py                  flags ad copy likely to be rejected or unlawful
│   └── preflight_media.py            checks technical specs and draws the safe-zone overlay
└── assets/
    └── compliance-report.md          handover template
tests/                                tests for both scripts
.claude/settings.json                 settings for working on this repository in Claude Code
```

## Accuracy and limits

- **Not legal advice.** The legal layer is a best-effort review based on published regulation and guidance, current as of October 2026. EU directives are written into law differently in each member state. Regulated products and large campaigns need the advertiser's own lawyers.
- **Policies change.** Platforms revise their policies, and the exceptions by market change. Each reference file ends with source links. Check the live pages before a close call.
- **Safe-zone figures are estimates.** They are conservative figures used by practitioners, not numbers TikTok publishes. The downloadable safe-zone templates in TikTok Ads Manager are the authoritative source.
- **Passing every check makes approval likely, not certain.** Each platform's ad review makes its own judgment.

## Contributing

Contributions are welcome, especially:

- **adding a platform** (Meta, Google Ads, YouTube, ...): the checklist is in [`MAINTENANCE.md`](MAINTENANCE.md)
- legal layers for other markets (US FTC, UK ASA/CAP, Australia, Brazil) as new `references/law/<market>.md` files with matching checker rule packs
- checker rule packs for more languages (Italian, Spanish, Dutch, Polish, ...), added as extra language keys on the existing rules
- policy updates, each with a link to the platform's or EUR-Lex source
- false positives and false negatives from the checker, with the copy that triggered them, ideally as a test case

Run the tests with `python3 -m unittest discover tests`. They use the standard library only; the media tests are skipped when `ffmpeg` isn't installed.

## Disclaimer

This project is not affiliated with, endorsed by, or sponsored by TikTok, ByteDance, Meta, Google or any other platform. Their names are trademarks of their owners and are used here only to describe what the plugin checks.

## License

MIT. See [LICENSE](LICENSE).
