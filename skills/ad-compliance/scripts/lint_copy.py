#!/usr/bin/env python3
"""Lint TikTok ad copy against the claim patterns that get ads rejected or make them unlawful.

This flags language for a human decision — it does not adjudicate. Some flags are
fine in context (a substantiated comparison, a disclosed risk warning). Every flag
needs a deliberate call, though, because review treats these categories strictly.

--market and --vertical are required and have no defaults: which rules apply depends
on both, and a guessed market or category produces a confident wrong answer. Ask the
user, then pass exactly what they confirmed.

Rule packs cover English, German and French copy. Copy in another language is
reported as unchecked rather than passed.

Usage:
    lint_copy.py --text "Lose 10lbs in 2 weeks, guaranteed!" --market US --vertical weight
    lint_copy.py --file script.txt --market DE,AT --vertical supplements,beauty
    lint_copy.py --file caption.txt --market FR --vertical other --creator --aigc --json
    lint_copy.py --text "Glow Serum" --market GB --vertical beauty --field brand_name
"""

import argparse
import json
import re
import sys
import unicodedata

# severity: BLOCK  = very likely rejected or unlawful as written
#           REVIEW = needs justification, substantiation, or a disclaimer
#           NOTE   = spec/limit/hygiene issue

ORDER = {"BLOCK": 0, "REVIEW": 1, "NOTE": 2}

VERTICALS = {
    "health": "OTC medicines, medical devices, clinics, health services",
    "pharmacy": "pharmacies and online pharmacies",
    "supplements": "food supplements and vitamins",
    "weight": "weight-management products, programmes and services",
    "cosmetic-procedures": "cosmetic surgery and aesthetic treatments",
    "beauty": "cosmetics, skincare, haircare, personal care",
    "food": "food and non-alcoholic drink, including baby food",
    "alcohol": "alcoholic drinks and alcohol-related venues",
    "finance": "banking, lending, investing, trading, insurance, payments",
    "crypto": "cryptocurrency, tokens, crypto services and mining devices",
    "gambling": "real-money gambling, betting, online casinos, lotteries",
    "prediction-markets": "prediction markets and event contracts",
    "gaming": "video and mobile games, social casino, rewarded games",
    "dating": "dating and live-chat apps",
    "other": "none of the above (apparel, tech, travel, services, ...)",
}

# Up to three words between a verb and its object ("treats the worst acne").
W = r"(?:[\w'’-]+\s+){0,3}?"

MED_COND_EN = (r"(?:acne|eczema|psoriasis|rosacea|dermatitis|pain|aches?|migraines?|headaches?|"
               r"arthritis|anxiety|depression|insomnia|infections?|inflammation|diseases?|"
               r"illness(?:es)?|symptoms?|allerg(?:y|ies)|colds?|flu|hair loss|alopecia|hypertension|"
               r"blood pressure|cholesterol|ibs|bloating|constipation|adhd|asthma|fungus|thrush)\b")
MED_COND_DE = (r"(?:akne|ekzem\w*|neurodermitis|schuppenflechte|psoriasis|rosazea|\w*schmerz\w*|"
               r"migräne|arthrose|arthritis|angstzuständ\w*|ängste|depression\w*|schlafstörung\w*|"
               r"schlaflosigkeit|infektion\w*|entzündung\w*|krankheit\w*|erkrankung\w*|symptom\w*|"
               r"allergie\w*|erkältung\w*|grippe|haarausfall|bluthochdruck|cholesterin\w*|blähungen|"
               r"verstopfung|\w*pilz\w*)\b")
MED_COND_FR = (r"(?:[ldj]['’])?(?:acné|eczéma|psoriasis|rosacée|dermatite|douleurs?|migraines?|"
               r"maux de (?:tête|dos|ventre)|arthrose|arthrite|anxiété|angoisses?|dépression|insomnies?|"
               r"infections?|inflammations?|maladies?|symptômes?|allergies?|rhumes?|grippe|"
               r"chute de(?:s)? cheveux|alopécie|hypertension|cholestérol|ballonnements|constipation|"
               r"mycoses?)\b")

# Words that turn "in 2 days" from a promised result into a delivery or prep time.
LOGISTICS_BEFORE = (r"\b(?:deliver\w*|ship\w*|arriv\w*|dispatch\w*|ready|cooked|returns?|refund\w*|"
                    r"reply|respond\w*|install\w*|set ?up|liefer\w*|geliefert|versand\w*|versendet|"
                    r"verschickt|zugestellt|bereit|fertig|zubereitet|livr\w*|expédi\w*|prêt\w*|"
                    r"reçu\w*|rembours\w*)\W+(?:[\w'’-]+\W+){0,3}$")

