---
name: ad-compliance
description: Check paid ads against the ad platform's policies and the advertising law of the target markets before they are produced — video, image, carousel, animated, creator and boosted posts. Platform policy is covered for TikTok today. For other platforms (Meta, Google Ads, YouTube, ...) it says their policies aren't covered and runs the legal and general claim checks only. Legal checks cover EU/EEA markets (UCPD, green claims, price-reduction rules, AI Act disclosure, health and cosmetics claims, influencer disclosure, national codes). Use this whenever the user is making, scripting, storyboarding, editing or reviewing an ad, promo or paid creative for any platform; whenever they ask whether a product, claim, visual or piece of ad copy is allowed on an ad platform or lawful in a market; or whenever an ad was rejected and they want to know why. Use it before producing any paid ad even if the user never mentions policy, because a problem found after the render is a reshoot.
license: MIT
compatibility: Works in any agent that can read files and run shell commands. The bundled checkers need Python 3.8+; the media check also needs ffmpeg and ffprobe. No network access needed.
---

# Ad Compliance

Ad platforms review every ad before it serves. Rejections are cheap to avoid and expensive to fix: a banned claim in a voiceover means re-recording, a prohibited product means the campaign never runs at all, and repeat violations put the whole ad account at risk. So the work is ordered to catch problems at the cheapest possible moment — eligibility before scripting, claims before rendering, specs before upload.

Run the three gates in order. Do not skip ahead to production because the brief sounds harmless; "harmless" categories like skincare, supplements, fintech apps, and fitness are exactly where most rejections live.

## Two layers, not one

Compliance here means two independent things, and clearing one does not clear the other:

1. **The ad platform's policy** — what ad review enforces. Failure means the ad doesn't run.
2. **The advertising law of the target market** — what regulators, consumer authorities and (in some member states) competitors enforce. Failure means fines, injunctions, or forced campaign withdrawal, and it can happen *after* the platform approved the ad.

Ad review does not check the Unfair Commercial Practices Directive, EU price-reduction rules, the AI Act, or German pharmaceutical advertising law. So an approved ad is not a lawful ad.

**If any EU or EEA market is in scope, read `references/law/eu-eea.md`.** It carries the legal layer and is not optional for those markets. Two obligations in it are live right now and routinely missed: AI Act Article 50 synthetic-content disclosure (applies since 2 August 2026, and not delayed by the Digital Omnibus) and the Directive (EU) 2024/825 ban on generic green claims (applies since 27 September 2026). For non-EU markets the equivalent legal layer is not bundled here. Say so plainly rather than implying the platform gate is the whole job.

## What's covered, and what to load

| Fact from Step 0 | Load |
|---|---|
| Platform is **TikTok** | the files in `references/platforms/tiktok/` (see the Gate 2 table for which one when) |
| Any **EU or EEA** market | `references/law/eu-eea.md` |
| Any other platform | no platform file exists yet — see below |
| A market outside the EU/EEA | no legal file exists — say so in the report |

**Platforms not covered yet** (Meta, Google Ads, YouTube, Snapchat, Pinterest, LinkedIn, X, Amazon, ...):

- Say plainly, before any other work, that this skill doesn't cover that platform's ad policies yet.
- Offer what it can do: the legal check for EU/EEA markets, and a general claim review — misleading, exaggerated, health, financial and environmental claims. Run the linter with `--platform other` for the legal checks.
- If you use the TikTok reference files as a guide for the general claim review, say that's what they are. Many platforms have similar rules, but the wording and the market exceptions differ.
- **Never imply the platform's own rules were checked.** In the report, mark platform policy as "not checked" and point to the platform's own policy pages.

**Several platforms in one campaign:** check each covered platform against its own files. Where creative is shared, the strictest rule wins. Any uncovered platform in the mix gets the treatment above.

## Step 0 — Ask for five facts before anything else

Ad policies are platform-specific, market-specific and vertical-specific to a degree that makes general answers useless. You cannot assess a single frame without knowing:

