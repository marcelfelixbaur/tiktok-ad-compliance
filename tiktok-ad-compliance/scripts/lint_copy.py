#!/usr/bin/env python3
"""Lint TikTok ad copy against the claim patterns that get ads rejected.

This flags language for a human decision — it does not adjudicate. Some flags are
fine in context (a substantiated comparison, a disclosed risk warning). Every flag
needs a deliberate call, though, because review treats these categories strictly.

Usage:
    lint_copy.py --text "Lose 10lbs in 2 weeks, guaranteed!"
    lint_copy.py --file script.txt --vertical health --market US
    lint_copy.py --text "Glow Serum" --field brand_name
    lint_copy.py --file caption.txt --field caption --json
"""

import argparse
import json
import re
import sys
import unicodedata

# severity: BLOCK  = very likely rejected as written
#           REVIEW = needs justification, substantiation, or a disclaimer
#           NOTE   = spec/limit/hygiene issue

RULES = [
    # --- Absolute superiority -------------------------------------------------
    dict(id="superlative-absolute", severity="BLOCK",
         pattern=r"(?:#\s?1\b|\bno\.?\s?1\b|\bnumber one\b|"
                 r"\bworld'?s (?:best|leading|number one|#\s?1)\b|"
                 r"\bthe (?:best|greatest)\b|\bunmatched\b|\bunbeatable\b|"
                 r"\bunrivall?ed\b|\bsecond to none\b)",
         policy="Misleading and false content — absolute superiority claims",
         fix="Replace with a specific, evidenced fact (review counts, a named test result, a dated award)."),
    dict(id="superlative-soft", severity="REVIEW",
         pattern=r"(?:\b(?:most effective|most powerful|top[- ]rated|award[- ]winning|revolutionary|"
                 r"game[- ]chang(?:er|ing)|perfect|the only \w+ that|"
                 r"(?:\w+ ){0,2}ever made|like no other)\b|(?<!the )\bbest\b)",
         policy="Misleading and false content — exaggerated claims",
         fix="Substantiate or soften. 'Award-winning' needs the named award on the landing page."),

    # --- Guarantees and promised outcomes ------------------------------------
    dict(id="guarantee", severity="BLOCK",
         pattern=r"\b(guarantee[ds]?|guaranteed results|100%\s*(?:effective|guaranteed|results|works)|"
                 r"risk[- ]free|no[- ]risk|fool[- ]?proof|works for everyone|never fails)\b",
         policy="Misleading and false content — promised results",
         fix="Drop the guarantee. A money-back returns policy is a different, allowable statement."),
    dict(id="instant-results", severity="BLOCK",
         pattern=r"\b(instant(?:ly|aneous)?|right away|overnight|in (?:just )?(?:\d+|a few|one|two|three)\s*"
                 r"(?:seconds?|minutes?|hours?|days?|weeks?)|immediate results?|see results (?:fast|in)|"
                 r"within (?:days?|hours?))\b",
         policy="Misleading and false content — 'must not promise or exaggerate results'",
         fix="Describe the mechanism or usage instead of a timeline to an outcome."),

    # --- Medical and health claims -------------------------------------------
    dict(id="medical-claim", severity="BLOCK",
         pattern=r"\b(cure[sd]?|curing|heal(?:s|ed|ing)?|treat(?:s|ed|ing|ment of)?|remedy|remedies|"
                 r"prevent(?:s|ed|ing)?|reverse[sd]?|eliminate[sd]? (?:your )?(?:pain|acne|anxiety|"
                 r"depression|symptoms?)|miracle|medically proven|doctor[- ]recommended|"
                 r"clinically proven to (?:cure|treat|heal))\b",
         policy="Healthcare — no medicinal claims to treat, cure, heal or prevent any condition",
         fix="Describe ingredients, formulation, or sensory experience. Medical claims need a licence."),
    dict(id="serious-disease", severity="BLOCK",
         pattern=r"\b(cancer|hiv|aids|covid(?:-?19)?|multiple sclerosis|parkinson'?s|alzheimer'?s|diabetes|"
                 r"tumou?rs?)\b",
         policy="Healthcare — cannot imply serious diseases are treatable by the product",
         fix="Remove the disease reference entirely unless the advertiser is a licensed medical provider."),
    dict(id="regulatory-namedrop", severity="REVIEW",
         pattern=r"\b(fda[- ]approved|ce[- ]certified|clinically proven|scientifically proven|"
                 r"dermatologist[- ](?:tested|approved)|lab[- ]tested)\b",
         policy="Healthcare / misleading content — regulatory claims must be accurate and evidenced",
         fix="Confirm the claim is literally true and documented; 'FDA registered' ≠ 'FDA approved'."),

    # --- Weight and body image -----------------------------------------------
    dict(id="weight-loss-quantified", severity="BLOCK",
         pattern=r"\b(lose|drop|shed|burn|melt(?:s|ing)?(?: away)?)\s+(?:up to\s+)?"
                 r"(?:\d+\s*(?:lbs?|pounds?|kgs?|kilos?|inches|sizes?|stone)|weight fast|fat fast|belly fat)\b",
         policy="Weight management — unrealistic weight loss, product-alone claims",
         fix="Remove the quantity and timeline. Describe the product, not the body outcome."),
    dict(id="body-ideal", severity="BLOCK",
         pattern=r"\b(bikini body|beach body|dream body|perfect body|ideal body|summer body|snatched|"
                 r"flat (?:belly|stomach|tummy)|slim(?:mer)? (?:legs|waist|thighs)|skinny|"
                 r"get your body back|problem areas)\b",
         policy="Weight management and body image — no ideal body type, no body shaming",
         fix="Talk about fit, fabric, comfort, or performance rather than body shape."),
    dict(id="body-life-outcome", severity="BLOCK",
         pattern=r"\b(finally (?:feel|love|be)|feel confident (?:again|in your)|"
                 r"(?:more|be) (?:desirable|attractive|popular|successful)|"
                 r"love (?:your(?:self)?|your body) again|new you|best version of you)\b",
         policy="Body image — cannot link appearance to improved life circumstances or self-image",
         fix="Cut the transformation-of-self framing; describe what the product is and does."),
    dict(id="effortless", severity="BLOCK",
         pattern=r"\b(no diet(?:ing)? (?:or|and) (?:exercise|workout)|without (?:diet|exercise|working out)|"
                 r"effortless(?:ly)?|no effort|while you sleep|easy weight loss|lose weight easily)\b",
         policy="Weight management — no claims the product alone works, or that it is easy/guaranteed",
         fix="Remove. This is one of the most consistently enforced rules in the policy set."),
    dict(id="before-after", severity="REVIEW",
         pattern=r"\b(before (?:and|&|/|\s*-\s*)\s*after|before/after|b&a|my transformation|"
                 r"\d+\s*(?:days?|weeks?|months?) (?:transformation|progress|results))\b",
         policy="Misleading content — before/after comparisons creating a false impression; prohibited "
                "outright for OTC medicines and supplements",
         fix="Avoid entirely for health, supplement, and body products."),

    # --- Financial ------------------------------------------------------------
    dict(id="financial-exaggerated", severity="BLOCK",
         pattern=r"\b(get rich|getting rich|financial freedom|passive income|"
                 r"(?:double|triple|10x|100x) your (?:money|investment|income)|"
                 r"turn \$?\d+ into|make \$?\d+[kK]?\s*(?:a|per|/)\s*(?:day|week|month)|"
                 r"guaranteed returns?|risk[- ]free investment|quit your job|beat the market)\b",
         policy="Financial services / deceptive practices — exaggerated financial claims, get-rich-quick",
         fix="Remove. Income and return claims are prohibited even when historically accurate."),
    dict(id="financial-disclosure-missing", severity="REVIEW", vertical="finance",
         pattern=r"\b(loan|credit|apr|interest|invest(?:ing|ment)?|trading|crypto|bitcoin|"
                 r"portfolio|returns?|shares?|stocks?)\b",
         policy="Financial services — must disclose rates, APR, fees, repayment terms and disclaimers",
         fix="Add the required risk warning / APR / representative example, legible on screen."),

    # --- Manufactured urgency and clickbait -----------------------------------
    dict(id="false-urgency", severity="REVIEW",
         pattern=r"\b(only \d+ (?:left|remaining|spots?|seats?)|last chance|hurry|act now|"
                 r"ends (?:today|tonight|in \d+)|limited spots?|almost gone|selling out fast|"
                 r"don'?t miss out|final hours?)\b",
         policy="Deceptive practices — manufactured urgency is misleading if not literally true",
         fix="Keep only if verifiably true and reflected on the landing page."),
    dict(id="clickbait-interaction", severity="REVIEW",
         pattern=r"\b(don'?t scroll|stop scrolling|tap (?:here|to reveal|the x)|click here|"
                 r"you won'?t believe|doctors hate|this one (?:trick|weird))\b",
         policy="Deceptive practices — clickbait; interactive elements must function as intended",
         fix="Write a hook that states the value instead of withholding it."),

    # --- TikTok brand ---------------------------------------------------------
    dict(id="tiktok-brand", severity="BLOCK",
         pattern=r"\b(tiktok\s*(?:bestseller|famous|made me buy|shop)|as seen on tiktok|"
                 r"viral on tiktok|tiktok'?s? (?:favou?rite|#\s?1)|bytedance)\b",
         policy="IP / format — no TikTok branding or implied TikTok endorsement in ad content",
         fix="Remove all TikTok references from creative and landing page."),

    # --- Adult / suggestive ---------------------------------------------------
    dict(id="adult-suggestive", severity="BLOCK",
         pattern=r"\b(nude|naked|nsfw|xxx|porn|sexy|seductive|horny|hook ?up|one night stand|"
                 r"casual sex|sugar (?:daddy|mommy|baby|dating)|cam ?girl|escort)\b",
         policy="Adult content — sexually suggestive or explicit text is prohibited",
         fix="Remove. Dating apps framed around casual sex cannot be advertised at all."),

    # --- Prohibited products flagged from copy --------------------------------
    dict(id="prohibited-product", severity="BLOCK",
         pattern=r"\b(vape[sr]?|vaping|e-?cig(?:arette)?s?|nicotine|tobacco|cigarettes?|"
                 r"payday loans?|bail bonds?|credit repair|pyramid|mlm|"
                 r"kratom|delta[- ]?8|thc)\b",
         policy="Dangerous products / financial services — globally prohibited categories",
         fix="This product category cannot be advertised on TikTok. Check restricted-verticals.md."),
    dict(id="crypto", severity="REVIEW",
         pattern=r"\b(crypto(?:currency)?|bitcoin|btc|ethereum|nft|web3|token sale|ico|defi|airdrop)\b",
         policy="Financial services — virtual currencies broadly restricted, market-specific approval needed",
         fix="Treat as prohibited unless the market and licensing are confirmed with a TikTok rep."),

    # --- Minors ---------------------------------------------------------------
    dict(id="teen-pressure", severity="BLOCK",
         pattern=r"\b(ask your (?:mom|dad|parents?|mum)|tell your parents|beg your parents|"
                 r"get your parents to buy)\b",
         policy="Teen safety — no encouraging teens to persuade parents or guardians to purchase",
         fix="Remove; address the purchasing adult directly."),

    # =========================================================================
    # EU / EEA legal layer. These are matters of law, not TikTok policy — an ad
    # can pass TikTok review and still be unlawful. See references/eu-law.md.
    # =========================================================================

    dict(id="eu-green-generic", severity="BLOCK", markets=["EU"],
         pattern=r"\b(eco[- ]?friendly|environmentally friendly|climate[- ]friendly|planet[- ]friendly|"
                 r"kind to (?:nature|the planet)|gentle on the environment|green product|"
                 r"eco[- ]conscious|earth[- ]friendly)\b",
         policy="Directive (EU) 2024/825 (from 27 Sep 2026) — generic environmental claims are "
                "blacklisted under UCPD Annex I unless backed by recognised excellent performance",
         fix="Replace with the specific verified fact ('carton is 80% recycled fibre, FSC-certified') "
             "or hold an EU Ecolabel."),
    dict(id="eu-green-offset", severity="BLOCK", markets=["EU"],
         pattern=r"\b(carbon[- ]neutral|climate[- ]neutral|co2[- ]neutral|net[- ]zero|carbon[- ]negative|"
                 r"climate[- ]positive|carbon[- ]offset|co2[- ]compensated|offset your carbon)\b",
         policy="Directive (EU) 2024/825 — carbon/climate-neutrality claims based on offsetting are "
                "blacklisted outright",
         fix="Remove. Offset-based neutrality claims cannot be made to EU consumers at all."),
    dict(id="eu-green-future", severity="REVIEW", markets=["EU"],
         pattern=r"\b(?:will be|aiming to be|committed to (?:being|becoming)|on track to be)\s+"
                 r"(?:\w+\s+){0,3}(?:carbon[- ]neutral|climate[- ]neutral|net[- ]zero|sustainable|"
                 r"fully recycl\w+)|\b(?:carbon[- ]neutral|net[- ]zero)\s+by\s+\d{4}\b",
         policy="Directive (EU) 2024/825 — future environmental performance claims need clear, "
                "verifiable, time-bound commitments and an independently verified implementation plan",
         fix="Drop it, or cite the published, independently verified plan."),
    dict(id="eu-green-soft", severity="REVIEW", markets=["EU"],
         pattern=r"\b(sustainable|sustainably|responsibly sourced|ethically (?:made|sourced)|"
                 r"biodegradable|compostable|all[- ]natural|100% natural|chemical[- ]free|"
                 r"plastic[- ]free|zero waste)\b",
         policy="Directive (EU) 2024/825 / UCPD — vague or unsubstantiated sustainability claims, and "
                "claims about one aspect presented as covering the whole product",
         fix="Substantiate against a certification scheme, scope the claim to the exact attribute, "
             "or remove."),

    dict(id="eu-price-reduction", severity="REVIEW", markets=["EU"],
         pattern=r"(?:\d+\s*%\s*(?:off|reduction|discount)|\bsave\s*[€£$]?\d+|"
                 r"\b(?:was|rrp|reduced from|instead of)\s*[€£$]?\d+|[€£$]\d+\s*(?:→|->|to)\s*[€£$]?\d+|"
                 r"\b(?:sale|black friday|cyber monday|mid[- ]season sale|clearance|"
                 r"lowest price ever|biggest discount|best deal)\b)",
         policy="Price Indication Directive Art. 6a (Omnibus) — a price-reduction announcement must "
                "reference the LOWEST price applied in the 30 days before the reduction, not RRP",
         fix="Have the advertiser confirm the 30-day low BEFORE this is rendered — the number is "
             "baked into the video and expensive to change afterwards."),

    dict(id="eu-health-claim", severity="BLOCK", markets=["EU"],
         pattern=r"\b(boosts? (?:your )?(?:immunity|immune system|metabolism)|immune[- ]boosting|"
                 r"detox(?:es|ify|ifying|ification)?|cleanses? your (?:body|system|gut)|"
                 r"burns? fat|fat[- ]burning|speeds? up (?:your )?metabolism|"
                 r"strengthens? (?:your )?immune)\b",
         policy="Reg. (EC) 1924/2006 — only claims on the EU Register of authorised health claims may "
                "be used, in the authorised wording; 'detox' and 'immune boosting' are not authorised",
         fix="Use the authorised wording, e.g. 'Vitamin C contributes to the normal function of the "
             "immune system', and only if the product meets the conditions of use."),
    dict(id="eu-weight-rate-food", severity="BLOCK", markets=["EU"], vertical="health",
         pattern=r"\b(lose \d+|\d+\s*(?:kg|lbs?|pounds?) (?:in|per|a) (?:week|month|day)|"
                 r"rapid weight loss|fast weight loss)\b",
         policy="Reg. (EC) 1924/2006 — claims referring to the RATE or AMOUNT of weight loss are "
                "prohibited outright for foods and food supplements",
         fix="Remove any rate or amount of weight loss. This is an absolute prohibition, not a "
             "substantiation question."),
    dict(id="eu-cosmetics-claim", severity="REVIEW", markets=["EU"],
         pattern=r"\b(free[- ]from|paraben[- ]free|sulphate[- ]free|sulfate[- ]free|silicone[- ]free|"
                 r"hypoallergenic|non[- ]comedogenic|dermatologically (?:tested|proven))\b",
         policy="Reg. (EU) 655/2013 Common Criteria — cosmetic claims must be truthful, evidence-based "
                "and fair; 'free from' claims are restricted where the ingredient was never lawful or "
                "never used in the category",
         fix="Hold the substantiation file, and drop 'free from' claims that denigrate lawful ingredients."),

    dict(id="eu-political", severity="BLOCK", markets=["EU"],
         pattern=r"\b(vote (?:for|against|now)|election|referendum|ballot|political party|"
                 r"our campaign for|sign the petition)\b",
         policy="TTPA (EU) 2024/900 + TikTok global ban — paid political, electoral and social-issue "
                "advertising is not available on TikTok in the EU",
         fix="This cannot run as a paid ad. Raise it before production, not after."),
]