RULES = [
    # --- Absolute superiority -------------------------------------------------
    dict(id="superlative-absolute", severity="BLOCK",
         en=r"(?:#\s?1\b|\bno\.?\s?1\b|\bnumber one\b|"
            r"\bworld'?s (?:best|leading|number one|#\s?1)\b|"
            r"\bthe (?:best|greatest)\b|\bunmatched\b|\bunbeatable\b|"
            r"\bunrivall?ed\b|\bsecond to none\b)",
         de=r"(?:\bnr\.?\s?1\b|\bnummer (?:eins|1)\b|\bwelt(?:weit)?beste[nrs]?\b|"
            r"\b(?:das|der|die) beste\b|\bunschlagbar\w*|\bunübertroffen\w*|\bkonkurrenzlos\w*)",
         fr=r"(?:\bn°\s?1\b|\bnuméro (?:un|1)\b|\b(?:le meilleur|la meilleure|les meilleur(?:e)?s)\b|"
            r"\bmeilleur(?:e)? au monde\b|\bimbattable\w*|\binégalé\w*|\bsans égal\b)",
         policy="Misleading and false content — absolute superiority claims",
         fix="Replace with a specific, evidenced fact (review counts, a named test result, a dated award)."),
    dict(id="superlative-soft", severity="REVIEW",
         en=r"(?:\b(?:most effective|most powerful|top[- ]rated|award[- ]winning|revolutionary|"
            r"game[- ]chang(?:er|ing)|perfect|the only \w+ that|"
            r"(?:\w+ ){0,2}ever made|like no other)\b|(?<!the )\bbest\b)",
         de=r"(?:\b(?:am wirksamsten|wirksamste\w*|stärkste\w*|bestbewertet\w*|preisgekrönt\w*|"
            r"revolutionär\w*|perfekte?[nrs]?|einzigartig\w*|wie kein anderer)\b|"
            r"(?<!das )(?<!der )(?<!die )\bbeste[nrs]?\b)",
         fr=r"(?:\b(?:l[ea]s? plus efficaces?|révolutionnaire\w*|parfait(?:e|s|es)?|unique en son genre|"
            r"primé(?:e|s|es)?|comme aucun autre)\b|(?<!le )(?<!la )(?<!les )\bmeilleur(?:e|s|es)?\b)",
         policy="Misleading and false content — exaggerated claims",
         fix="Substantiate or soften. 'Award-winning' needs the named award on the landing page."),

    # --- Guarantees and promised outcomes ------------------------------------
    dict(id="guarantee", severity="BLOCK",
         en=r"\b(?:guarantee[ds]?|guaranteed results|100%\s*(?:effective|guaranteed|results|works)|"
            r"risk[- ]free|no[- ]risk|fool[- ]?proof|works for everyone|never fails)\b",
         de=r"\b(?:garantiert\w*|ergebnisgarantie|erfolgsgarantie|100\s*%\s*(?:wirksam|garantiert)|"
            r"risikofrei\w*|ohne risiko|wirkt bei (?:jedem|allen))\b",
         fr=r"\b(?:garanti(?:e|s|es)?|résultats garantis|100\s*%\s*(?:efficace|garanti\w*)|sans risque|"
            r"zéro risque|infaillible|marche pour tout le monde)\b",
         soften_near=r"money[- ]back|refund|returns?\b|deliver|shipping|satisfaction|geld[- ]zurück|"
                     r"rückgabe|liefer|versand|zufriedenheit|rembours|satisfait|livraison|retour",
         hard_near=r"result|ergebnis|résultat|works|wirkt|efficace",
         soften_fix="A money-back, returns or delivery guarantee is a different, allowable statement. "
                    "Keep it only if that is what it is, and match the terms on the landing page.",
         policy="Misleading and false content — promised results",
         fix="Drop the guarantee. A money-back returns policy is a different, allowable statement."),
    dict(id="instant-results", severity="BLOCK",
         en=r"\b(?:instant(?:ly|aneous)?|right away|overnight|in (?:just )?(?:\d+|a few|one|two|three)\s*"
            r"(?:seconds?|minutes?|hours?|days?|weeks?)|immediate results?|see results (?:fast|in)|"
            r"within (?:days?|hours?))\b",
         de=r"\b(?:sofort (?:sichtbar\w*|wirksam\w*)|sofortige?[nr]? (?:ergebnis\w*|wirkung)|über nacht|"
            r"in (?:nur )?(?:\d+|wenigen|einem|einer|zwei|drei)\s*(?:sekunden|minuten|stunden|tagen?|wochen?)|"
            r"innerhalb (?:von )?(?:\d+ )?(?:tagen|stunden))\b",
         fr=r"\b(?:instantané(?:e|s|es|ment)?|immédiat(?:e|s|es|ement)?|du jour au lendemain|"
            r"en (?:seulement |juste )?(?:\d+|quelques|un|une|deux|trois)\s*(?:secondes?|minutes?|heures?|"
            r"jours?|semaines?)|résultats? (?:visibles? )?dès)\b",
         unless_before=LOGISTICS_BEFORE,
         policy="Misleading and false content — 'must not promise or exaggerate results'",
         fix="Describe the mechanism or usage instead of a timeline to an outcome."),

    # --- Medical and health claims -------------------------------------------
    dict(id="medical-claim", severity="BLOCK",
         en=r"\b(?:(?:cure[sd]?|curing|heal(?:s|ed|ing)?|remed(?:y|ies)|miracles?|medically proven|"
            r"doctor[- ]recommended|clinically proven to (?:cure|treat|heal))\b"
            r"(?!\s+(?:meats?|ham|bacon|salmon|sausages?|pork|beef|fish)\b)|"
            r"(?:treat(?:s|ed|ing)?|prevent(?:s|ed|ing)?|revers(?:e|es|ed|ing)|reliev(?:e|es|ed|ing)|"
            r"eliminat(?:e|es|ed|ing)|fights?|stops?|ends?)\s+" + W + MED_COND_EN + ")",
         de=r"\b(?:(?:heil(?:t|en|ung|mittel)|geheilt|kuriert|wundermittel|wunderheil\w*|"
            r"medizinisch (?:bewiesen|erwiesen)|ärztlich empfohlen|von ärzten empfohlen|klinisch bewiesen)\b|"
            r"(?:behandel\w*|lindert|lindern|bekämpf\w*|(?:hilft|wirkt) gegen|beugt|vorbeug\w*|beseitigt)\s+"
            + W + MED_COND_DE + ")",
         fr=r"\b(?:(?:guéri(?:t|r|ssent|son)|remèdes?|miracles?|miraculeu(?:x|se)|"
            r"médicalement prouvé(?:e|s|es)?|recommandé(?:e|s|es)? par les médecins|"
            r"cliniquement prouvé(?:e|s|es)?)\b|"
            r"(?:trait(?:e|ent|er)|soign(?:e|ent|er)|prévien(?:t|nent)|prévenir|soulag(?:e|ent|er)|"
            r"combat(?:s|tre|tent)?|élimin(?:e|ent|er)|lutte(?:nt)? contre|agi(?:t|ssent) contre|"
            r"stoppe(?:nt)?)\s+" + W + MED_COND_FR + ")",
         policy="Healthcare — no medicinal claims to treat, cure, heal or prevent any condition",
         fix="Describe ingredients, formulation, or sensory experience. Medical claims need a licence."),
    dict(id="serious-disease", severity="BLOCK",
         en=r"(?:\b(?:cancer|hiv|covid(?:-?19)?|multiple sclerosis|parkinson'?s|alzheimer'?s|diabetes|"
            r"tumou?rs?)\b|(?-i:\bAIDS\b))",
         de=r"(?:\b(?:krebs|multiple sklerose|diabetes|tumor(?:e|en)?)\b|(?-i:\bAids\b))",
         fr=r"\b(?:cancers?|vih|sida|sclérose en plaques|diabète|tumeurs?)\b",
         policy="Healthcare — cannot imply serious diseases are treatable by the product",
         fix="Remove the disease reference entirely unless the advertiser is a licensed medical provider."),
    dict(id="regulatory-namedrop", severity="REVIEW",
         en=r"\b(?:fda[- ]approved|ce[- ]certified|clinically proven|scientifically proven|"
            r"dermatologist[- ](?:tested|approved)|lab[- ]tested)\b",
         de=r"\b(?:klinisch (?:getestet|geprüft|bewiesen)|wissenschaftlich (?:bewiesen|belegt|erwiesen)|"
            r"dermatologisch (?:getestet|bestätigt|geprüft)|von dermatologen (?:getestet|empfohlen)|"
            r"ce[- ]zertifiziert)\b",
         fr=r"\b(?:cliniquement (?:testé|prouvé)\w*|scientifiquement prouvé\w*|"
            r"testé\w* (?:sous contrôle )?dermatologique\w*|dermatologiquement testé\w*)\b",
         policy="Healthcare / misleading content — regulatory claims must be accurate and evidenced",
         fix="Confirm the claim is literally true and documented; 'FDA registered' ≠ 'FDA approved'."),

    # --- Weight and body image -----------------------------------------------
    dict(id="weight-loss-quantified", severity="BLOCK",
         en=r"\b(?:lose|drop|shed|burn|melt(?:s|ing)?(?: away)?)\s+(?:up to\s+)?"
            r"(?:\d+\s*(?:lbs?|pounds?|kgs?|kilos?|inches|sizes?|stone)|weight fast|fat fast|belly fat)\b",
         de=r"\b(?:\d+\s*(?:kg|kilo|pfund|kleidergrößen?)\s+(?:abnehmen|verlieren|weniger|runter)|"
            r"(?:nimm|nehmen sie|abnehmen|verliere|verlieren sie)\s+(?:bis zu\s+)?\d+\s*(?:kg|kilo|pfund)|"
            r"bauchfett\s+(?:weg|verlieren|verbrennen|schmelzen)|schnell abnehmen)\b",
         fr=r"\b(?:perd(?:ez|re|s)\s+(?:jusqu['’]à\s+)?\d+\s*(?:kg|kilos?|tailles?)|"
            r"\d+\s*(?:kg|kilos?)\s+en moins|maigri(?:r|s|ssez) vite|perte de poids rapide|"
            r"fai(?:tes|re|s) fondre (?:la graisse|le ventre|vos kilos))\b",
         policy="Weight management — unrealistic weight loss, product-alone claims",
         fix="Remove the quantity and timeline. Describe the product, not the body outcome."),
    dict(id="body-ideal", severity="BLOCK",
         en=r"\b(?:bikini body|beach body|dream body|perfect body|ideal body|summer body|snatched|"
            r"flat (?:belly|stomach|tummy)|slim(?:mer)? (?:legs|waist|thighs)|skinny|"
            r"get your body back|problem areas)\b",
         de=r"\b(?:bikinifigur|strandfigur|traumfigur|traumkörper|perfekte(?:r|n)? (?:körper|figur)|"
            r"idealfigur|flache(?:r|n)? bauch|schlanke(?:re)? (?:beine|taille|oberschenkel)|"
            r"problemzonen|sommerfigur)\b",
         fr=r"\b(?:corps de rêve|silhouette de rêve|corps parfait|silhouette parfaite|ventre plat|"
            r"jambes fines|taille fine|corps d['’]été|zones? à problèmes?)\b",
         policy="Weight management and body image — no ideal body type, no body shaming",
         fix="Talk about fit, fabric, comfort, or performance rather than body shape."),
    dict(id="body-life-outcome", severity="BLOCK",
         en=r"\b(?:finally (?:feel|love|be)|feel confident (?:again|in your)|"
            r"(?:more|be) (?:desirable|attractive|popular|successful)|"
            r"love (?:your(?:self)?|your body) again|new you|best version of you)\b",
         de=r"\b(?:endlich (?:wohl|selbstbewusst|schön)\w*|(?:mehr|wieder) selbstbewusst\w*|"
            r"begehrenswerter|attraktiver|ein neues ich|die beste version (?:von )?dir)\b",
         fr=r"\b(?:enfin (?:bien dans (?:ta|votre) peau|confiante?|belle?)|plus confiante?|"
            r"plus désirable|plus attirante?|une? nouvel(?:le)? toi|"
            r"la meilleure version de (?:toi|vous)(?:-même)?)\b",
         policy="Body image — cannot link appearance to improved life circumstances or self-image",
         fix="Cut the transformation-of-self framing; describe what the product is and does."),
    dict(id="effortless", severity="BLOCK",
         en=r"\b(?:no diet(?:ing)? (?:or|and) (?:exercise|workouts?)|"
            r"without (?:diet(?:ing)?|exercise|working out)|easy weight loss|"
            r"lose weight (?:easily|effortlessly|while you sleep)|(?:burn fat|slim down) while you sleep|"
            r"effortless weight loss)\b",
         de=r"\b(?:ohne diät|ohne sport|ohne (?:zu )?hungern|im schlaf abnehmen|"
            r"(?:leicht|einfach|mühelos) abnehmen|abnehmen ohne (?:diät|sport|verzicht))\b",
         fr=r"\b(?:sans régime|sans (?:faire de )?sport|maigrir (?:sans effort|en dormant|facilement)|"
            r"perdre du poids (?:sans effort|facilement|en dormant))\b",
         policy="Weight management — no claims the product alone works, or that it is easy/guaranteed",
         fix="Remove. This is one of the most consistently enforced rules in the policy set."),
    dict(id="effortless-generic", severity="REVIEW", verticals=["weight", "supplements", "health"],
         en=r"\b(?:effortless(?:ly)?|no effort)\b",
         de=r"\b(?:mühelos\w*|ohne anstrengung)\b",
         fr=r"\bsans effort\b",
         policy="Weight management — suggesting results are easy is prohibited for weight and body outcomes",
         fix="Fine for 'effortless to use'; not for anything implying an effortless body or health outcome."),
    dict(id="before-after", severity="REVIEW",
         severity_by_vertical={"health": "BLOCK", "supplements": "BLOCK", "weight": "BLOCK",
                               "cosmetic-procedures": "BLOCK"},
         en=r"\b(?:before (?:and|&|/|\s*-\s*)\s*after|before/after|b&a|my transformation|"
            r"\d+\s*(?:days?|weeks?|months?) (?:transformation|progress|results))\b",
         de=r"\b(?:vorher[- /]+nachher|vorher und nachher|meine verwandlung|"
            r"\d+\s*(?:tage|wochen|monate)\s+(?:verwandlung|fortschritt|ergebnis(?:se)?))\b",
         fr=r"\b(?:avant[- /]+après|avant et après|ma transformation|"
            r"\d+\s*(?:jours|semaines|mois)\s+de (?:transformation|progrès|résultats))\b",
         policy="Misleading content — before/after comparisons creating a false impression; prohibited "
                "outright for OTC medicines and supplements, and exaggerated ones for cosmetic procedures",
         fix="Avoid entirely for health, supplement, weight and body products."),

    # --- Financial ------------------------------------------------------------
    dict(id="financial-exaggerated", severity="BLOCK",
         en=r"\b(?:get rich|getting rich|financial freedom|passive income|"
            r"(?:double|triple|10x|100x) your (?:money|investment|income)|"
            r"turn \$?\d+ into|make \$?\d+[kK]?\s*(?:a|per|/)\s*(?:day|week|month)|"
            r"guaranteed returns?|risk[- ]free investment|quit your job|beat the market)\b",
         de=r"\b(?:schnell reich|reich werden|finanzielle freiheit|passives einkommen|"
            r"verdopple (?:dein|ihr) geld|\d+\s*(?:€|euro) (?:am|pro|im) (?:tag|woche|monat)|"
            r"garantierte rendite\w*|risikolose (?:anlage|investition|rendite)|kündige deinen job)\b",
         fr=r"\b(?:devenir riche|deviens riche|s['’]enrichir rapidement|liberté financière|"
            r"revenus? passifs?|double[rz]? (?:votre|ton) argent|gagne[rz]? \d+\s*(?:€|euros?) par "
            r"(?:jour|semaine|mois)|rendements? garantis?|placement sans risque|"
            r"quitte[rz]? (?:ton|votre) (?:travail|job))\b",
         policy="Financial services / deceptive practices — exaggerated financial claims, get-rich-quick",
         fix="Remove. Income and return claims are prohibited even when historically accurate."),
    dict(id="financial-disclosure-missing", severity="REVIEW", verticals=["finance", "crypto"], once=True,
         en=r"\b(?:loan|credit|apr|interest|invest(?:ing|ment)?|trading|crypto|bitcoin|"
            r"portfolio|returns?|shares?|stocks?)\b",
         de=r"\b(?:kredit\w*|darlehen|zins\w*|effektivzins|jahreszins|investier\w*|geldanlage|"
            r"krypto\w*|depot|rendite\w*|aktien?)\b",
         fr=r"\b(?:crédits?|prêts?|taux|taeg|investi(?:r|ssez|ssement)\w*|placement financier|"
            r"rendements?|bourse)\b",
         policy="Financial services — must disclose rates, APR, fees, repayment terms and disclaimers",
         fix="Add the required risk warning / APR / representative example, legible on screen."),

    # --- Manufactured urgency and clickbait -----------------------------------
    dict(id="false-urgency", severity="REVIEW",
         en=r"\b(?:only \d+ (?:left|remaining|spots?|seats?)|last chance|hurry|act now|"
            r"ends (?:today|tonight|in \d+)|limited spots?|almost gone|selling out fast|"
            r"don'?t miss out|final hours?)\b",
         de=r"\b(?:nur noch \d+ (?:stück|verfügbar|übrig|plätze)|letzte chance|beeil dich|"
            r"beeilen sie sich|nur heute|endet (?:heute|heute nacht|in \d+)|fast ausverkauft|"
            r"nicht verpassen|letzte stunden)\b",
         fr=r"\b(?:plus que \d+|il ne reste que \d+|dernière chance|dépêche[- ]toi|dépêchez[- ]vous|"
            r"aujourd['’]hui seulement|seulement aujourd['’]hui|se termine (?:ce soir|aujourd['’]hui|dans \d+)|"
            r"presque épuisé\w*|ne (?:le )?ratez pas|dernières heures)\b",
         policy="Deceptive practices — manufactured urgency is misleading if not literally true",
         fix="Keep only if verifiably true and reflected on the landing page."),
    dict(id="clickbait-interaction", severity="REVIEW",
         en=r"\b(?:don'?t scroll|stop scrolling|tap (?:here|to reveal|the x)|click here|"
            r"you won'?t believe|doctors hate|this one (?:trick|weird))\b",
         de=r"\b(?:nicht (?:weiter)?scrollen|hör auf zu scrollen|hier (?:klicken|tippen)|"
            r"du wirst (?:es )?nicht glauben|dieser eine trick)\b",
         fr=r"\b(?:arrête de scroller|ne scrolle pas|clique[zr]? ici|"
            r"(?:vous n['’]allez|tu ne vas) pas (?:le )?croire|cette astuce)\b",
         policy="Deceptive practices — clickbait; interactive elements must function as intended",
         fix="Write a hook that states the value instead of withholding it."),

    # --- TikTok brand ---------------------------------------------------------
    dict(id="tiktok-brand", severity="BLOCK",
         en=r"\b(?:tiktok\s*(?:bestseller|famous|made me buy|shop)|as seen on tiktok|"
            r"viral on tiktok|tiktok'?s? (?:favou?rite|#\s?1)|bytedance)\b",
         de=r"\b(?:bekannt (?:aus|von) tiktok|viral auf tiktok|tiktok hat mich)\b",
         fr=r"\b(?:vu sur tiktok|viral sur tiktok|tiktok m['’]a fait acheter)\b",
         policy="IP / format — no TikTok branding or implied TikTok endorsement in ad content",
         fix="Remove all TikTok references from creative and landing page."),

    # --- Adult / suggestive ---------------------------------------------------
    dict(id="adult-explicit", severity="BLOCK",
         en=r"\b(?:nsfw|xxx|porn\w*|horny|one night stand|casual sex|sugar (?:daddy|mommy|baby|dating)|"
            r"cam ?girls?|escorts?|nudes)\b",
         de=r"\b(?:porno\w*|seitensprung\w*|sexdate\w*|sextreff\w*|nacktbilder)\b",
         fr=r"\b(?:porno\w*|plans? culs?|rencontres? d['’]un soir|aventure extraconjugale)\b",
         policy="Adult content — sexually explicit text, casual-sex dating and infidelity are prohibited",
         fix="Remove. Dating apps framed around casual sex cannot be advertised at all."),
    dict(id="adult-suggestive", severity="REVIEW",
         en=r"\b(?:nude|naked|sexy|seductive|sensual|hook ?ups?)\b",
         de=r"\b(?:nackt\w*|verführerisch\w*|geil\w*)\b",
         fr=r"\b(?:nue?s?|séduisant\w*|sensuel\w*|coquin\w*)\b",
         policy="Adult content — sexually suggestive text and innuendo are prohibited",
         fix="Fine as a colour or product name ('nude lipstick', 'naked cake'); not as innuendo."),

    # --- Prohibited products flagged from copy --------------------------------
    dict(id="prohibited-product", severity="BLOCK",
         en=r"\b(?:vape[sr]?|vaping|e-?cig(?:arette)?s?|nicotine|tobacco|cigarettes?|"
            r"payday loans?|bail bonds?|credit repair|pyramid (?:scheme|selling)|mlm|"
            r"kratom|delta[- ]?8|thc)\b",
         de=r"\b(?:e-?zigarette\w*|zigarette\w*|tabak\w*|nikotin\w*|schneeballsystem\w*)\b",
         fr=r"\b(?:vapoteuse\w*|cigarettes?|e-?cigarettes?|cigarette électronique|tabac|chicha|"
            r"système pyramidal|vente pyramidale)\b",
         soften_near=r"nicotine[- ]free|tobacco[- ]free|smoke[- ]free|quit(?:ting)? smoking|"
                     r"stop(?:ping)? smoking|smoking cessation|anti[- ]smoking|rauchfrei|rauchstopp|"
                     r"nichtraucher|mit dem rauchen aufhören|nikotinfrei|arrêter de fumer|arrêt du tabac|"
                     r"sevrage tabagique|sans nicotine|anti[- ]tabac",
         soften_fix="Cessation context detected. Anti-smoking campaigns and non-pharmaceutical cessation "
                    "products are allowed; nicotine-containing products are not, and nicotine replacement "
                    "therapy is a medicine under the healthcare rules. Confirm which this is.",
         policy="Dangerous products / financial services — globally prohibited categories",
         fix="This product category cannot be advertised on TikTok. Check restricted-verticals.md."),
    dict(id="crypto", severity="REVIEW",
         en=r"\b(?:crypto(?:currency)?|bitcoin|btc|ethereum|nfts?|web3|token sale|ico|defi|airdrop)\b",
         de=r"\b(?:krypto\w*)\b",
         fr=r"\b(?:cryptomonnaies?|crypto-?actifs?)\b",
         policy="Financial services — virtual currencies broadly restricted, market-specific approval needed",
         fix="Treat as prohibited unless the market and licensing are confirmed with a TikTok rep."),
    dict(id="real-money-gaming", severity="REVIEW",
         en=r"\b(?:win real (?:money|cash)|real[- ]money (?:games?|prizes?)|cash prizes?|"
            r"earn (?:real )?money (?:by )?playing|withdraw (?:your )?winnings|play (?:to|and) earn)\b",
         de=r"\b(?:echtgeld\w*|um echtes geld|bargeld gewinnen|geld verdienen mit spielen|"
            r"gewinne auszahlen)\b",
         fr=r"\b(?:argent réel|gagne[rz]? de l['’]argent en jouant|retire[rz]? (?:tes|vos) gains)\b",
         policy="Gambling and games — real-money and rewarded mechanics are gambling or rewarded gaming, "
                "which need TikTok approval and are allowed only in specific markets",
         fix="Confirm the product is licensed and TikTok-approved for this market, or remove the claim."),

    # --- Minors ---------------------------------------------------------------
    dict(id="teen-pressure", severity="BLOCK",
         en=r"\b(?:ask your (?:mom|dad|parents?|mum)|tell your parents|beg your parents|"
            r"get your parents to buy)\b",
         de=r"\b(?:frag deine (?:eltern|mama|mutter|papa|vater)|sag deinen eltern|überrede deine eltern)\b",
         fr=r"\b(?:demande à tes parents|dis à tes parents|convaincs tes parents)\b",
         policy="Teen safety — no encouraging teens to persuade parents or guardians to purchase",
         fix="Remove; address the purchasing adult directly."),

    # =========================================================================
    # EU / EEA legal layer. These are matters of law, not TikTok policy — an ad
    # can pass TikTok review and still be unlawful. See references/eu-law.md.
    # =========================================================================

    dict(id="eu-green-generic", severity="BLOCK", markets=["EU"],
         en=r"\b(?:eco[- ]?friendly|environmentally friendly|climate[- ]friendly|planet[- ]friendly|"
            r"kind to (?:nature|the planet)|gentle on the environment|green product|"
            r"eco[- ]conscious|earth[- ]friendly)\b",
         de=r"\b(?:umweltfreundlich\w*|klimafreundlich\w*|umweltschonend\w*|naturfreundlich\w*|"
            r"planetenfreundlich\w*|gut für (?:die umwelt|den planeten|das klima)|"
            r"ökologisch(?:e|er|es|en|em)?\b(?!\s+(?:landbau|anbau|landwirtschaft|erzeugung)))",
         fr=r"\b(?:écologiques?|éco-?responsables?|respectueu(?:x|se|ses) de (?:l['’]environnement|la planète)|"
            r"bon(?:ne)? pour (?:la planète|l['’]environnement)|ami(?:e)? de la planète|produit vert)\b",
         policy="Directive (EU) 2024/825 (from 27 Sep 2026) — generic environmental claims are "
                "blacklisted under UCPD Annex I unless backed by recognised excellent performance",
         fix="Replace with the specific verified fact ('carton is 80% recycled fibre, FSC-certified') "
             "or hold an EU Ecolabel."),
    dict(id="eu-green-offset", severity="BLOCK", markets=["EU"],
         en=r"\b(?:carbon[- ]neutral|climate[- ]neutral|co2[- ]neutral|net[- ]zero|carbon[- ]negative|"
            r"climate[- ]positive|carbon[- ]offset|co2[- ]compensated|offset your carbon)\b",
         de=r"\b(?:klimaneutral\w*|co[2₂]-?neutral\w*|treibhausgasneutral\w*|netto[- ]null|klimapositiv\w*|"
            r"co[2₂]-?kompensiert\w*|klimakompensiert\w*)",
         fr=r"\b(?:neutres? en carbone|neutralité carbone|climatiquement neutres?|zéro émission nette|"
            r"zéro carbone|carbone négatif|compens(?:é|ée|és|ées|ation) carbone|émissions compensées)\b",
         policy="Directive (EU) 2024/825 — carbon/climate-neutrality claims based on offsetting are "
                "blacklisted outright",
         fix="Remove. Offset-based neutrality claims cannot be made to EU consumers at all."),
    dict(id="eu-green-future", severity="REVIEW", markets=["EU"],
         en=r"\b(?:will be|aiming to be|committed to (?:being|becoming)|on track to be)\s+"
            r"(?:\w+\s+){0,3}(?:carbon[- ]neutral|climate[- ]neutral|net[- ]zero|sustainable|"
            r"fully recycl\w+)|\b(?:carbon[- ]neutral|net[- ]zero)\s+by\s+\d{4}\b",
         de=r"\b(?:bis|ab) 20\d\d\s+(?:\w+\s+){0,2}?(?:klimaneutral|co[2₂]-?neutral|netto[- ]null|"
            r"nachhaltig|vollständig recycel\w*)|\b(?:klimaneutral|co[2₂]-?neutral|netto[- ]null)\s+"
            r"(?:bis|ab)\s+20\d\d\b",
         fr=r"\b(?:neutres? en carbone|neutralité carbone|zéro émission nette|zéro carbone)\s+"
            r"(?:d['’]ici|en|avant)\s+20\d\d\b",
         policy="Directive (EU) 2024/825 — future environmental performance claims need clear, "
                "verifiable, time-bound commitments and an independently verified implementation plan",
         fix="Drop it, or cite the published, independently verified plan."),
    dict(id="eu-green-soft", severity="REVIEW", markets=["EU"],
         en=r"\b(?:sustainable|sustainably|responsibly sourced|ethically (?:made|sourced)|"
            r"biodegradable|compostable|all[- ]natural|100% natural|chemical[- ]free|"
            r"plastic[- ]free|zero waste)\b",
         de=r"\b(?:nachhaltig\w*|verantwortungsvoll (?:hergestellt|beschafft|produziert)|"
            r"fair (?:hergestellt|produziert)|biologisch abbaubar\w*|kompostierbar\w*|100\s*% natürlich|"
            r"rein natürlich|chemiefrei|ohne chemie|plastikfrei)\b",
         fr=r"\b(?:(?:mode|produit|emballage|matériau|consommation) durables?|durablement|écoconçu\w*|"
            r"(?:approvisionnement|sourcing) responsable|biodégradables?|compostables?|"
            r"100\s*% naturel(?:le)?s?|sans produits? chimiques?|sans plastique|zéro déchet)\b",
         policy="Directive (EU) 2024/825 / UCPD — vague or unsubstantiated sustainability claims, and "
                "claims about one aspect presented as covering the whole product",
         fix="Substantiate against a certification scheme, scope the claim to the exact attribute, "
             "or remove."),

    dict(id="eu-price-reduction", severity="REVIEW", markets=["EU"],
         en=r"(?:\d+\s*%\s*(?:off|reduction|discount)|\bsave\s*[€£$]?\d+|"
            r"\b(?:was|rrp|reduced from|instead of)\s*[€£$]?\d+|[€£$]\d+\s*(?:→|->|to)\s*[€£$]?\d+|"
            r"\b(?:sale|black friday|cyber monday|mid[- ]season sale|clearance|"
            r"lowest price ever|biggest discount|best deal)\b)",
         de=r"(?:\d+\s*%\s*(?:rabatt|reduziert|günstiger|sparen|nachlass)|[-−–]\s?\d+\s*%|"
            r"\bspare?n?\s*\d+\s*(?:€|euro)|\b(?:statt|uvp|vorher|ehemals|ursprünglich)\s*:?\s*\d+|"
            r"\b(?:sonderangebot|schlussverkauf|ausverkauf|tiefstpreis\w*|bestpreis\w*|"
            r"niedrigster preis\w*|preiskracher|reduziert)\b)",
         fr=r"(?:[-−–]\s?\d+\s*%|\d+\s*%\s*de (?:réduction|remise|rabais)|\bremise de \d+|"
            r"\bau lieu de\s*\d+|\bprix barrés?|\béconomise[zr]?\s*\d+|"
            r"\b(?:soldes|promo(?:tion)?s?|prix le plus bas|meilleur prix|prix cassés?|déstockage)\b)",
         policy="Price Indication Directive Art. 6a (Omnibus) — a price-reduction announcement must "
                "reference the LOWEST price applied in the 30 days before the reduction, not RRP",
         fix="Have the advertiser confirm the 30-day low BEFORE this is rendered — the number is "
             "baked into the video and expensive to change afterwards."),

    dict(id="eu-health-claim", severity="BLOCK", markets=["EU"],
         en=r"\b(?:boosts? (?:your )?(?:immunity|immune system|metabolism)|immune[- ]boosting|"
            r"detox(?:es|ify|ifying|ification)?|cleanses? your (?:body|system|gut)|"
            r"burns? fat|fat[- ]burning|speeds? up (?:your )?metabolism|"
            r"strengthens? (?:your )?immune)\b",
         de=r"\b(?:stärkt (?:dein|ihr|das) immunsystem|stärkung (?:des|deines|ihres) immunsystems|"
            r"immunbooster|immun-?boost\w*|stärkt die abwehr\w*|abwehrkräfte stärken|entgift\w*|"
            r"entschlack\w*|fettverbrenn\w*|verbrennt fett|kurbelt (?:den|deinen|ihren) stoffwechsel an|"
            r"stoffwechsel ankurbeln|reinigt (?:deinen|ihren|den) (?:körper|darm))\b",
         fr=r"\b(?:booste[rz]? (?:votre |ton |vos |tes |l['’])?(?:immunité|système immunitaire|"
            r"défenses immunitaires|métabolisme)|renforce[rz]? (?:votre |ton |vos |tes |les |l['’])?"
            r"(?:immunité|système immunitaire|défenses(?: immunitaires)?)|détox\w*|détoxi\w*|"
            r"brûle[- ]graisses?|brûle les graisses|brûleur de graisse|"
            r"accélère[rz]? (?:votre |ton |le )?métabolisme|"
            r"nettoie[rz]? (?:votre |ton |l['’])?(?:organisme|corps|intestin))\b",
         policy="Reg. (EC) 1924/2006 — only claims on the EU Register of authorised health claims may "
                "be used, in the authorised wording; 'detox' and 'immune boosting' are not authorised",
         fix="Use the authorised wording, e.g. 'Vitamin C contributes to the normal function of the "
             "immune system', and only if the product meets the conditions of use."),
    dict(id="eu-weight-rate-food", severity="BLOCK", markets=["EU"],
         verticals=["health", "supplements", "weight", "food"],
         en=r"\b(?:lose \d+|\d+\s*(?:kg|lbs?|pounds?) (?:in|per|a) (?:\d+\s+)?(?:weeks?|months?|days?)|"
            r"rapid weight loss|fast weight loss)\b",
         de=r"\b(?:\d+\s*(?:kg|kilo|pfund) (?:in|pro|im|je) (?:\d+\s+)?(?:wochen?|monat(?:en)?|tag(?:en)?)|"
            r"schnell abnehmen|rasche gewichtsabnahme|schnelle(?:r|n)? gewichtsverlust)\b",
         fr=r"\b(?:perdez \d+|\d+\s*(?:kg|kilos?) (?:en|par) (?:\d+\s+)?(?:semaines?|mois|jours?)|"
            r"perte de poids rapide|maigrir vite)\b",
         policy="Reg. (EC) 1924/2006 — claims referring to the RATE or AMOUNT of weight loss are "
                "prohibited outright for foods and food supplements",
         fix="Remove any rate or amount of weight loss. This is an absolute prohibition, not a "
             "substantiation question."),
    dict(id="eu-cosmetics-claim", severity="REVIEW", markets=["EU"],
         en=r"\b(?:free[- ]from|paraben[- ]free|sulphate[- ]free|sulfate[- ]free|silicone[- ]free|"
            r"hypoallergenic|non[- ]comedogenic|dermatologically (?:tested|proven))\b",
         de=r"\b(?:frei von|ohne parabene|parabenfrei|sulfatfrei|silikonfrei|hypoallergen\w*|"
            r"nicht komedogen\w*|dermatologisch (?:getestet|bestätigt|geprüft))\b",
         fr=r"\b(?:sans (?:parabènes?|sulfates?|silicones?|perturbateurs? endocriniens?)|"
            r"hypoallergéniques?|non comédogènes?|testé\w* (?:sous contrôle )?dermatologique\w*|"
            r"dermatologiquement testé\w*)\b",
         policy="Reg. (EU) 655/2013 Common Criteria — cosmetic claims must be truthful, evidence-based "
                "and fair; 'free from' claims are restricted where the ingredient was never lawful or "
                "never used in the category",
         fix="Hold the substantiation file, and drop 'free from' claims that denigrate lawful ingredients."),

    dict(id="eu-political", severity="BLOCK", markets=["EU"],
         en=r"\b(?:vote (?:for|against|now)|election|referendum|ballot|political party|"
            r"our campaign for|sign the petition)\b",
         de=r"\b(?:geh(?:t)? wählen|wählen gehen|stimm(?:t|e)? (?:für|gegen)|wahlkampf\w*|wahlaufruf|"
            r"bundestagswahl|landtagswahl|kommunalwahl|europawahl|volksentscheid|volksbegehren|"
            r"unterschreib\w* (?:die|unsere) petition)\b",
         fr=r"\b(?:votez|votons|aux urnes|élections?|référendum|scrutin|parti politique|"
            r"signe[zr]? la pétition)\b",
         policy="TTPA (EU) 2024/900 + TikTok global ban — paid political, electoral and social-issue "
                "advertising is not available on TikTok in the EU",
         fix="This cannot run as a paid ad. Raise it before production, not after."),
]