1. **Ad platform(s)**: where the ad will run — TikTok, Meta (Facebook, Instagram), Google Ads, YouTube, or others. This selects the platform rules: the same creative can pass one platform's review and fail another's.
2. **Target market(s)**: the countries the ad will run in. This selects the legal layer as well as the policy carve-outs. A supplement ad that's fine in the US is unlawful in the EU the moment it says "boosts immunity"; alcohol, crypto, gambling and pharmacy rules differ country by country, and France, Germany, Italy and the Nordics each add national rules on top of EU law.
3. **What's being sold**: the product category, which determines which gate in the platform's restricted-verticals file applies (for TikTok, `references/platforms/tiktok/restricted-verticals.md`).
4. **Ad format**: formats, specs and safe zones differ by platform. On TikTok: In-Feed auction, Spark Ad (boosting an organic post), TopView, carousel/image, or Pangle.
5. **Advertiser status**: do they hold the licences, certifications, or regulatory approvals their category requires? Restricted verticals are not "be careful" categories; they are "produce nothing until the paperwork exists" categories.

**Never assume the platform, the market or the product category. Ask.** This holds when the user wants a quick draft, sounds impatient, or the answer looks obvious, because a wrong guess here invalidates every check that follows and nothing downstream flags it.

- **"A social ad", "paid social" or "everywhere" isn't a platform.** Ask which platforms. Don't infer the platform from the format either: a 9:16 vertical video can run on TikTok, Instagram Reels, YouTube Shorts or Snapchat, and each reviews it differently.
- **Don't infer the market** from the language the user writes in, the currency in the brief, the brand's home country, or where the user seems to be. A German-speaking user may be targeting Austria, Switzerland or the US. "€" covers 20 countries with different national rules.
- **"Europe", "the EU", "global" or "everywhere" isn't an answer.** Ask which countries. National rules differ too much to treat the EU as one market, and "global" includes markets where the product may be banned.
- **Don't infer the category from the product name alone.** Say which category you would place it in and ask the user to confirm. "Collagen powder" can be a food supplement or a cosmetic, a "detox tea" can be food or a weight-loss product, and the rules differ. If it spans categories, confirm each one.
- **Ask for format and licence status too.** If the user doesn't know whether a licence exists, record that as an open question for the report. Don't wait on it before asking the rest.

Ask everything that's missing in one message, so the user answers once. Until the platform(s), market(s) and category are confirmed, don't write script, copy or shot lists, and don't give a verdict on whether something is allowed. `scripts/lint_copy.py` refuses to run without `--platform`, `--market` and `--vertical` for the same reason.

## Gate 1 — Eligibility (before you write a word of script)

Read the platform's restricted-verticals file (TikTok: `references/platforms/tiktok/restricted-verticals.md`) and place the product in one of three buckets:

- **Prohibited** — the ad cannot run in that market, full stop. Say this immediately and plainly. Don't produce creative and don't try to word around it; obscuring a prohibited product is itself a policy violation (see deceptive practices). Offer the nearest legitimate angle instead — e.g. a vape brand can't advertise vapes, but a cessation-adjacent or lifestyle-brand play may be viable, and that's a real conversation to have.
- **Restricted** — allowed only with specific preconditions: a license on file, platform approval (on TikTok, sales-rep or certification approval), mandatory 18+ (sometimes 21+ or 25+) age targeting, and required disclaimers. Enumerate every precondition as a checklist the user must satisfy *outside* the creative, and bake the required disclaimers into the creative from the first draft rather than bolting them on later.
- **Unrestricted** — proceed, but the content rules in Gate 2 still apply in full.

National law can ban a category outright whatever the platform allows — alcohol advertising in Norway and Lithuania, gambling advertising in Italy. For EU/EEA markets, check the member-state table in `references/law/eu-eea.md` too. For a platform that isn't covered, that legal check is the only eligibility check you can run; say so.

Age-gating is a campaign setting, not a creative one — but it constrains creative, because an 18+ ad must not use childish visual language, cartoon treatments, or anything that reads as aimed at teens. Flag this to the user as a campaign-setup task they own; you cannot set it from the creative side.

