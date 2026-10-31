"""Regression tests for scripts/lint_copy.py. Run with: python3 -m unittest discover tests"""

import importlib.util
import pathlib
import subprocess
import sys
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "skills" / "ad-compliance" / "scripts" / "lint_copy.py"
spec = importlib.util.spec_from_file_location("lint_copy", SCRIPT)
lint_copy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint_copy)


def run(text, market, vertical="other", platform="tiktok", **kw):
    scopes = lint_copy.market_scopes(lint_copy.parse_markets(market))
    return lint_copy.lint(text, lint_copy.parse_verticals(vertical), lint_copy.parse_platforms(platform),
                          scopes=scopes, **kw)


def ids(findings, severity=None):
    return {f["id"] for f in findings if severity is None or f["severity"] == severity}


class RequiredScope(unittest.TestCase):
    def cli(self, *args, platform=("--platform", "tiktok")):
        return subprocess.run([sys.executable, str(SCRIPT), "--text", "Hello there", *platform, *args],
                              capture_output=True, text=True)

    def test_market_and_vertical_are_required(self):
        for args in ([], ["--market", "DE"], ["--vertical", "beauty"]):
            r = self.cli(*args)
            self.assertEqual(r.returncode, 2, args)
            self.assertIn("ask the user", r.stderr)

    def test_platform_is_required(self):
        r = self.cli("--market", "DE", "--vertical", "beauty", platform=())
        self.assertEqual(r.returncode, 2)
        self.assertIn("ask the user", r.stderr)

    def test_unknown_platforms_are_rejected(self):
        for platform in ("meta", "facebook", "tiktok,youtube", ""):
            r = self.cli("--market", "DE", "--vertical", "beauty", platform=("--platform", platform))
            self.assertEqual(r.returncode, 2, platform)

    def test_platform_list(self):
        self.assertEqual(lint_copy.parse_platforms("TikTok, other"), {"tiktok", "other"})

    def test_vague_or_unknown_markets_are_rejected(self):
        for market in ("Germany", "Europe", "global"):
            r = self.cli("--market", market, "--vertical", "other")
            self.assertEqual(r.returncode, 2, market)

    def test_unknown_vertical_is_rejected(self):
        self.assertEqual(self.cli("--market", "DE", "--vertical", "banana").returncode, 2)

    def test_aliases(self):
        self.assertEqual(lint_copy.parse_markets("uk, el"), {"GB", "GR"})

    def test_non_eu_market_says_no_legal_pack(self):
        r = self.cli("--market", "US", "--vertical", "other")
        self.assertEqual(r.returncode, 0)
        self.assertIn("No legal rule pack for US", r.stdout)


