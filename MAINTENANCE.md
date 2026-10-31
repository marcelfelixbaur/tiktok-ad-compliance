# Maintenance

How the plugin's policy and legal content is kept current, released and extended. The weekly review follows this file, so keep it up to date with every change.

## Sources to watch

### Platform policies

**TikTok**

- Policy index: <https://ads.tiktok.com/resources/help/article/tiktok-advertising-policies>
- 2026 change log: <https://ads.tiktok.com/resources/help/article/tiktok-ad-policy-change-log-2026>
- From January 2027, find the new year's change log from the policy index. The URL is likely `https://ads.tiktok.com/resources/help/article/tiktok-ad-policy-change-log-2027`.
- The individual policy pages are listed under Sources in each file in `skills/ad-compliance/references/platforms/tiktok/`.

### Law (EU/EEA)

| Area | Source |
|---|---|
| EU legislation | EUR-Lex: <https://eur-lex.europa.eu/>. Directive (EU) 2024/825: <https://eur-lex.europa.eu/eli/dir/2024/825/oj>. DSA: <https://eur-lex.europa.eu/eli/reg/2022/2065/oj>. Reg. (EU) 655/2013: <https://eur-lex.europa.eu/eli/reg/2013/655/oj> |
| AI Act transparency (Art. 50) | <https://digital-strategy.ec.europa.eu/en/policies/guidelines-ai-transparency-obligations> |
| Digital Fairness Act | Commission initiative page: <https://ec.europa.eu/info/law/better-regulation/have-your-say/initiatives/13413-Digital-fairness-fitness-check-on-EU-consumer-law_en> |
| Influencer disclosure | Commission Influencer Legal Hub: <https://commission.europa.eu/topics/consumers/consumer-rights-and-complaints/influencer-legal-hub_en> |
| Price-reduction rule | <https://commission.europa.eu/law/law-topic/consumer-protection-law_en> |
| Health claims | EU Register: <https://food.ec.europa.eu/food-safety/labelling-and-nutrition/nutrition-and-health-claims/eu-register-health-claims_en> |
| Political advertising (TTPA) | <https://commission.europa.eu/strategy-and-policy/policies/justice-and-fundamental-rights/democracy-eu-citizenship-anti-corruption/democracy-and-electoral-rights/transparency-and-targeting-political-advertising_en> |
| France: influence law (Loi 2023-451) | Légifrance: <https://www.legifrance.gouv.fr/loda/id/JORFTEXT000047663185> |
| Italy: AGCOM influencer code (Delibera 197/25/CONS) | <https://www.agcom.it/provvedimenti/delibera-197-25-cons> |
| Italy: gambling advertising ban | ADM: <https://www.adm.gov.it/portale/giochi>. AGCOM guidelines, Delibera 132/19/CONS: <https://www.agcom.it/provvedimenti/delibera-132-19-cons>. Supplement, Delibera 200/26/CONS: <https://www.agcom.it/sites/default/files/provvedimenti/delibera/2026/200_26_CONS.pdf> |
| Spain: gambling advertising (RD 958/2020) | BOE consolidated text: <https://www.boe.es/buscar/act.php?id=BOE-A-2020-13495> |
| Netherlands: gambling advertising | Kansspelautoriteit (KSA): <https://kansspelautoriteit.nl/> |
| Belgium: gambling advertising | Gaming Commission: <https://www.gamingcommission.be/> |

## TikTok 2026 change-log entries already incorporated

