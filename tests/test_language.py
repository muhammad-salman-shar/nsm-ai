import unittest
from src.language import Language
from src.personality import Personality
from src.affect import Affect


class TestLanguage(unittest.TestCase):
    def setUp(self):
        self.lang = Language(seed=42)
        self.p = Personality

    def test_all_intents_nonempty(self):
        for intent in ["greeting", "identity", "question", "sad", "happy",
                       "farewell", "statement", "unknown"]:
            out = self.lang.generate(intent, self.p)
            self.assertIsInstance(out, str)
            self.assertGreater(len(out), 0, f"{intent} empty")

    def test_unknown_intent_fallback(self):
        out = self.lang.generate("nonexistent_intent", self.p)
        self.assertGreater(len(out), 0)

    def test_context_substitution(self):
        for _ in range(20):
            out = self.lang.generate("identity", self.p)
            for token in ["{name}", "{age}", "{builder}", "{full_name}"]:
                self.assertNotIn(token, out, f"unfilled {token} in: {out}")

    def test_deterministic_seed(self):
        l1 = Language(seed=42)
        l2 = Language(seed=42)
        a = [l1.generate("greeting", self.p) for _ in range(10)]
        b = [l2.generate("greeting", self.p) for _ in range(10)]
        self.assertEqual(a, b)

    def test_mood_bank_diversity(self):
        bank = Language.TEMPLATES["greeting"]
        self.assertIn("happy", bank)
        self.assertIn("neutral", bank)
        self.assertIn("bored", bank)
        self.assertNotEqual(bank["happy"], bank["neutral"])

    def test_mood_affects_selection(self):
        happy = Affect()
        happy.drives["satisfaction"] = 90
        happy.drives["social_reward"] = 90
        happy.hormones["dopamine"] = 80
        happy.hormones["oxytocin"] = 80
        happy.drives["confusion"] = 20

        bored = Affect()
        bored.drives["attention"] = 10
        bored.drives["satisfaction"] = 10
        bored.hormones["dopamine"] = 20

        h_outs = {Language(seed=i).generate("greeting", self.p, affect=happy) for i in range(30)}
        b_outs = {Language(seed=i).generate("greeting", self.p, affect=bored) for i in range(30)}
        self.assertNotEqual(h_outs, b_outs,
                            f"mood had no effect: happy={h_outs} bored={b_outs}")

    def test_affect_none_defaults_neutral(self):
        out = self.lang.generate("greeting", self.p, affect=None)
        self.assertGreater(len(out), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