## Gate 2 — Build compliant creative

Load the reference that matches what you're working on. They are written to be read one at a time, not all at once:

| Working on | Read |
|---|---|
| Script, voiceover, on-screen text, caption, headline | `references/platforms/tiktok/claims-and-copy.md` |
| Visuals, shot list, storyboard, editing, UI mockups, animation | `references/platforms/tiktok/creative-and-format.md` |
| Soundtrack, licensed footage, logos, celebrity or creator likeness | `references/platforms/tiktok/music-and-ip.md` |
| Export settings, dimensions, text placement, character limits | `references/platforms/tiktok/specs-and-safe-zones.md` |
| Industry gates, age limits, required disclaimers | `references/platforms/tiktok/restricted-verticals.md` |
| **Any EU/EEA market** — green claims, discounts, AI disclosure, health claims, targeting, national rules | **`references/law/eu-eea.md`** |

The four rules that cause the most avoidable TikTok rejections, worth holding in mind while you draft anything. Most platforms have rules in the same spirit, but check the platform's own wording:

1. **No promised or exaggerated outcomes.** "Get slim legs right away," "guaranteed returns," "cures X," "#1 in the world" — TikTok treats promised results and absolute superiority as misleading regardless of whether they're true. Rewrite toward what the product *does*, not what the user will *become*.
2. **Every interactive-looking element must actually work.** Fake play buttons, fake close/X buttons, fake progress bars, simulated system notifications, non-functional carousel dots, and imagery deliberately obscured to force a tap are all explicitly prohibited clickbait. This bites hardest on animated and game ads, where a mocked-up UI is a natural design instinct.
3. **The ad and the landing page must tell the same story.** Same product, same price, same discount, same terms. Mismatch is a rejection even when both pages are individually fine.
4. **Disclose synthetic media.** Significantly edited or AI-generated content is allowed, but on TikTok it needs the AIGC label or a clear visible disclaimer, caption, watermark, or sticker. Undisclosed AIGC risks rejection or restriction — and this applies to AI voiceovers and AI-generated b-roll, not just deepfake faces. In the EU, the AI Act adds its own disclosure duty on every platform.

### Producing the actual asset

Once the script and shot list clear Gate 2, produce the asset with whatever tooling is available. If a video or motion-production skill is installed (HyperFrames, Remotion, or similar), hand production to it. Either way, carry the platform's constraints into the production brief rather than discovering them at render time. For TikTok:

- 9:16, 1080×1920, with all text and logos inside the safe zone from `references/platforms/tiktok/specs-and-safe-zones.md`
- an audio track present throughout — TikTok requires audio and rejects muffled or absent sound
- continuous motion; static frames may not dominate (hold them to under half the runtime)
- no TikTok logos, TikTok UI chrome, or "TikTok Bestseller"-style copy anywhere in frame
- music sourced per `references/platforms/tiktok/music-and-ip.md` — this is the constraint most likely to be violated by default, since the obvious trending track is usually the one you cannot use

For still and carousel ads, the same content rules apply; only the specs change. For a platform that isn't covered, use that platform's published specs and say they weren't checked here.

## Gate 3 — Preflight before handing anything over

Two bundled scripts do the mechanical checks so you don't burn reasoning on them or eyeball things a parser does better.

**Copy and caption lint** — pattern-matches script, caption, headline, and on-screen text against the claim categories that get ads rejected, and checks character limits:

```bash
python3 scripts/lint_copy.py --text "your ad copy here" --platform tiktok --market US --vertical supplements
python3 scripts/lint_copy.py --file script.txt --platform tiktok --market DE --vertical beauty    # EU pack on
python3 scripts/lint_copy.py --file script.txt --platform tiktok --market FR,BE --vertical other --creator --aigc
python3 scripts/lint_copy.py --file script.txt --platform other --market DE --vertical food       # legal checks only
```

