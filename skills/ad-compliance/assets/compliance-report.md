# Ad Compliance Report — [campaign / asset name]

Fill this in and hand it over with the creative. Keep it to what the user must act on;
they don't need the policy text quoted back at them, they need to know what to do.

---

**Verdict:** Clear to run · Clear with conditions · Cannot run as briefed
**Date:** [YYYY-MM-DD]
**Asset(s):** [filenames]
**References last reviewed:** [oldest "Last reviewed" date among the reference files used. If it's more than 60 days old, say so above the verdict and how to update.]

## Scope confirmed with the user

| | |
|---|---|
| Platform(s) | as confirmed, e.g. TikTok. Platforms whose policies aren't covered: say "policy not checked" |
| Target market(s) | country codes, e.g. DE, FR |
| Product category | as confirmed, e.g. supplements + beauty |
| Ad format | per platform, e.g. TikTok In-Feed auction / Spark / TopView / image / Pangle |
| Age targeting | 18+ / 21+ / 25+ / unrestricted |

Platform(s), market(s) and category come from the user, never from an assumption. If any is
still unconfirmed, don't issue this report: go back and ask. A wrong platform, market or
category invalidates most of what follows.

## Eligibility

- **Bucket:** prohibited / restricted / unrestricted
- **Basis:** [which policy, and why this product lands there]

## Preconditions the advertiser owns

Things that must be true outside the creative before this can launch. Leave the table
out entirely if there are none — don't pad it.

| # | Requirement | Owner | Status |
|---|---|---|---|
| 1 | e.g. 18+ age targeting set at campaign level | advertiser | not yet set |
| 2 | e.g. regulator licence uploaded to Ads Manager | advertiser | unknown |
| 3 | e.g. responsible-drinking disclaimer on landing page | advertiser | outstanding |

## Legal layer (EU/EEA markets)

Delete this section for non-EU campaigns. Keep it whenever any EU or EEA market is targeted —
the platform approving the ad does not resolve any of it.

| Area | Status |
|---|---|
| Green / sustainability claims (Dir. (EU) 2024/825, applies since 27 Sep 2026) | n/a · clear · **outstanding** |
| Price-reduction claims (PID Art. 6a — 30-day lowest prior price) | n/a · confirmed by advertiser · **unverified** |
| Health / nutrition claim wording (Reg. (EC) 1924/2006 register) | n/a · clear · **outstanding** |
| Cosmetic claim substantiation (Reg. (EU) 655/2013) | n/a · clear · **outstanding** |
| AI Act Art. 50 synthetic-content disclosure (in force since 2 Aug 2026) | n/a · on-screen label applied · **outstanding** |
| Influencer / creator disclosure (national rules) | n/a · on-screen label applied · **outstanding** |
| Pixel consent, advanced matching, DSA targeting limits | advertiser-owned — confirmed? |
| Member-state specifics (FR, DE, IT, SE, NO, GR, ES, LT, NL, BE) | which apply, and are they met |

Flag anything marked **outstanding** as a launch blocker, not a nice-to-have. Note explicitly
where a call needs the advertiser's own legal review — a regulated vertical, a large spend, or
a novel claim all warrant it, and saying so is not hedging.

## Checks run

| Check | Result |
|-------|--------|
| Platform policy | checked against `references/platforms/<platform>/` · **not checked** (platform not covered) |
| Copy lint (`lint_copy.py`) | n block · n review · n note (platform: ___, market: ___, vertical: ___, language: ___, EU pack on/off) |
| Media preflight (`preflight_media.py`) | n fail · n warn · n pass |
| Safe-zone overlay reviewed | yes / no — [what you saw] |
| Music rights | CML / direct sync licence / original / **unresolved** |
| Landing page consistency | checked / not checked / n/a |
| AIGC disclosure | not applicable / applied / **outstanding** |

## Changes made for compliance

What you changed and why, so the user can push back if a change cost something they cared about.

- [original phrasing] → [rewrite] — [policy reason]

## Flagged and accepted

Anything the linter or policy raised that was consciously kept, with the justification.
If this section is empty, say "none" rather than deleting it — its emptiness is information.

- [flag] — kept because [reason]. Residual risk: [low/medium/high].

## Open questions

Decisions that depend on facts only the advertiser has. Name the fact, not just the doubt.

- [e.g. "Is the 'dermatologist tested' claim documented? If not it has to come out."]

---

*Passing these checks makes approval likely, not certain — the platform's ad review is its own
judgment, policies change, and market carve-outs vary. Live policy index for TikTok:*
*https://ads.tiktok.com/resources/help/article/tiktok-advertising-policies*

*The legal layer is a working compliance review, not legal advice. EU directives are transposed
differently per member state and carry real financial exposure.*