Each line is the title of an entry in the [2026 change log](https://ads.tiktok.com/resources/help/article/tiktok-ad-policy-change-log-2026). All entries marked "incorporated" are reflected in `references/platforms/tiktok/restricted-verticals.md`. The weekly review compares the live change log against this list. Last compared: 2026-10-31 (29 entries, no new ones).

| Month | Entry | Markets | Status |
|---|---|---|---|
| Mar | Update to Cosmetic Surgery Policy | US, CA | incorporated |
| May | Update to Contraceptives Policy | LK | incorporated |
| May | Update to Weight Management and Body Image Policy | global + APAC/MEA lists | incorporated |
| Jun | Update to Rewarded Gaming | AR, GT | incorporated |
| Jun | Update to Social Casinos | GT | incorporated |
| Jun | Update to Offensive Content | global (split in two) | incorporated |
| Jun | Update to Adult Content policy (live-chat apps) | PK, BD | incorporated |
| Jun | Update to Baby Food Products Policy | AZ | incorporated |
| Jun | Update to Alcohol Policy | CY, LU | incorporated |
| Jun | Update to Financial Services Policy (digital-currency advisory) | GB, IE | incorporated |
| Jun | Update to Political Advertising | global | incorporated |
| Jun | Clarifications to Adult Content Policy | — | **not retrieved** |
| Jul | Update to Alcohol: Market-specific requirements (venues) | KH, PH, SG, LK, VN | incorporated |
| Jul | Update to Prediction Markets and Event Contracts Policy | 17 markets | incorporated |
| Jul | Update to Weight loss and Muscle Gain Policy | EMEA, NA, LATAM | incorporated |
| Jul | Update to Crypto Mining Devices Policy | US, CA | incorporated |
| Jul | Update to Financial Services Policy (FX) | FR | incorporated |
| Jul | Update to Investment Consultation or Advice Policy | BO, PY | incorporated |
| Jul | Update to 0% Alcohol Policy | — | **not retrieved** |
| Jul | Update to Horoscope and Fortune-telling Policy | BD, LB, MA | incorporated |
| Jul | Update to Adult Content Policy (dating apps) | DZ, BD, EG, PK, TR, AE | incorporated |
| Jul | Update to Online Casino Policy | 19 markets | incorporated |
| Jul | Update to Online Gambling, Fantasy Sports and Rewarded Gaming Policies | KE, NG | incorporated |
| Aug | Update to Alcohol Policy (>5% ABV) | AZ | incorporated |
| Aug | Update to Lotteries Policy (passive lotteries) | BR | incorporated |
| Aug | NGO MDA Requirement Update | — | **not retrieved** |
| Aug | Update to Precious Metals Trading Policy | FR, IT, DE, GB | incorporated |
| Aug | Update to CFD (Contracts for Difference) Policy | US, CA | incorporated |
| Oct | Update to Online Gambling Policy (ban) | BR | incorporated |

## Watchlist

Known upcoming changes. Remove an item once it's handled, and add new ones as they come up.

| When | What | Affects |
|---|---|---|
| 2 Dec 2026 | The AI Act Art. 50(2) grace period for providers' machine-readable marking on systems already on the market ends. | `references/law/eu-eea.md` (AI-generated content section) |
| Nov 2026 (expected) | The Commission's Digital Fairness Act proposal. Reports disagree on whether it has already been presented. | `references/law/eu-eea.md` ("On the horizon" paragraph) |
| Ongoing | Italy may relax its gambling advertising ban (pressure from football bodies). AGCOM adopted Delibera 200/26/CONS on 29 July 2026, supplementing its 2019 guidelines on responsible-gambling campaigns, and a further consultation on the 2019 guidelines was reported in October 2026. The reference files cite "AGCOM's March 2026 guidelines"; check that date and description against 200/26/CONS. | `references/law/eu-eea.md` (member-state table), `references/platforms/tiktok/restricted-verticals.md`, the Italy gambling gate and `MARKET_NOTES["IT"]` in `lint_copy.py` |
| Ongoing | Spain's Supreme Court annulled several articles of RD 958/2020 in April 2024. Check that the Spain row still describes the rules correctly. | `references/law/eu-eea.md` (member-state table), the Spain precondition in `lint_copy.py` |
| Retry | Three TikTok update pages failed to load on 2026-10-31: 0% Alcohol (July 2026), Clarifications to Adult Content (June 2026), NGO MDA requirement (August 2026). | `references/platforms/tiktok/restricted-verticals.md` |
| Jan 2027 | TikTok's 2027 change log. | `references/platforms/tiktok/restricted-verticals.md`, the list above |

## Weekly review procedure

The scheduled weekly task runs this. It can also be run by hand.

1. Read this file: the incorporated change-log entries, the watchlist, and the sources.
2. **Platform policies.** For each supported platform:
   1. Open its current change log. In January, look for the new year's log from the policy index.
   2. List every entry that isn't in the incorporated list, and read each one.
   3. Retry any page in the watchlist that previously failed to load.
3. **Law.** For each watchlist item whose date has passed, or that is marked ongoing, check the primary source for news. Also run one web search per area for changes in the last 14 days: EU advertising and consumer law, AI Act transparency, and the national rules named in `references/law/eu-eea.md`.
4. **Links.** Check that every URL in the reference files' Sources sections still loads. Treat a 403 from a site that blocks bots as "can't check", not as broken.
5. **If nothing changed:**
   - If the newest "Last reviewed" date is older than 28 days, open a small pull request that only updates the dates and raises the patch version. This keeps users' copies from looking stale.
   - Otherwise stop and report "no changes".
6. **If something changed:**
   - Update the affected reference files (including the 2026/2027 change table), and the checker's rules, gates and preconditions where a change affects them. Add a test for each new gate or rule.
   - Update this file (incorporated list, watchlist) and `CHANGELOG.md`, raise the patch version, and update the "Last reviewed" dates.
   - Run the tests and `claude plugin validate --profile directory --strict .`.
7. **Pull request** titled `Policy update YYYY-MM-DD: <short summary>`. The body has a table of each change (what, which file, source link) and anything it couldn't verify. Remove the footer the integration adds. Don't merge it: Marcel reviews and merges.
8. **Rules for every run:**
   - Never weaken a check without a primary source.
   - Never remove the "not legal advice" or "approval likely, not certain" wording.
   - Never touch files unrelated to the update.
   - Never assume facts that need the advertiser.

## Release procedure

Every change that reaches `main` and touches `skills/` or `.claude-plugin/plugin.json` is a release:

1. Raise `version` in `.claude-plugin/plugin.json`. Users only get an update when this string changes, and the checks fail a pull request that forgets.
   - **Patch** (1.0.x): policy or legal content updates.
   - **Minor** (1.x.0): new rules, categories or platforms.
   - **Major** (x.0.0): breaking changes to the scripts' flags.
2. Add a `CHANGELOG.md` entry.
3. Update the "Last reviewed" line of every reference file you reviewed.
4. Run the tests and validation:

   ```bash
   python3 -m unittest discover tests
   ```

   ```bash
   claude plugin validate --profile directory --strict .
   ```

Never rename the plugin: existing installs break.

## Adding a platform

The checklist for when Meta, Google Ads, YouTube or another platform is added:

1. Research the platform's ad policies, restricted categories, editorial and character rules, specs and safe zones, and its change log.
2. Add `skills/ad-compliance/references/platforms/<platform>/`, mirroring TikTok's files, each with a "Last reviewed" line. Add the platform to the routing table in `SKILL.md` and to its description (still under 1024 characters).
3. Add it to `PLATFORMS` in `lint_copy.py` and to `SPECS` in `preflight_media.py`. Review every claim rule currently marked `["tiktok"]` and extend the ones that apply. Add the platform's own rules (for example Meta's personal-attributes rule and Google's editorial rules), its field limits, specs and gates.
4. Add tests for the platform's rules and for leaving TikTok's results unchanged.
5. Add the platform's sources and change log to this file, and the platform to the README's platform table. Raise the minor version and add a changelog entry.