FIELD_LIMITS = {
    # field: (min_latin, max_latin, allow_emoji, banned_chars)
    "brand_name":  (2, 20, False, ""),
    "app_name":    (4, 40, False, ""),
    "description": (1, 100, False, "{}#"),
    "caption":     (1, 100, True, ""),
    "account_name": (1, 20, True, ""),
}

EU_EEA = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE",
    "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    "IS", "LI", "NO",
}

# Country-specific reminders surfaced as notes. Not exhaustive -- a prompt to verify.
MARKET_NOTES = {
    "FR": "Loi Évin: alcohol advertising runs on a POSITIVE LIST — anything not expressly "
          "permitted is prohibited. Pharmacy ads prohibited. Loi Toubon requires French. "
          "Influencer Act creates joint liability between brand and creator.",
    "DE": "HWG restricts health-product advertising. UWG lets competitors and trade bodies "
          "issue cease-and-desist warnings (Abmahnung) over ad claims — fast, cheap for them, "
          "expensive for you. Disclosure must read #Werbung or #Anzeige, placed at the start.",
    "IT": "AGCOM influencer rules apply above ~1M followers; penalties €30k–€600k where minors "
          "are affected.",
    "SE": "Advertising directed at children under 12 is restricted.",
    "NO": "Advertising directed at children under 12 is restricted; alcohol advertising is "
          "banned outright.",
    "GR": "Pharmacy advertising prohibited; toy advertising restricted on TV.",
    "ES": "Gambling advertising is among the most tightly restricted in the EU "
          "(Royal Decree 958/2020).",
}