**Pass exactly what the user confirmed in Step 0.** `--platform`, `--market` (ISO country codes, comma-separated) and `--vertical` are all required and have no defaults. Never fill them with a guess.

- `--platform` takes `tiktok`, or `other` for any platform not covered yet. `other` runs only the legal checks and says in its output that platform policy wasn't checked. Comma-separate for multi-platform campaigns (`tiktok,other`).
- `--vertical` takes one or more of `health`, `pharmacy`, `supplements`, `weight`, `cosmetic-procedures`, `beauty`, `food`, `alcohol`, `finance`, `crypto`, `gambling`, `prediction-markets`, `gaming`, `dating`, `other`.
- An EU/EEA country code turns on the legal rule pack: green claims, the 30-day price rule, EU health-claim wording, AI Act disclosure, influencer disclosure and country notes. The same copy can lint clean for `US` and return three blocking findings for `DE`. Those findings are matters of law that ad review will not catch for you.
- The platform, market and category together trigger checks that don't depend on the wording. These are outright bans, such as alcohol in Norway and Lithuania and gambling in Italy (law, on every platform), and pharmacy ads in France, gambling in Brazil, and prediction markets outside the 17 markets TikTok allows (TikTok policy). They also include the preconditions the advertiser owns.
- For markets outside the EU/EEA, the linter checks platform policy only and says so. A clean result there is not a legal clearance.
- Rule packs exist for **English, German and French** copy. Copy in another language is reported as unchecked. Review it by hand against the reference files with a native speaker rather than treating a clean result as a pass.

It flags for human judgment; it does not adjudicate. A flag means "justify or rewrite this," and some flags are legitimately fine in context — but every flag needs a deliberate decision, not a shrug.

**Media preflight** — runs ffprobe against a rendered file and checks resolution, aspect ratio, duration, bitrate, file size, whether there is audible audio (a silent track fails like a missing one), and how much of the runtime is effectively static. It also writes a safe-zone overlay frame you can look at to confirm nothing important sits under the platform's UI. `--platform` is required; specs are bundled for TikTok only:

```bash
python3 scripts/preflight_media.py ad.mp4 --platform tiktok --format in-feed --overlay out/safezone.png
python3 scripts/preflight_media.py banner.jpg --platform tiktok --format image
```

The safe-zone overlay is worth actually opening — text placement is the one check no parser can do for you, and TikTok's caption block, CTA button, and side rail cover more of the frame than people expect.

## Check how current the references are

Every reference file has a `Last reviewed: YYYY-MM-DD` line under its title. Before giving a verdict, read that date in each file you used. If any is more than 60 days before today:

- say so at the top of the report, naming the file and its date;
- tell the user how to update, for the way they installed it:
  - Claude Code plugin: `claude plugin update online-ad-compliance@marcelfelixbaur`, or turn on auto-update under `/plugin` → **Marketplaces**;
  - Anthropic's plugin directory: updates arrive by themselves;
  - uploaded zip, or a copy in another agent's skills folder: get the latest `skills/ad-compliance` folder from <https://github.com/marcelfelixbaur/online-ad-compliance> and replace the old one;
- check the live policy pages listed under Sources in that file before making any close call.

## Reporting back

End with a short compliance summary, not a wall of policy text. `assets/compliance-report.md` is the template. Keep it to what the user has to act on:

- the verdict (clear to run / clear with conditions / cannot run as briefed)
- the platform(s), market(s), category and format the user confirmed
- for any platform that isn't covered: that its ad policies were **not checked**
- preconditions they own outside the creative — licenses, age-gate settings, landing-page fixes
- anything flagged and consciously accepted, with the reasoning

Be straight about uncertainty. Platform policies change and vary by market, and several of them turn on facts only the advertiser has (whether a license exists, whether a claim is substantiated). Where a call depends on such a fact, say so and name the fact — a confident wrong "it's fine" is worse than a flagged unknown. Point them at the live policy pages listed at the bottom of each reference file when a decision is close to the line, and note that ad review is ultimately a human-and-model judgment on the platform's side: passing every gate here makes approval likely, not certain.
