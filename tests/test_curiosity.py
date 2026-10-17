import unittest
from src.brain import Brain, STOPWORDS


class TestCuriosity(unittest.TestCase):
    def setUp(self):
        self.b = Brain()

    def test_new_word_triggers_question(self):
        r = self.b.observe("I saw a zebra")
        self.assertIn("zebra", r["response"])
        self.assertIn("?", r["response"])
        self.assertIsNotNone(self.b.pending)
        self.assertEqual(self.b.pending[0], "zebra")

    def test_known_word_no_question(self):
        r = self.b.observe("hello there")
        self.assertNotIn("don't know", r["response"].lower())
        self.assertIsNone(self.b.pending)

    def test_explanation_stored(self):
        self.b.observe("I saw a zebra")
        self.b.observe("zebra is a striped animal")
        self.assertIn("zebra", self.b.definitions)
        self.assertIn("striped", self.b.definitions["zebra"])

    def test_pending_cleared_after_explanation(self):
        self.b.observe("I saw a zebra")
        self.assertIsNotNone(self.b.pending)
        # explanation with only known words -> no new followup
        self.b.observe("zebra is an animal")
        self.assertIsNone(self.b.pending)

    def test_followup_question_on_new_word_in_explanation(self):
        self.b.observe("I saw a zebra")
        r = self.b.observe("zebra has stripes")
        self.assertIn("stripes", r["response"])
        self.assertIn("?", r["response"])
        self.assertIsNotNone(self.b.pending)
        self.assertEqual(self.b.pending[0], "stripes")

    def test_original_answered_after_learning(self):
        self.b.observe("I saw a zebra")
        r = self.b.observe("zebra is an animal")
        self.assertTrue(r["response"].startswith("Got it!"))
        self.assertIsNone(self.b.pending)

    def test_definition_recall_later(self):
        self.b.observe("I saw a zebra")
        self.b.observe("zebra is an animal")
        r = self.b.observe("what is zebra")
        self.assertIn("zebra", r["response"].lower())
        self.assertIn("animal", r["response"])

    def test_max_depth_prevents_infinite_loop(self):
        self.b.observe("I saw a zzzz")
        for _ in range(10):
            if self.b.pending:
                self.b.observe("a bbbb cccc dddd eeee")
            else:
                break
        # loop terminates, no crash
        self.assertLessEqual(self.b.ask_depth, 3)

    def test_stopwords_dont_trigger_question(self):
        for w in list(STOPWORDS)[:30]:
            if len(w) >= 3:
                self.b.observe(w)
                self.assertIsNone(self.b.pending, f"stopword '{w}' triggered question")

    def test_definition_used_in_future_answer(self):
        self.b.observe("tell me about rocket")
        self.b.observe("rocket is a spaceship")
        r = self.b.observe("what is rocket")
        self.assertIn("spaceship", r["response"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