class Platforms(unittest.TestCase):
    def test_other_runs_the_eu_pack_but_no_tiktok_rules(self):
        text = "The #1 eco-friendly serum, guaranteed. TikTok made me buy it. SHOP NOW NOW"
        found = ids(run(text, "DE", "beauty", platform="other", aigc=True))
        for rule in ("eu-green-generic", "eu-ai-act-disclosure"):
            self.assertIn(rule, found)
        for rule in ("superlative-absolute", "guarantee", "tiktok-brand", "aigc-undisclosed", "doubled-word",
                     "shouting"):
            self.assertNotIn(rule, found)

    def test_other_runs_legal_gates_but_no_tiktok_gates(self):
        for market, vertical in [("IT", "gambling"), ("NO", "alcohol"), ("LT", "alcohol")]:
            self.assertIn("market-vertical-gate", ids(run("Visit us", market, vertical, platform="other")),
                          f"{vertical} in {market}")
        self.assertIn("market-vertical-gate",
                      ids(run("Publicité", "FR", "cosmetic-procedures", platform="other", creator=True)))
        for market, vertical in [("FR", "pharmacy"), ("BR", "gambling"), ("DE", "prediction-markets")]:
            self.assertNotIn("market-vertical-gate", ids(run("Visit us", market, vertical, platform="other")),
                             f"{vertical} in {market}")

    def test_other_shows_only_the_legal_part_of_preconditions(self):
        scopes = lint_copy.market_scopes({"DE"})
        _, pre = lint_copy.check_gates({"food", "health"}, scopes, {"other"})
        self.assertEqual(len(pre), 1)
        self.assertIn("1924/2006", pre[0])
        self.assertNotIn("Infant formula", pre[0])
        _, pre = lint_copy.check_gates({"food"}, scopes, {"tiktok"})
        self.assertIn("Infant formula", pre[0])

    def test_other_says_platform_policy_was_not_checked(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "--text", "Hello there", "--platform", "other",
                            "--market", "US", "--vertical", "other"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Platform policy was NOT checked", r.stdout)

    def test_tiktok_brand_only_fires_for_tiktok(self):
        text = "TikTok made me buy it"
        self.assertIn("tiktok-brand", ids(run(text, "US"), "BLOCK"))
        self.assertNotIn("tiktok-brand", ids(run(text, "US", platform="other")))

    def test_adding_other_leaves_tiktok_results_unchanged(self):
        text = "Our eco-friendly serum is the #1 choice. 30% off, was €49."
        for market in ("US", "DE", "FR"):
            self.assertEqual(run(text, market, "beauty", aigc=True, creator=True),
                             run(text, market, "beauty", platform="tiktok,other", aigc=True, creator=True))


class SkillsOwnRewrites(unittest.TestCase):
    """The rewrite table in references/claims-and-copy.md must agree with the linter."""

    REJECTED = ["Lose 10lbs in 2 weeks, guaranteed", "The #1 skincare brand in the world",
                "Cures your anxiety", "Turn $100 into $10,000", "You'll finally feel confident in your body"]
    COMPLIANT = ["A 300-calorie meal replacement, ready in 60 seconds", "Over 40,000 five-star reviews",
                 "Made with magnesium glycinate and L-theanine", "Commission-free trading. Capital at risk.",
                 "Sizes 6–24, cut for a high waist", "Ships free through Sunday"]

    def test_rejected_examples_block(self):
        for text in self.REJECTED:
            self.assertTrue(ids(run(text, "US"), "BLOCK"), text)

    def test_compliant_rewrites_do_not_block(self):
        for text in self.COMPLIANT:
            self.assertFalse(ids(run(text, "US"), "BLOCK"), text)


class FalsePositives(unittest.TestCase):
    def test_everyday_copy_does_not_block(self):
        for text in ["Treat yourself this weekend", "Delivered in 2 days", "Our hearing aids are rechargeable",
                     "Prevents frizz all day", "Dog treats made with real chicken", "Cured ham from Parma",
                     "Effortless to clean", "Soigne et protège ta peau", "Geliefert in 2 Tagen",
                     "Livré en 48 heures", "Nude lipstick in six shades", "30-day money-back guarantee"]:
            self.assertFalse(ids(run(text, "US"), "BLOCK"), text)

    def test_exceptions_do_not_hide_real_claims(self):
        for text in ["Guaranteed results, free returns", "Results already in 3 days",
                     "Nicotine pouches with free shipping"]:
            self.assertTrue(ids(run(text, "US"), "BLOCK"), text)

    def test_cessation_products_are_review_not_block(self):
        findings = run("Nicotine-free quit-smoking support", "US", "health")
        self.assertFalse(ids(findings, "BLOCK"))
        self.assertIn("prohibited-product", ids(findings, "REVIEW"))


class MedicalClaims(unittest.TestCase):
    def test_conditions_block_in_every_language(self):
        for text in ["Treats acne fast", "Prevents hair loss", "Living with AIDS? Try this",
                     "Hilft gegen Kopfschmerzen", "Lutte contre l'acné", "Guérit les rhumes"]:
            self.assertTrue({"medical-claim", "serious-disease"} & ids(run(text, "US"), "BLOCK"), text)


class EULanguagePacks(unittest.TestCase):
    def test_english_german_french_equivalents(self):
        cases = {
            "DE": "Unser umweltfreundliches Serum ist klimaneutral und stärkt dein Immunsystem. "
                  "30% Rabatt, statt 49 €. Nachhaltig und parabenfrei.",
            "FR": "Notre sérum écologique est neutre en carbone et booste votre immunité. "
                  "-30%, au lieu de 49 €. Sans parabènes.",
            "IE": "Our eco-friendly serum is carbon neutral and boosts your immune system. "
                  "30% off, was €49. Paraben-free.",
        }
        for market, text in cases.items():
            found = ids(run(text, market, "beauty"))
            for rule in ("eu-green-generic", "eu-green-offset", "eu-health-claim", "eu-price-reduction",
                         "eu-cosmetics-claim"):
                self.assertIn(rule, found, f"{market}: {rule}")

    def test_eu_rules_stay_off_outside_eu(self):
        self.assertFalse(ids(run("Eco-friendly and carbon neutral", "US")))

    def test_unsupported_language_is_flagged_not_passed(self):
        text = "Il nostro siero è il migliore per la tua pelle, con la vitamina C che non ti delude"
        self.assertIn("unsupported-language", ids(run(text, "IT", "beauty")))

    def test_english_copy_for_france(self):
        self.assertIn("fr-language", ids(run("Our new cream is here for you and your skin", "FR", "beauty")))


class Verticals(unittest.TestCase):
    def test_weight_rate_claim_fires_for_weight_and_food(self):
        for vertical in ("weight", "supplements", "food", "health"):
            self.assertIn("eu-weight-rate-food", ids(run("Lose 5 kg per month", "FR", vertical)), vertical)
        self.assertNotIn("eu-weight-rate-food", ids(run("Lose 5 kg per month", "FR", "other")))

    def test_before_after_blocks_for_supplements(self):
        self.assertIn("before-after", ids(run("Before and after", "US", "supplements"), "BLOCK"))
        self.assertIn("before-after", ids(run("Before and after", "US", "other"), "REVIEW"))

    def test_market_vertical_bans(self):
        for market, vertical in [("FR", "pharmacy"), ("IT", "gambling"), ("BR", "gambling"),
                                 ("NO", "alcohol"), ("LT", "alcohol"), ("DE", "prediction-markets")]:
            self.assertIn("market-vertical-gate", ids(run("Visit us", market, vertical), "BLOCK"),
                          f"{vertical} in {market}")

    def test_allowed_combinations_do_not_block(self):
        for market, vertical in [("SE", "prediction-markets"), ("DE", "gambling"), ("US", "cosmetic-procedures")]:
            self.assertNotIn("market-vertical-gate", ids(run("Visit us", market, vertical)),
                             f"{vertical} in {market}")

    def test_french_influencers_cannot_promote_cosmetic_procedures(self):
        text = "Collaboration commerciale : ma clinique"
        self.assertIn("market-vertical-gate",
                      ids(run(text, "FR", "cosmetic-procedures", creator=True), "BLOCK"))
        self.assertNotIn("market-vertical-gate", ids(run(text, "FR", "cosmetic-procedures")))

    def test_every_vertical_has_preconditions_or_is_other(self):
        for vertical in lint_copy.VERTICALS:
            _, pre = lint_copy.check_gates({vertical}, lint_copy.market_scopes({"US"}), {"tiktok"})
            self.assertEqual(bool(pre), vertical != "other", vertical)


class CreatorDisclosure(unittest.TestCase):
    def test_french_named_labels_are_accepted(self):
        for text in ("Collaboration commerciale avec Marque X", "Publicité — ma routine"):
            found = run(text, "FR", creator=True)
            self.assertFalse([f for f in found if f["id"] == "eu-creator-disclosure" and f["severity"] == "BLOCK"],
                             text)

    def test_french_equivalent_is_review(self):
        found = run("#sponsorisé ma routine", "FR", creator=True)
        self.assertIn("eu-creator-disclosure", ids(found, "REVIEW"))
        self.assertNotIn("eu-creator-disclosure", ids(found, "BLOCK"))

    def test_german_label_must_come_first(self):
        late = ("Meine liebste Morgenroutine mit dem neuen Serum, ich benutze es seit Wochen jeden Tag "
                "#werbung")
        found = [f for f in run(late, "DE", creator=True) if f["id"] == "eu-creator-disclosure"]
        self.assertEqual(len(found), 1)
        self.assertIn("start", found[0]["fix"])

    def test_missing_disclosure_blocks_per_market(self):
        found = [f for f in run("My favourite routine", "DE,NL", creator=True)
                 if f["id"] == "eu-creator-disclosure"]
        self.assertEqual({f["matched"].split(":")[0] for f in found}, {"DE", "NL"})
        self.assertTrue(all(f["severity"] == "BLOCK" for f in found))


class AIGC(unittest.TestCase):
    def test_disclosure_terms(self):
        self.assertIn("aigc-undisclosed", ids(run("Synthetic leather bag", "US", aigc=True)))
        for text in ("AI-generated presenter", "KI-generiert", "Généré par l'IA", "Image virtuelle"):
            self.assertNotIn("aigc-undisclosed", ids(run(text, "DE", aigc=True)), text)


if __name__ == "__main__":
    unittest.main()
