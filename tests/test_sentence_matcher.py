"""Unit tests for NSM Sentence-Token Matcher, Comma Clause Handling, and General Facts."""

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
        res = self.brain.observe_bulk("Overheating laptop throttling.")
        self.assertEqual(res["mode"], "stored")
        self.assertIn("overheating causes cpu throttling", res["response"].lower())
        self.assertTrue(any("direct lift" in p.lower() for p in res["proof_steps"]))

    def test_reference_match_between_20_and_39_percent(self):
        res = self.brain.observe_bulk("Heavy gaming thermal throttling.")
        self.assertEqual(res["mode"], "derived")
        self.assertIn("overheating causes cpu throttling", res["response"].lower())
        self.assertTrue(any("reference match" in p.lower() for p in res["proof_steps"]))

    def test_below_20_percent_returns_unknown(self):
        res = self.brain.observe_bulk("Quantum entanglement photonic crystals.")
        self.assertEqual(res["mode"], "unknown")

    def test_multi_sentence_one_by_one_filtering(self):
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

    def test_comma_lists_vs_comma_compound_clauses(self):
        # 1. Comma list inside one sentence must stay intact
        r_list = self.brain.observe_bulk("Plants need water, air, and sunlight to grow.")
        self.assertEqual(r_list["mode"], "stored")
        self.assertEqual(len(r_list["learned"]), 1)

        # 2. Compound comma-separated clauses must split into two separate learned facts
        r_comp = self.brain.observe_bulk("Python is a programming language, SQLite is an embedded database.")
        self.assertEqual(r_comp["mode"], "stored")
        self.assertEqual(len(r_comp["learned"]), 2)

        # 3. Comma-separated questions must answer both
        r_q = self.brain.observe_bulk("What is Python, what is SQLite?")
        low_q = r_q["response"].lower()
        self.assertIn("programming language", low_q)
        self.assertIn("embedded database", low_q)

    def test_science_paragraph_and_pronoun_topic_preservation(self):
        # Pronoun 'It' must stay bound to 'computer' even after 'We can use computers...'
        self.brain.observe_bulk(
            "Computer is an electronic machine. "
            "We can use computers for studying and playing games. "
            "It can store a lot of information."
        )
        r_can = self.brain.observe_bulk("Can a computer store a lot of information?")
        self.assertEqual(r_can["mode"], "stored")
        self.assertIn("yes", r_can["response"].lower())

        # Full 10-sentence Science paragraph must learn all 10 facts cleanly
        sci = self.brain.observe_bulk(
            "Science helps us understand the world around us. "
            "The sun gives us heat and light. "
            "Plants need water, air, and sunlight to grow. "
            "Water is essential for all living things. "
            "The moon is a natural satellite of the Earth. "
            "Our body needs oxygen to stay alive. "
            "Electricity is used to run many machines. "
            "The Earth revolves around the sun. "
            "Animals and plants are living things. "
            "Scientists discover new things through experiments."
        )
        self.assertEqual(len(sci["learned"]), 10)

        r_sun = self.brain.observe_bulk("What does the sun give us?")
        self.assertIn("heat and light", r_sun["response"].lower())

        r_plants = self.brain.observe_bulk("What do plants need to grow?")
        self.assertIn("water, air, and sunlight", r_plants["response"].lower())

        r_body = self.brain.observe_bulk("What does our body need to stay alive?")
        self.assertIn("oxygen", r_body["response"].lower())

        r_earth = self.brain.observe_bulk("What does the Earth revolve around?")
        self.assertIn("sun", r_earth["response"].lower())


if __name__ == "__main__":
    unittest.main()