def market_scopes(market):
    """Map a --market value to the rule scopes it activates."""
    if not market:
        return set()
    raw = {m.strip().upper() for m in re.split(r"[,/\s]+", market) if m.strip()}
    scopes = set(raw)
    if raw & EU_EEA or raw & {"EU", "EEA", "EU/EEA", "EUROPE"}:
        scopes.add("EU")
    return scopes


EMOJI_RE = re.compile(
    "[" "\U0001F000-\U0001FAFF" "\U00002600-\U000027BF" "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF" "\U00002B00-\U00002BFF" "️" "]"
)


def has_emoji(text):
    if EMOJI_RE.search(text):
        return True
    return any(unicodedata.category(ch) == "So" for ch in text)


def context(text, match, width=48):
    start = max(0, match.start() - width // 2)
    end = min(len(text), match.end() + width // 2)
    snippet = text[start:end].replace("\n", " ").strip()
    return ("…" if start > 0 else "") + snippet + ("…" if end < len(text) else "")


def lint(text, vertical=None, field=None, aigc=False, scopes=None, creator=False):
    findings = []
    lowered = text.lower()
    scopes = scopes or set()

    for rule in RULES:
        if rule.get("vertical") and rule["vertical"] != vertical:
            continue
        if rule.get("markets") and not (set(rule["markets"]) & scopes):
            continue
        for m in re.finditer(rule["pattern"], lowered, re.IGNORECASE):
            findings.append(dict(
                id=rule["id"], severity=rule["severity"], matched=text[m.start():m.end()],
                context=context(text, m), policy=rule["policy"], fix=rule["fix"],
            ))

    # Field-level spec checks
    if field and field in FIELD_LIMITS:
        lo, hi, allow_emoji, banned = FIELD_LIMITS[field]
        n = len(text.strip())
        if n < lo or n > hi:
            findings.append(dict(
                id="field-length", severity="NOTE", matched=f"{n} characters",
                context=text[:60], policy=f"Spec — {field} must be {lo}–{hi} Latin characters",
                fix=f"Adjust to {lo}–{hi} characters (Asian-script limits are roughly half).",
            ))
        if not allow_emoji and has_emoji(text):
            findings.append(dict(
                id="field-emoji", severity="NOTE", matched="emoji present", context=text[:60],
                policy=f"Spec — emoji are not supported in {field}",
                fix="Remove emoji from this field.",
            ))
        for ch in banned:
            if ch in text:
                findings.append(dict(
                    id="field-banned-char", severity="NOTE", matched=ch, context=text[:60],
                    policy=f"Spec — '{ch}' is not supported in {field}",
                    fix=f"Remove '{ch}'.",
                ))

    # Cheap hygiene proxies — spelling/grammar errors are an enumerated rejection reason
    for m in re.finditer(r"\b(\w+)\s+\1\b", lowered):
        findings.append(dict(
            id="doubled-word", severity="NOTE", matched=m.group(0), context=context(text, m),
            policy="Ad format — caption and text must be free of spelling and grammatical mistakes",
            fix="Proofread; duplicated word.",
        ))
    if re.search(r"[A-Z]{6,}", text) and field != "brand_name":
        findings.append(dict(
            id="shouting", severity="NOTE", matched="ALL CAPS run", context=text[:60],
            policy="Ad quality — excessive capitalisation reads as low-quality to review",
            fix="Use sentence case for body copy; reserve caps for short emphasis.",
        ))

    if aigc:
        disclosed = re.search(r"\b(ai[- ]generated|generated with ai|ai[- ]created|synthetic|aigc|"
                              r"created using ai|ai voice)\b", lowered)
        if not disclosed:
            findings.append(dict(
                id="aigc-undisclosed", severity="BLOCK", matched="(no disclosure found)",
                context="—",
                policy="Misleading content — AIGC requires the AIGC label or a clear visible disclaimer",
                fix="Apply the AIGC label in Ads Manager and add a visible on-screen disclosure.",
            ))
        if "EU" in scopes:
            findings.append(dict(
                id="eu-ai-act-disclosure", severity="BLOCK" if not disclosed else "REVIEW",
                matched="AI-generated creative targeting EU", context="—",
                policy="AI Act (EU) 2024/1689 Art. 50 (applies since 2 Aug 2026) — deployers creating "
                       "deepfakes must disclose artificial generation; duty applies WITHOUT intent to "
                       "deceive, and to non-EU advertisers targeting EU audiences",
                fix="Disclosure must be clear, distinguishable and given no later than first exposure: "
                    "visible on screen for visual content, audible where audio is the relevant mode. "
                    "A campaign-level setting is not disclosure. Stricter than TikTok's own AIGC rule.",
            ))

    if creator and "EU" in scopes:
        tags = re.search(r"(#\s?(?:werbung|anzeige|ad|ads|advert|sponsored|sponsorisé|sponsorise|"
                         r"partenariat|publicidad|pubblicità|reklame|samarbeid|annonse)\b|"
                         r"\b(?:paid partnership|bezahlte partnerschaft|publicité)\b)", lowered)
        findings.append(dict(
            id="eu-creator-disclosure",
            severity="REVIEW" if tags else "BLOCK",
            matched=tags.group(0) if tags else "(no disclosure found)",
            context=text[:60],
            policy="UCPD + national influencer rules — commercial content must be disclosed clearly and "
                   "upfront. DE: #Werbung/#Anzeige at the start. FR: Loi Delaporte-Vojetta, brand and "
                   "creator jointly liable. IT: AGCOM, €30k–€600k where minors are affected",
            fix="Put the disclosure ON SCREEN, not only in the caption — captions truncate and the "
                "label disappears. Gifted product and affiliate links count as commercial relationships.",
        ))

    order = {"BLOCK": 0, "REVIEW": 1, "NOTE": 2}
    findings.sort(key=lambda f: order[f["severity"]])
    return findings


def main():
    p = argparse.ArgumentParser(description="Lint TikTok ad copy against policy claim patterns.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="Copy to lint.")
    src.add_argument("--file", help="File containing the copy (script, caption, VO).")
    p.add_argument("--vertical", help="health | finance | weight | beauty | gaming | general",
                   default="general")
    p.add_argument("--market", default="unspecified",
                   help="Target market(s), e.g. US, DE, 'DE,FR', or EU. EU/EEA codes activate the "
                        "EU legal rule pack (green claims, price rules, health claims, AI Act).")
    p.add_argument("--creator", action="store_true",
                   help="Creative is creator/UGC/Spark content — checks influencer disclosure.")
    p.add_argument("--field", choices=sorted(FIELD_LIMITS), help="Apply this field's spec limits.")
    p.add_argument("--aigc", action="store_true", help="Creative uses AI-generated media.")
    p.add_argument("--json", action="store_true", help="Machine-readable output.")
    a = p.parse_args()

    text = a.text if a.text else open(a.file, encoding="utf-8").read()
    scopes = market_scopes(a.market)
    findings = lint(text, vertical=a.vertical, field=a.field, aigc=a.aigc,
                    scopes=scopes, creator=a.creator)
    notes = [MARKET_NOTES[c] for c in sorted(scopes & set(MARKET_NOTES))]
    if "EU" in scopes and not (scopes & set(MARKET_NOTES)):
        notes.append("EU/EEA market with no specific country given — national rules differ "
                     "materially (FR, DE, IT, SE, NO, GR, ES each add their own). Narrow it down.")

    if a.json:
        print(json.dumps(dict(market=a.market, scopes=sorted(scopes), vertical=a.vertical,
                              field=a.field, findings=findings, market_notes=notes), indent=2))
    else:
        counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ("BLOCK", "REVIEW", "NOTE")}
        eu = " · EU legal pack ACTIVE" if "EU" in scopes else ""
        print(f"\nTikTok copy lint — market: {a.market} · vertical: {a.vertical}"
              + (f" · field: {a.field}" if a.field else "") + eu)
        print(f"{counts['BLOCK']} block · {counts['REVIEW']} review · {counts['NOTE']} note\n")
        if not findings:
            print("  No flagged patterns. Still check claims against claims-and-copy.md —")
            print("  the linter catches known phrasings, not every policy problem.\n")
        for f in findings:
            print(f"  [{f['severity']}] {f['id']}: \"{f['matched']}\"")
            print(f"      context: {f['context']}")
            print(f"      policy:  {f['policy']}")
            print(f"      fix:     {f['fix']}\n")
        print("  Spelling and grammar are an enumerated rejection reason — proofread separately.")
        for n in notes:
            print(f"\n  [market] {n}")
        if "EU" in scopes:
            print("\n  EU findings are matters of LAW, not TikTok policy — passing ad review does not")
            print("  resolve them. See references/eu-law.md. Not legal advice.")
        print()

    return 1 if any(f["severity"] == "BLOCK" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
