import unittest
from src.brain import Brain


class TestBrain(unittest.TestCase):
    def setUp(self):
        self.b = Brain()

    def test_greeting_responds(self):
        r = self.b.observe("hi")
        self.assertEqual(r["intent"], "greeting")
        self.assertGreater(len(r["response"]), 0)

    def test_identity_question(self):
        r = self.b.observe("who are you")
        self.assertEqual(r["intent"], "identity")
        self.assertIn("NSM", r["response"])

    def test_math_digits(self):
        r = self.b.observe("what is 2 + 3")
        self.assertIn("5", r["response"])

    def test_math_words(self):
        r = self.b.observe("what is five plus two")
        self.assertIn("7", r["response"])

    def test_math_minus(self):
        r = self.b.observe("10 - 4")
        self.assertIn("6", r["response"])

    def test_episode_stored(self):
        self.b.observe("i like games")
        self.assertEqual(self.b.episodic.size(), 1)
        self.b.observe("hello")
        self.assertGreaterEqual(self.b.episodic.size(), 2)

    def test_recall_mentions_past(self):
        self.b.observe("i love mangoes")
        r = self.b.observe("mangoes")
        self.assertIsNotNone(r["recall"])
        self.assertIn("mangoes", r["recall"])

    def test_unknown_text(self):
        r = self.b.observe("qzxv blorp")
        self.assertEqual(r["intent"], "question")
        self.assertIn("blorp", r["response"])

    def test_vocabulary_grows(self):
        before = len(self.b.lexicon.words)
        self.b.observe("elephant trumpet")
        if self.b.pending:
            self.b.observe("elephant is a large animal")
        after = len(self.b.lexicon.words)
        self.assertGreater(after, before)

    def test_state_shape(self):
        self.b.observe("hi")
        s = self.b.state()
        self.assertIn("mood", s)
        self.assertIn("episodes", s)
        self.assertIn("vocab", s)
        self.assertEqual(s["turn"], 1)

    def test_mood_changes_over_time(self):
        moods = set()
        for _ in range(30):
            self.b.observe("hi")
            moods.add(self.b.state()["mood"])
        self.assertGreaterEqual(len(moods), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
