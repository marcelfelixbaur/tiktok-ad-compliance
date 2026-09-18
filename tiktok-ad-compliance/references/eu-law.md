# EU / EEA Legal Layer

**Read this whenever any EU or EEA market is in scope.** It sits *on top of* TikTok's platform
policy, not inside it.

The distinction matters and is easy to get wrong: **TikTok approving an ad does not make it
lawful.** Ad review checks TikTok's policies. It does not check the Unfair Commercial Practices
Directive, the price-indication rules, the AI Act, or German pharmaceutical advertising law.
An ad can sail through review and still expose the advertiser to a regulator, a consumer
association, or a competitor injunction — and in several member states competitors can and do
sue over advertising claims directly.

So for EU campaigns there are two independent gates, and creative must clear both.

> **Not legal advice.** This is a working compliance layer built from published regulation and
> guidance, current as of September 2026. EU directives are transposed differently in each
> member state, national case law varies, and the rules below carry real financial exposure.
> For a regulated vertical, a large spend, or a novel claim, the advertiser needs their own
> legal review. Say so rather than implying this file settles it.

**Contents:** [Which law applies](#which-law-applies) · [Green claims](#green-claims--in-force-27-september-2026) · [Price and discounts](#price-and-discount-claims) · [AI disclosure](#ai-generated-content--in-force-since-2-august-2026) · [Unfair commercial practices](#unfair-commercial-practices-ucpd) · [Health, food, cosmetics](#health-food-and-cosmetics-claims) · [Data and targeting](#data-protection-and-targeting) · [Minors](#minors) · [Political ads](#political-advertising) · [Influencer disclosure](#influencer-and-creator-disclosure) · [Member-state specifics](#member-state-specifics) · [Sources](#sources)

## Which law applies

Targeting decides it, not where the advertiser sits. A US brand running ads at German
consumers is subject to German and EU rules. The main instruments touching ad creative:

| Instrument | What it governs | Status |
|---|---|---|
| UCPD 2005/29/EC | Misleading and aggressive practices; Annex I blacklist | In force |
| Directive (EU) 2024/825 (ECGT / "EmpCo") | Environmental and durability claims | **Applies 27 Sep 2026** |
| Price Indication Directive 98/6/EC Art. 6a (via Omnibus 2019/2161) | Price-reduction announcements | In force since 28 May 2022 |
| AI Act (EU) 2024/1689 Art. 50 | Disclosure of synthetic content and deepfakes | **Applies since 2 Aug 2026** |
| DSA (EU) 2022/2065 Arts. 26, 28 | Ad transparency; targeting of minors; special-category data | In force |
| GDPR (EU) 2016/679 + ePrivacy 2002/58/EC | Pixels, tracking, retargeting, lead data | In force |
| Reg. (EC) 1924/2006 | Nutrition and health claims on food and supplements | In force |
| Reg. (EC) 1223/2009 + Reg. (EU) 655/2013 | Cosmetic product claims | In force |
| AVMSD 2010/13/EU (as amended by 2018/1808) | Commercial communications, minors, alcohol, HFSS | In force |
| TTPA (EU) 2024/900 | Political advertising | Applies since 10 Oct 2025 |

On the horizon: the **Digital Fairness Act** is in progress and is expected to tighten
influencer marketing, dark patterns, and personalisation. Not law yet — don't write to it,
but don't build a campaign that only works if it never arrives.

## Green claims — in force 27 September 2026

The single most likely thing to catch an otherwise careful 2026 campaign, because the phrasing
it bans is exactly the phrasing brands have used for a decade. Directive (EU) 2024/825 amends
the UCPD and adds these to the Annex I blacklist — meaning **unfair in all circumstances**, no
case-by-case balancing:

- **Generic environmental claims** with no demonstrated excellent environmental performance:
  "eco-friendly", "green", "environmentally friendly", "eco", "climate friendly", "gentle on
  the environment", "kind to nature", "natural", "biodegradable" used as a bare adjective.
  The recognised way to hold one is an EU Ecolabel or equivalent certified scheme.
- **Carbon-neutral / climate-neutral / net-zero claims based on offsetting.** "Carbon neutral
  delivery", "climate positive", "CO2-compensated" are blacklisted where the basis is offsets.
- **Future environmental performance claims** — "carbon neutral by 2030", "will be fully
  recycled" — unless backed by clear, verifiable, time-bound commitments and an independently
  verified implementation plan.
- **Sustainability labels** not based on a certification scheme or established by public authorities.
- Claims about the whole product when they only concern one aspect of it.
- Presenting legally required attributes as a distinctive feature ("CFC-free", "no lead").

Exposure runs to fines of up to **4% of annual turnover** in member states that set penalties
that way, plus confiscation of revenue and exclusion from public procurement.

**Practical rewrite:** replace the adjective with the specific, measurable, verified fact.
"Eco-friendly packaging" → "carton is 80% recycled fibre, FSC-certified". If the specific fact
isn't available, the claim doesn't go in the ad.

## Price and discount claims

Price Indication Directive Art. 6a. Any announcement of a price reduction must state the prior
price, and **the prior price is the lowest price the trader applied in the 30 days before the
reduction.**

This catches more than a struck-through price:

- "20% off", "save €30", "from €99 to €79", crossed-out pricing
- General campaign framing: "Sale", "Black Friday deals", "Mid-season sale"
- "Lowest price ever", "best deal", "biggest discount of the year"

The percentage, the reference price, and any superlative flourish all have to line up with that
30-day low — not RRP, not the manufacturer's suggested price, not a briefly-restored high price.
The classic violation: a product sits at €99 for three weeks, jumps to €149 for two days, then
"drops" to €89 advertised as saving €60. The lawful reference is €99.

For creative, this means **any discount number in an ad needs the advertiser to confirm the
30-day low before it's rendered.** Treat an unverified discount figure as a blocker, not a
detail — it's baked into the video and expensive to change.

## AI-generated content — in force since 2 August 2026

Two separate obligations, and a TikTok campaign can trigger both:

- **Art. 50(2)** — synthetic audio, image, video, or text must be marked in a machine-readable
  format and detectable as AI-generated. That duty sits with the provider of the generating
  system, but a deployer choosing tools should confirm the tooling does it.
- **Art. 50(4)** — a deployer creating a **deepfake** must disclose that the content is
  artificially generated or manipulated. This bites on ad creative directly.

Points that trip people up:

- **The deepfake duty applies without intent to deceive.** A synthetic presenter, an AI voice,
  or an AI-generated person who looks real needs disclosure even where nobody is being fooled
  and even where the person doesn't exist.
- Disclosure must be **clear, distinguishable, accessible, and given no later than first
  exposure** — visible for visual content, audible where audio is the relevant mode. A line in
  the campaign settings is not disclosure; an on-screen label is.
- It applies to **non-EU advertisers targeting EU audiences.**

This overlaps with, but is stricter than, TikTok's own AIGC labelling rule in
`claims-and-copy.md`. Satisfy the AI Act and you satisfy TikTok; the reverse isn't guaranteed.

## Unfair commercial practices (UCPD)

The general standard behind most national advertising enforcement. A practice is unfair if it
is misleading (by action or omission) or aggressive and distorts the average consumer's
transactional decision. Annex I lists practices banned outright in all circumstances —
including bait advertising, false "limited time" claims, falsely claiming a product cures
illness, fake free offers, and (from 27 Sep 2026) the green claims above.

Two that hit TikTok creative specifically:

- **False urgency.** "Only 3 left", "ends tonight", countdown timers — a blacklisted practice
  when untrue. TikTok flags this as deceptive; the UCPD makes it unlawful.
- **Material omissions.** Where the ad is the invitation to purchase, the main characteristics,
  total price including unavoidable charges, and delivery costs must be apparent. A 9-second
  video can't carry everything, but the price shown must not become materially higher at checkout.

## Health, food, and cosmetics claims

Stricter than TikTok policy, and stricter than US practice — this is where US-written copy
most often becomes unlawful in the EU.

**Food and supplements — Reg. (EC) 1924/2006.** Only claims on the **EU Register of authorised
health claims** may be used, in the authorised wording or wording with the same meaning, and
only where the conditions of use are met. Consequences:

- "Boosts your immune system" is not authorised. "Vitamin C contributes to the normal function
  of the immune system" is, if the product qualifies as a source of vitamin C.
- **"Detox" is not an authorised claim.** Neither are most "burns fat", "speeds metabolism",
  "cleanses", or general wellbeing claims made without an authorised specific claim alongside.
- Claims referring to the rate or amount of weight loss are **prohibited outright** for foods.
- Claims that a food prevents, treats or cures disease are prohibited outright.
- A nutrition claim ("high in fibre", "low fat") must meet the Annex conditions.

**Cosmetics — Reg. (EC) 1223/2009 and the Common Criteria in Reg. (EU) 655/2013.** Claims must
be legally compliant, truthful, evidence-based, honest, fair, and allow informed decisions.
"Free from" claims are heavily restricted where the ingredient was never lawful or never used
in the category; "hypoallergenic" requires substantiation; a cosmetic may not claim to treat a
medical condition (that would make it a medicinal product).

**Medicines — national law, e.g. Germany's Heilmittelwerbegesetz (HWG).** Advertising
prescription medicines to the public is prohibited EU-wide. Several member states impose
additional restrictions on OTC medicine and medical device advertising, mandatory warning
wording, and restrictions on testimonials and before/after imagery in a health context.

## Data protection and targeting

Creative-adjacent but campaign-critical, and the advertiser owns it:

- **The TikTok Pixel requires prior opt-in consent** in the EU/EEA. It must not fire before
  consent — blocked entirely, not merely sending a denied signal. Reject-all must be one click
  and visually equal to accept-all; pre-ticked boxes and dark patterns fail.
- **Advanced matching** (hashed email, phone, name) is a personal-data transfer to TikTok and
  needs a lawful basis and disclosure in the privacy policy.
- **DSA Art. 26(3):** no ad targeting based on profiling using special-category data
  (health, religion, sexuality, political opinion, ethnicity, trade union membership).
  A campaign inferring a health condition to target is unlawful regardless of creative.
- **DSA Art. 28(2):** no profiling-based advertising to users known with reasonable certainty
  to be minors.
- **Lead ads** need a GDPR-compliant privacy notice, a lawful basis, and no bundled consent.

Expect EU consent rates of roughly 40–60%, which changes measurement expectations — worth
flagging when someone benchmarks EU performance against US.

## Minors

Beyond TikTok's own teen-safety policy and DSA Art. 28:

- **Sweden and Norway** prohibit television advertising directed at children under 12. That
  statutory ban covers broadcasting; online marketing to children falls under each country's
  general marketing law, enforced by the consumer ombudsman. Treat child-directed creative in
  these markets as high-risk.
- **Greece** bans toy advertising on television within defined hours.
- **Flemish Belgium** restricts advertising around children's programming.
- **AVMSD Art. 9** bars commercial communications causing physical, mental or moral detriment
  to minors — no direct exhortation to buy exploiting inexperience, no encouraging minors to
  persuade parents, no exploiting their trust in parents or teachers.
- HFSS food and drink advertising around children's content is restricted through national
  codes of conduct under AVMSD Art. 9(2), with several member states going further.

## Political advertising

TikTok bans paid political advertising globally, and the **TTPA (EU) 2024/900** has applied
since 10 October 2025 — leading Meta and Google to stop EU political ads entirely. Treat any
political, electoral, or social-issue advertising as **not available** on TikTok in the EU.
Where a client's cause-based campaign might read as social-issue advertising, raise it before
production rather than after.

## Influencer and creator disclosure

Where creative is a creator post, a Spark Ad, or whitelisted UGC, disclosure duties attach to
both the creator and the brand — and in France they are jointly and severally liable.

- Disclosure must be clear, upfront, and understandable — not buried in hashtags at the end.
- **Germany:** `#Werbung` or `#Anzeige`, placed at the start.
- **France:** the Loi Delaporte-Vojetta (June 2023) requires clear labelling such as
  `#sponsorisé`, `#partenariat rémunéré`, or "publicité"; it also covers gifted product.
- **Italy:** AGCOM rules under the Audiovisual Media Act apply to influencers above roughly one
  million followers, with penalties from €30,000 to €600,000 for breaches affecting minors.
- Gifted product, affiliate links, and the brand's own employees all count as commercial
  relationships requiring disclosure.
- Enforcement is active — penalties have landed in France, Latvia, Romania, Norway, Denmark
  and Poland.

Disclosure has to survive the format: a label that only exists in the caption disappears when
the caption is truncated. Put it on screen.

## Member-state specifics

Check these before producing for the market. Not exhaustive — a prompt to verify, not a substitute.

| Market | Watch for |
|---|---|
| **France** | Loi Évin: alcohol advertising works on a *positive list* — anything not expressly permitted is prohibited, and content is restricted to factual product attributes. Pharmacy advertising prohibited (also a TikTok rule). Influencer Act liability. Mandatory French language (Loi Toubon). |
| **Germany** | HWG restrictions on health-product advertising; UWG allows competitors and trade associations to issue cease-and-desist warnings (*Abmahnung*) over ad claims — an unusually fast enforcement route. Strict on comparative advertising and on `#Werbung` placement. |
| **Italy** | AGCOM influencer rules; strong minors provisions with high penalties. |
| **Sweden / Norway** | Advertising directed at under-12s restricted; Norway bans alcohol advertising outright. |
| **Greece** | Pharmacy advertising prohibited (TikTok rule); toy advertising restricted on TV. |
| **Spain** | Restrictions on gambling advertising (Royal Decree 958/2020) are among the strictest in the EU — tight windows and heavy limits on promotional offers. |
| **Netherlands / Denmark / Poland** | Active consumer-authority enforcement on influencer disclosure and pricing claims. |
| **Ireland / Malta / Cyprus** | English-language creative often defaults here; confirm alcohol and gambling rules separately. |

**Language:** several markets require, or effectively require, local-language advertising —
France by statute. Beyond compliance, TikTok itself rejects copy with spelling and grammar
errors, so machine-translated creative fails twice over. Have local-language copy reviewed by
a speaker.

**The UK is not in scope here.** It is not an EU market: it has UK GDPR, the CAP/BCAP Codes
administered by the ASA, and the DMCCA 2024 regime. Similar in spirit, different in detail —
don't apply this file to UK campaigns without checking.

## Sources

- UCPD and green claims (Directive (EU) 2024/825): https://eur-lex.europa.eu/eli/dir/2024/825/oj
- Price Indication Directive Art. 6a guidance: https://commission.europa.eu/law/law-topic/consumer-protection-law_en
- AI Act Art. 50 guidance: https://digital-strategy.ec.europa.eu/en/policies/guidelines-ai-transparency-obligations
- DSA: https://eur-lex.europa.eu/eli/reg/2022/2065/oj
- EU Register of health claims: https://food.ec.europa.eu/food-safety/labelling-and-nutrition/nutrition-and-health-claims/eu-register-health-claims_en
- Cosmetics claims common criteria (Reg. (EU) 655/2013): https://eur-lex.europa.eu/eli/reg/2013/655/oj
- TTPA (Reg. (EU) 2024/900): https://commission.europa.eu/strategy-and-policy/policies/justice-and-fundamental-rights/democracy-eu-citizenship-anti-corruption/democracy-and-electoral-rights/transparency-and-targeting-political-advertising_en
- Commission Influencer Legal Hub: https://commission.europa.eu/topics/consumers/consumer-rights-and-complaints/influencer-legal-hub_en
