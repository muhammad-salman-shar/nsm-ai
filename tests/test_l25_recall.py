import unittest
from src.brain import Brain


class TestRecallGating(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_no_cross_recall_on_shared_function_words(self):
        self.b.observe("i am salman")
        r = self.b.observe("i am happy")
        # should NOT say "I remember you said 'i am salman'"
        self.assertNotIn("i am salman", r["response"].lower())

    def test_no_recall_between_questions(self):
        self.b.observe("what is your name")
        r = self.b.observe("what is happy")
        self.assertNotIn("your name", r["response"].lower())
        self.assertNotIn("I remember you said", r["response"])

    def test_meaningful_recall_still_works(self):
        self.b.observe("i love mangoes")
        r = self.b.observe("do i love mangoes")
        self.assertIn("mangoes", r["response"].lower())

    def test_what_is_undefined_known_word_triggers_question(self):
        # "happy" is in lexicon from training data but no definition
        r = self.b.observe("what is happy")
        self.assertIn("don't know", r["response"].lower())
        self.assertIn("happy", r["response"].lower())
        self.assertIsNotNone(self.b.pending)

    def test_what_is_unknown_word_still_asks(self):
        r = self.b.observe("what is zorblax")
        self.assertIn("zorblax", r["response"].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)

class TestPendingCancel(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_greeting_cancels_pending(self):
        self.b.observe("what is zorblax")
        self.assertIsNotNone(self.b.pending)
        r = self.b.observe("hello")
        self.assertIsNone(self.b.pending)
        self.assertNotIn("zorblax means", r["response"].lower())
        self.assertIn("hello", r["response"].lower())

    def test_skip_cancels_pending(self):
        self.b.observe("what is zorblax")
        r = self.b.observe("skip")
        self.assertIsNone(self.b.pending)

    def test_valid_definition_still_works(self):
        self.b.observe("what is zorblax")
        r = self.b.observe("zorblax is an animal")
        self.assertIn("zorblax", self.b.definitions)
