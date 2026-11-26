"""Unit tests for NSM Sentence-Token Memory Matcher (20% reference / 40%+ direct lift / multi-sentence)."""

import unittest

from src.brain import Brain


class TestSentenceTokenMatcher(unittest.TestCase):
    def setUp(self):
        self.brain = Brain(seed_core=True)
        self.brain.observe_bulk(
            "Overheating causes CPU throttling. "
            "Spaced repetition works by reviewing study material at gradually increasing intervals. "
            "Active recall is used for strengthening long-term memory retrieval before exams."
        )

    def test_direct_lift_above_40_percent(self):
        # 2/3 content words match ("overheating", "throttling" out of "overheating", "laptop", "throttling") -> 66.7% >= 40%
        res = self.brain.observe_bulk("Overheating laptop throttling.")
        self.assertEqual(res["mode"], "stored")
        self.assertIn("overheating causes cpu throttling", res["response"].lower())
        self.assertTrue(any("direct lift" in p.lower() for p in res["proof_steps"]))

    def test_reference_match_between_20_and_39_percent(self):
        # 1/4 content words match ("throttling" out of "heavy", "gaming", "thermal", "throttling") -> 25% (20%-39%)
        res = self.brain.observe_bulk("Heavy gaming thermal throttling.")
        self.assertEqual(res["mode"], "derived")
        self.assertIn("overheating causes cpu throttling", res["response"].lower())
        self.assertTrue(any("reference match" in p.lower() for p in res["proof_steps"]))

    def test_below_20_percent_returns_unknown(self):
        # 0% match -> unknown
        res = self.brain.observe_bulk("Quantum entanglement photonic crystals.")
        self.assertEqual(res["mode"], "unknown")

    def test_multi_sentence_one_by_one_filtering(self):
        # 3 sentences separated by full stops: 1st matches, 2nd is unrelated (<20%), 3rd matches
        query = (
            "Tell me about spaced repetition intervals. "
            "Quantum gravity black hole radiation. "
            "Active recall before exams."
        )
        res = self.brain.observe_bulk(query)
        self.assertIn(res["mode"], {"stored", "derived"})
        low = res["response"].lower()
        self.assertIn("spaced repetition works by", low)
        self.assertIn("active recall is used for", low)
        self.assertNotIn("quantum gravity", low)


if __name__ == "__main__":
    unittest.main()