# Market x vertical gates. These fire on what is being sold and where, whatever the copy
# says. BLOCK gates are findings; PRECONDITION gates list what the advertiser owns.
PREDICTION_MARKETS = {"CA", "US", "PH", "BO", "EC", "GT", "DO", "PY", "CO", "PA", "PE",
                      "GB", "IE", "DK", "FI", "SE", "IL"}

GATES = [
    dict(verticals={"pharmacy"}, markets={"FR", "GR", "JP"}, severity="BLOCK",
         policy="TikTok healthcare policy — pharmacy advertising is prohibited in France, Greece and Japan",
         fix="Cannot run in this market."),
    dict(verticals={"alcohol"}, markets={"NO"}, severity="BLOCK",
         policy="Norway — alcohol advertising is banned outright (Alcohol Act)",
         fix="Cannot run in this market."),
    dict(verticals={"alcohol"}, markets={"LT"}, severity="BLOCK",
         policy="Lithuania — the Law on Alcohol Control bans alcohol advertising in all media, "
                "including online and social media, since 2018",
         fix="Cannot run in this market."),
    dict(verticals={"gambling"}, markets={"IT"}, severity="BLOCK",
         policy="Italy — Decreto Dignità (DL 87/2018, art. 9) bans gambling advertising in all media; "
                "AGCOM's March 2026 guidelines allow only branded responsible-gambling messages",
         fix="Cannot run as a gambling ad. A responsible-gambling message needs Italian legal review."),
    dict(verticals={"gambling"}, markets={"BR"}, severity="BLOCK",
         policy="TikTok (Oct 2026) — all online gambling and gambling-information ads are prohibited in "
                "Brazil. Passive lotteries may be allowed with sales-rep approval (Aug 2026)",
         fix="Cannot run unless this is a licensed passive lottery approved by a TikTok sales rep."),
    dict(verticals={"prediction-markets"}, markets_not=PREDICTION_MARKETS, severity="BLOCK",
         policy="TikTok (July 2026) — prediction markets and event contracts are allowed only in CA, US, "
                "PH, BO, EC, GT, DO, PY, CO, PA, PE, GB, IE, DK, FI, SE and IL",
         fix="Cannot run in this market."),
    dict(verticals={"cosmetic-procedures"}, markets={"FR"}, creator=True, severity="BLOCK",
         policy="France — Loi 2023-451 bans commercial influence promoting cosmetic surgery and "
                "aesthetic procedures",
         fix="Cannot run as creator or influencer content in France."),

    dict(verticals={"health"}, severity="PRECONDITION",
         text="OTC medicines and medical devices need local regulator approval on file (CE/UKCA marking "
              "where relevant) and 18+ targeting. Prescription medicines only in CA, US and NZ (NZ 25+). "
              "No before/after for OTC medicines."),
    dict(verticals={"pharmacy"}, severity="PRECONDITION",
         text="Pharmacy licence certification on file and 18+ targeting."),
    dict(verticals={"supplements"}, severity="PRECONDITION",
         text="Regulatory approval where required and 18+ targeting. No before/after. Some markets require "
              "a health-risk disclosure in the local language. Weight-loss supplements: see weight."),
    dict(verticals={"weight"}, severity="PRECONDITION",
         text="18+ targeting. Weight-loss supplements, meal replacements and weight-loss surgery are "
              "allowed only in the markets listed in restricted-verticals.md (2026 changes), with "
              "sales-rep approval and local licences."),
    dict(verticals={"cosmetic-procedures"}, markets={"US", "CA"}, severity="PRECONDITION",
         text="Allowed since March 2026 with TikTok sales-rep approval, a licensed provider, age targeting, "
              "clear disclosure of medical risks and recovery times, and no exaggerated before/after "
              "imagery or body shaming."),
    dict(verticals={"cosmetic-procedures"}, markets_not={"US", "CA"}, severity="PRECONDITION",
         text="Surgery and invasive procedures (fillers, rhinoplasty) are prohibited in most markets "
              "outside the US and Canada; weight-loss surgery only where listed in restricted-verticals.md. "
              "Non-invasive aesthetic services need regulatory approval, 18+ and sales-rep approval."),
    dict(verticals={"beauty"}, severity="PRECONDITION",
         text="No medical claims (treating, curing or preventing a condition) without a medical licence. "
              "EU: hold a claim-substantiation file under Reg. (EU) 655/2013."),
    dict(verticals={"food"}, severity="PRECONDITION",
         text="EU: only authorised health claims (Reg. (EC) 1924/2006); HFSS limits around children's "
              "content. Infant formula for 0–24 months is prohibited in most markets."),
    dict(verticals={"alcohol"}, severity="PRECONDITION",
         text="Only in markets where TikTok allows alcohol, with licences, sales-rep approval where "
              "required, and age targeting at or above the legal drinking age. Nobody under 25 on camera. "
              "State the ABV and a responsible-drinking message on the ad and landing page. No discounts "
              "or offers that encourage drinking."),
    dict(verticals={"alcohol"}, markets={"FR"}, severity="PRECONDITION",
         text="France — Loi Évin positive list: only expressly permitted content (origin, composition, "
              "ABV, production method) and a health warning."),
    dict(verticals={"finance"}, severity="PRECONDITION",
         text="Licensed by local regulators, 18+ targeting, and legible disclosure of APR, fees, repayment "
              "terms and risk warnings. 2026 carve-outs (CFDs, precious metals, FX, investment advice) "
              "apply only in the markets listed in restricted-verticals.md."),
    dict(verticals={"crypto"}, severity="PRECONDITION",
         text="Treat as prohibited until a TikTok sales rep confirms it for this market. 2026 carve-outs: "
              "digital-currency advisory in GB and IE, crypto-mining devices in US and CA."),
    dict(verticals={"gambling"}, severity="PRECONDITION",
         text="TikTok certification and a local licence, age targeting, nobody underage on camera. "
              "Online casino ads were added in July 2026 for AT, BG, CH, CZ, DE, DK, ES, GR, HR, HU, IE, "
              "IL, LU, NL, PT, RO, SE, SI and SK; national advertising limits still apply."),
    dict(verticals={"gambling"}, markets={"ES"}, severity="PRECONDITION",
         text="Spain — Royal Decree 958/2020 limits gambling advertising timing, content and promotional "
              "offers; get Spanish legal review."),
    dict(verticals={"prediction-markets"}, markets=PREDICTION_MARKETS, severity="PRECONDITION",
         text="Sales-rep approval, age targeting and clear disclaimers."),
    dict(verticals={"gaming"}, severity="PRECONDITION",
         text="Footage must show the real game and its real mechanics. Real-money, rewarded gaming, "
              "social casino and loot boxes fall under the gambling and games rules and need approval."),
    dict(verticals={"dating"}, severity="PRECONDITION",
         text="18+ targeting. No casual-sex or sugar-dating framing. Dating and live-chat apps are not "
              "allowed in every market; confirm this market with a TikTok sales rep."),
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

ISO_COUNTRIES = set("""
AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS
BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE
EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM
HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC
LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA
NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW
SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO
TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS XK YE YT ZA ZM ZW
""".split())
MARKET_ALIASES = {"UK": "GB", "EL": "GR"}

# Country-specific reminders surfaced as notes. Not exhaustive -- a prompt to verify.
MARKET_NOTES = {
    "FR": "Loi Évin: alcohol advertising runs on a POSITIVE LIST — anything not expressly "
          "permitted is prohibited. Pharmacy ads prohibited. Loi Toubon requires French. "
          "Influence law (Loi 2023-451, amended by Ordonnance 2024-978): label creator content "
          "'Publicité' or 'Collaboration commerciale' (or an equivalent, understandable mention), "
          "mark retouched bodies and faces 'Image retouchée' and AI-generated ones 'Image virtuelle', "
          "and no influencer promotion of cosmetic surgery. Brand and creator are jointly liable.",
    "DE": "HWG restricts health-product advertising. UWG lets competitors and trade bodies "
          "issue cease-and-desist warnings (Abmahnung) over ad claims — fast, cheap for them, "
          "expensive for you. Disclosure must read #Werbung or #Anzeige, placed at the start.",
    "IT": "AGCOM influencer code (Delibera 197/25/CONS, binding since 2025) covers creators with "
          "500k+ followers or 1M+ average monthly views, who must register with AGCOM. Gambling "
          "advertising is banned (Decreto Dignità).",
    "SE": "Advertising directed at children under 12 is restricted.",
    "NO": "Advertising directed at children under 12 is restricted; alcohol advertising is "
          "banned outright.",
    "GR": "Pharmacy advertising prohibited; toy advertising restricted on TV.",
    "ES": "Gambling advertising is among the most tightly restricted in the EU "
          "(Royal Decree 958/2020).",
    "LT": "Alcohol advertising is banned in all media, including social media (since 2018).",
}

# Rule packs exist for these languages. Copy in any other language is reported as unchecked.
SUPPORTED_LANGUAGES = {"en": "English", "de": "German", "fr": "French"}

STOPWORDS = {
    "en": "the and you your for with our this that is are of it on get now".split(),
    "de": "der die das und ist nicht mit für dein deine ihr ihre wir unser auf ein eine sie zu den "
          "jetzt dich".split(),
    "fr": "le la les et est pas avec pour votre vos ton ta tes nous notre une des du sur dans "
          "maintenant".split(),
    "es": "el los las y es con para tu tus su nuestro una del por que ahora".split(),
    "it": "il lo gli e è con per tuo tua tuoi nostro una del della che non ora".split(),
    "nl": "het een en is niet met voor jouw je uw ons onze van op dat nu".split(),
    "pt": "o os e é com para seu sua nosso uma do da que não em agora".split(),
    "pl": "i w z na nie się jest do że to dla twój twoja nasz teraz".split(),
    "sv": "och är inte med för din ditt vår att en ett på av som nu".split(),
    "da": "og er ikke med for din dit vores at en et på af som nu".split(),
}
LANGUAGE_NAMES = {"es": "Spanish", "it": "Italian", "nl": "Dutch", "pt": "Portuguese",
                  "pl": "Polish", "sv": "Swedish", "da": "Danish/Norwegian", **SUPPORTED_LANGUAGES}


def parse_markets(value):
    """Turn '--market DE,fr/UK' into {'DE', 'FR', 'GB'}. Rejects anything that isn't a country code."""
    tokens = [t.strip().upper() for t in re.split(r"[,/\s]+", value) if t.strip()]
    markets, bad = set(), []
    for t in tokens:
        t = MARKET_ALIASES.get(t, t)
        if t in ISO_COUNTRIES or t in ("EU", "EEA"):
            markets.add(t)
        else:
            bad.append(t)
    if bad or not markets:
        raise argparse.ArgumentTypeError(
            f"not a market: {', '.join(bad) or repr(value)}. Use ISO country codes (DE, FR, US, GB) "
            "or EU/EEA, comma-separated. 'Europe' or 'global' isn't specific enough: ask the user "
            "which countries.")
    return markets


def parse_verticals(value):
    verticals = {v.strip().lower() for v in value.split(",") if v.strip()}
    bad = sorted(verticals - set(VERTICALS))
    if bad or not verticals:
        raise argparse.ArgumentTypeError(
            f"unknown vertical: {', '.join(bad) or repr(value)}. Choose from: {', '.join(VERTICALS)}")
    return verticals


def market_scopes(markets):
    """Add the 'EU' scope when any EU/EEA market is targeted."""
    scopes = set(markets)
    if markets & (EU_EEA | {"EU", "EEA"}):
        scopes.add("EU")
    return scopes


def detect_language(text):
    """Best-guess language code from stopwords, or None when there is too little text to tell."""
    words = re.findall(r"[^\W\d_]+", text.lower())
    if len(words) < 4:
        return None
    scores = {lang: sum(w in stop for w in words) for lang, stop in STOPWORDS.items()}
    best = max(scores, key=scores.get)
    ranked = sorted(scores.values(), reverse=True)
    if ranked[0] < 2 or ranked[0] == ranked[1]:
        return None
    return best


EMOJI_RE = re.compile(
    "[" "\U0001F000-\U0001FAFF" "\U00002600-\U000027BF" "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF" "\U00002B00-\U00002BFF" "️" "]"
)


def has_emoji(text):
    if EMOJI_RE.search(text):
        return True
    return any(unicodedata.category(ch) == "So" for ch in text)


def context(text, start, end, width=48):
    lo = max(0, start - width // 2)
    hi = min(len(text), end + width // 2)
    snippet = text[lo:hi].replace("\n", " ").strip()
    return ("…" if lo > 0 else "") + snippet + ("…" if hi < len(text) else "")


def finding(id, severity, matched, ctx, policy, fix):
    return dict(id=id, severity=severity, matched=matched, context=ctx, policy=policy, fix=fix)


def match_rules(text, verticals, scopes):
    findings = []
    for rule in RULES:
        if rule.get("verticals") and not (set(rule["verticals"]) & verticals):
            continue
        if rule.get("markets") and not (set(rule["markets"]) & scopes):
            continue
        severity = min([rule["severity"]] + [s for v, s in rule.get("severity_by_vertical", {}).items()
                                             if v in verticals], key=ORDER.get)
        spans = []
        for lang in SUPPORTED_LANGUAGES:
            if lang not in rule or (rule.get("once") and spans):
                continue
            for m in re.finditer(rule[lang], text, re.IGNORECASE):
                if any(m.start() < e and s < m.end() for s, e in spans):
                    continue
                before = text[max(0, m.start() - 40):m.start()]
                if rule.get("unless_before") and re.search(rule["unless_before"], before, re.IGNORECASE):
                    continue
                spans.append((m.start(), m.end()))
                sev, fix = severity, rule["fix"]
                near = (re.search(r"(?:\S+\s+){0,3}\S*$", text[:m.start()]).group(0) + m.group(0)
                        + re.match(r"\S*(?:\s+\S+){0,3}", text[m.end():]).group(0))
                if (rule.get("soften_near") and re.search(rule["soften_near"], near, re.IGNORECASE)
                        and not re.search(rule.get("hard_near", r"(?!)"), near, re.IGNORECASE)):
                    sev, fix = "REVIEW", rule["soften_fix"]
                findings.append(finding(rule["id"], sev, m.group(0), context(text, m.start(), m.end()),
                                        rule["policy"], fix))
                if rule.get("once"):
                    break
    return findings


def check_creator_disclosure(text, scopes):
    """Influencer disclosure duties differ by country; check the ones we know, generically for the rest."""
    lowered = text.lower()
    countries = scopes - {"EU", "EEA"}
    findings = []
    policy = "UCPD + national influencer rules — commercial content must be disclosed clearly and upfront"
    on_screen = ("Put the disclosure ON SCREEN, not only in the caption — captions truncate and the "
                 "label disappears. Gifted product and affiliate links count as commercial relationships.")

    if "DE" in countries:
        m = re.search(r"#?\s?(?:werbung|anzeige)\b", lowered)
        if not m:
            findings.append(finding("eu-creator-disclosure", "BLOCK", "DE: no #Werbung/#Anzeige", text[:60],
                                    policy + ". DE: 'Werbung' or 'Anzeige', placed at the start", on_screen))
        elif m.start() > 60:
            findings.append(finding("eu-creator-disclosure", "REVIEW", f"DE: {m.group(0)}",
                                    context(text, m.start(), m.end()),
                                    policy + ". DE: the label has to come first, not at the end",
                                    "Move 'Werbung' or 'Anzeige' to the start of the caption and on screen."))
        else:
            findings.append(finding("eu-creator-disclosure", "REVIEW", f"DE: {m.group(0)}", text[:60],
                                    policy, on_screen))

    if "FR" in countries:
        named = re.search(r"\b(?:publicité|collaboration commerciale)\b", lowered)
        equivalent = re.search(r"(?:#?sponsoris[ée]|partenariat (?:rémunéré|commercial)|#pub\b|#ad\b|"
                               r"\bsponsored\b|\bpaid partnership\b)", lowered)
        fr_policy = (policy + ". FR: Loi 2023-451 as amended by Ordonnance 2024-978 — 'Publicité' or "
                     "'Collaboration commerciale', or an equivalent mention the audience understands; "
                     "brand and creator jointly liable")
        if named:
            findings.append(finding("eu-creator-disclosure", "REVIEW", f"FR: {named.group(0)}", text[:60],
                                    fr_policy, on_screen))
        elif equivalent:
            findings.append(finding("eu-creator-disclosure", "REVIEW", f"FR: {equivalent.group(0)}", text[:60],
                                    fr_policy, "Equivalent wording is accepted since November 2024 if a "
                                    "French viewer understands it; 'Publicité' or 'Collaboration "
                                    "commerciale' are the safe choice. " + on_screen))
        else:
            findings.append(finding("eu-creator-disclosure", "BLOCK", "FR: no disclosure found", text[:60],
                                    fr_policy, "Add 'Publicité' or 'Collaboration commerciale'. " + on_screen))
        findings.append(finding(
            "fr-image-labels", "REVIEW", "FR creator content", "—",
            "France — Loi 2023-451: images whose body or face was retouched need 'Image retouchée'; "
            "bodies or faces generated by AI need 'Image virtuelle' (or an equivalent mention)",
            "Confirm whether any shot was slimmed, reshaped or AI-generated, and label it on screen."))

    others = (countries & EU_EEA) - {"DE", "FR"}
    if others or not countries & EU_EEA:
        m = re.search(r"(?:#\s?(?:werbung|anzeige|ad|ads|advert|sponsored|sponsoris[ée]|partenariat|pub|"
                      r"publicidad|pubblicità|adv|reklame|reklama|samarbeid|annonse|advertentie)\b|"
                      r"\b(?:paid partnership|bezahlte partnerschaft|publicité|publicidad|pubblicità|"
                      r"collaboration commerciale|advertentie|reklama|reklame)\b)", lowered)
        label = ", ".join(sorted(others)) or "EU"
        findings.append(finding("eu-creator-disclosure", "REVIEW" if m else "BLOCK",
                                f"{label}: {m.group(0)}" if m else f"{label}: no disclosure found", text[:60],
                                policy + ". IT: AGCOM code for creators with 500k+ followers or 1M+ monthly "
                                "views", on_screen))
    return findings


def check_gates(verticals, scopes, creator=False):
    """Market x vertical gates: (blocking findings, preconditions)."""
    countries = scopes - {"EU", "EEA"}
    blocks, preconditions = [], []
    for gate in GATES:
        if not (gate["verticals"] & verticals):
            continue
        if gate.get("creator") and not creator:
            continue
        if "markets" in gate:
            hit = sorted(gate["markets"] & countries)
        elif "markets_not" in gate:
            hit = sorted(countries - gate["markets_not"])
        else:
            hit = ["all"]
        if not hit:
            continue
        label = ", ".join(sorted(gate["verticals"] & verticals))
        if gate["severity"] == "BLOCK":
            blocks.append(finding("market-vertical-gate", "BLOCK", f"{label} in {', '.join(hit)}", "—",
                                  gate["policy"], gate["fix"]))
        else:
            where = "" if hit == ["all"] else f" ({', '.join(hit)})"
            preconditions.append(f"{label}{where}: {gate['text']}")
    return blocks, preconditions


def lint(text, verticals, field=None, aigc=False, scopes=None, creator=False):
    scopes = scopes or set()
    countries = scopes - {"EU", "EEA"}
    findings = match_rules(text, verticals, scopes)

    # Field-level spec checks
    if field and field in FIELD_LIMITS:
        lo, hi, allow_emoji, banned = FIELD_LIMITS[field]
        n = len(text.strip())
        if n < lo or n > hi:
            findings.append(finding(
                "field-length", "NOTE", f"{n} characters", text[:60],
                f"Spec — {field} must be {lo}–{hi} Latin characters",
                f"Adjust to {lo}–{hi} characters (Asian-script limits are roughly half)."))
        if not allow_emoji and has_emoji(text):
            findings.append(finding("field-emoji", "NOTE", "emoji present", text[:60],
                                    f"Spec — emoji are not supported in {field}", "Remove emoji from this field."))
        for ch in banned:
            if ch in text:
                findings.append(finding("field-banned-char", "NOTE", ch, text[:60],
                                        f"Spec — '{ch}' is not supported in {field}", f"Remove '{ch}'."))

    # Cheap hygiene proxies — spelling/grammar errors are an enumerated rejection reason
    for m in re.finditer(r"\b(\w+)\s+\1\b", text, re.IGNORECASE):
        findings.append(finding(
            "doubled-word", "NOTE", m.group(0), context(text, m.start(), m.end()),
            "Ad format — caption and text must be free of spelling and grammatical mistakes",
            "Proofread; duplicated word."))
    if re.search(r"[A-Z]{6,}", text) and field != "brand_name":
        findings.append(finding(
            "shouting", "NOTE", "ALL CAPS run", text[:60],
            "Ad quality — excessive capitalisation reads as low-quality to review",
            "Use sentence case for body copy; reserve caps for short emphasis."))

    # Language coverage — a clean result on copy we can't read is not a pass
    lang = detect_language(text)
    if lang and lang not in SUPPORTED_LANGUAGES:
        findings.append(finding(
            "unsupported-language", "REVIEW", LANGUAGE_NAMES[lang], text[:60],
            "Linter coverage — rule packs exist for English, German and French only",
            f"This copy looks {LANGUAGE_NAMES[lang]}, so most of it was NOT checked. Have a native "
            "speaker review it against references/claims-and-copy.md and references/eu-law.md."))
    if "FR" in countries and lang == "en":
        findings.append(finding(
            "fr-language", "REVIEW", "English copy for FR", text[:60],
            "France — Loi Toubon: advertising must be in French; foreign-language text needs a French "
            "translation that is as legible and audible as the original",
            "Write the French version, and have a native speaker check it — TikTok also rejects "
            "spelling and grammar errors."))

    if aigc:
        disclosed = re.search(r"\b(?:ai[- ]generated|generated (?:with|by) ai|ai[- ]created|"
                              r"created (?:with|using) ai|made with ai|synthetic (?:voice|media|image|video|"
                              r"presenter|content)|aigc|ai voice|ki[- ]generiert\w*|mit ki (?:erstellt|"
                              r"generiert)|durch ki (?:erstellt|generiert)|ki[- ]stimme|künstlich (?:erzeugt|"
                              r"generiert)|généré(?:e|s|es)? par (?:l['’])?ia|créé(?:e|s|es)? (?:avec|par) "
                              r"(?:l['’])?ia|images? virtuelles?|voix (?:de synthèse|générée par (?:l['’])?ia))\b",
                              text, re.IGNORECASE)
        if not disclosed:
            findings.append(finding(
                "aigc-undisclosed", "BLOCK", "(no disclosure found)", "—",
                "Misleading content — AIGC requires the AIGC label or a clear visible disclaimer",
                "Apply the AIGC label in Ads Manager and add a visible on-screen disclosure."))
        if "EU" in scopes:
            findings.append(finding(
                "eu-ai-act-disclosure", "BLOCK" if not disclosed else "REVIEW",
                "AI-generated creative targeting EU", "—",
                "AI Act (EU) 2024/1689 Art. 50 (applies since 2 Aug 2026) — deployers creating "
                "deepfakes must disclose artificial generation; duty applies WITHOUT intent to "
                "deceive, and to non-EU advertisers targeting EU audiences",
                "Disclosure must be clear, distinguishable and given no later than first exposure: "
                "visible on screen for visual content, audible where audio is the relevant mode. "
                "A campaign-level setting is not disclosure. Stricter than TikTok's own AIGC rule."))

    if creator and "EU" in scopes:
        findings.extend(check_creator_disclosure(text, scopes))

    blocks, _ = check_gates(verticals, scopes, creator)
    findings.extend(blocks)

    findings.sort(key=lambda f: ORDER[f["severity"]])
    return findings


def main():
    p = argparse.ArgumentParser(
        description="Lint TikTok ad copy against policy claim patterns and EU advertising law.",
        epilog="--market and --vertical are required. Ask the user which countries the ad will run in "
               "and what is being sold; never guess.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="Copy to lint.")
    src.add_argument("--file", help="File containing the copy (script, caption, VO).")
    p.add_argument("--market", type=parse_markets,
                   help="REQUIRED. Target market(s) as ISO country codes, e.g. US, DE, 'DE,FR', or EU/EEA. "
                        "EU/EEA codes activate the EU legal rule pack.")
    p.add_argument("--vertical", type=parse_verticals,
                   help="REQUIRED. What is being sold; comma-separate if it spans several. One of: "
                        + "; ".join(f"{k} ({v})" for k, v in VERTICALS.items()))
    p.add_argument("--creator", action="store_true",
                   help="Creative is creator/UGC/Spark content — checks influencer disclosure.")
    p.add_argument("--field", choices=sorted(FIELD_LIMITS), help="Apply this field's spec limits.")
    p.add_argument("--aigc", action="store_true", help="Creative uses AI-generated media.")
    p.add_argument("--json", action="store_true", help="Machine-readable output.")
    a = p.parse_args()

    missing = [flag for flag, val in (("--market", a.market), ("--vertical", a.vertical)) if not val]
    if missing:
        p.error(f"{' and '.join(missing)} required. Don't assume: ask the user which countries the ad "
                "will run in and what is being sold, then pass exactly what they confirmed.")

    text = a.text if a.text else open(a.file, encoding="utf-8").read()
    scopes = market_scopes(a.market)
    countries = a.market - {"EU", "EEA"}
    findings = lint(text, a.vertical, field=a.field, aigc=a.aigc, scopes=scopes, creator=a.creator)
    _, preconditions = check_gates(a.vertical, scopes, a.creator)

    notes = [f"{c}: {MARKET_NOTES[c]}" for c in sorted(countries & set(MARKET_NOTES))]
    if a.market & {"EU", "EEA"} and not countries & EU_EEA:
        notes.append("EU/EEA market with no specific country given — national rules differ "
                     "materially (FR, DE, IT, SE, NO, GR, ES, LT each add their own). Narrow it down.")
    no_legal_pack = sorted(countries - EU_EEA)
    if no_legal_pack:
        notes.append(f"No legal rule pack for {', '.join(no_legal_pack)}. Findings for "
                     f"{'this market' if len(no_legal_pack) == 1 else 'these markets'} cover TikTok "
                     "platform policy only, not local advertising law — a clean result is not a legal "
                     "clearance.")

    lang = detect_language(text)
    market_label = ",".join(sorted(a.market))
    vertical_label = ",".join(sorted(a.vertical))
    if a.json:
        print(json.dumps(dict(market=sorted(a.market), scopes=sorted(scopes), vertical=sorted(a.vertical),
                              language=lang, field=a.field, findings=findings,
                              preconditions=preconditions, market_notes=notes), indent=2,
                         ensure_ascii=False))
    else:
        counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ORDER}
        eu = " · EU legal pack ACTIVE" if "EU" in scopes else ""
        lang_label = LANGUAGE_NAMES.get(lang, "undetermined")
        print(f"\nTikTok copy lint — market: {market_label} · vertical: {vertical_label}"
              + (f" · field: {a.field}" if a.field else "") + f" · language: {lang_label}" + eu)
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
        for pre in preconditions:
            print(f"\n  [precondition] {pre}")
        for n in notes:
            print(f"\n  [market] {n}")
        if "EU" in scopes:
            print("\n  EU findings are matters of LAW, not TikTok policy — passing ad review does not")
            print("  resolve them. See references/eu-law.md. Not legal advice.")
        print()

    return 1 if any(f["severity"] == "BLOCK" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
