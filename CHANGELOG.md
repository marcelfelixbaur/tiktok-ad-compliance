# Changelog

Each release raises `version` in `.claude-plugin/plugin.json`. See [MAINTENANCE.md](MAINTENANCE.md) for the release procedure.

## 1.0.1 — 2026-10-31

- Every reference file shows when it was last reviewed. Claude warns at the top of the report when a file it used is more than 60 days old, says how to update, and checks the live policy pages before a close call.
- Added `MAINTENANCE.md`: sources to watch, the TikTok change-log entries already incorporated, a watchlist of upcoming changes, and the weekly review, release and add-a-platform procedures.
- Checks run on every pull request: tests, plugin validation, and a check that the version was raised.

## 1.0.0 — 2026-10-31

First release as a plugin, `online-ad-compliance`, installable from this repository's marketplace.

**Multi-platform restructure**

- The skill is now `ad-compliance` and platform-neutral. Step 0 asks for five facts and never assumes any of them: the ad platform(s), countries, product category, ad format and the advertiser's licences.
- TikTok is the first supported platform. For any other platform, Claude says its policies aren't covered and runs only the legal and general claim checks.
- References split into `references/law/` (EU/EEA) and `references/platforms/tiktok/`.
- Both scripts take a required `--platform`. `lint_copy.py --platform other` runs only the legal checks and says platform policy wasn't checked. TikTok results are unchanged.

**Content update (reviewed October 2026)**

- TikTok's 2026 market-specific category changes: cosmetic surgery in the US and Canada, weight-management supplements, prediction markets, online casino, Brazil's gambling ban, finance and crypto carve-outs, alcohol, dating and more.
- AI Act Art. 50 unchanged by the Digital Omnibus, apart from a 50(2) grace period for existing systems.
- France: influencer labels after Ordonnance 2024-978, image-retouching and AI-image labels, and the ban on influencer promotion of cosmetic procedures.
- Italy's AGCOM influencer code and gambling advertising ban, Lithuania's alcohol advertising ban, and gambling restrictions in the Netherlands and Belgium.
- The copy checker gained German and French rule packs, market-by-category bans and preconditions, and market-specific creator disclosure. The media check now fails a silent audio track.
