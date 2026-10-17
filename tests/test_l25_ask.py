import unittest
from src.brain import Brain


class TestAskMe(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_ask_me_something_returns_question(self):
        r = self.b.observe("ask me something")
        self.assertIn("?", r["response"])

    def test_ask_me_after_unknown_word(self):
        self.b.observe("what is zorblax")
        r = self.b.observe("ask me something")
        self.assertIn("zorblax", r["response"].lower())
        self.assertIn("?", r["response"])

    def test_ask_me_after_name_known(self):
        self.b.observe("my name is Salman")
        r = self.b.observe("ask me something")
        self.assertIn("?", r["response"])
        self.assertNotIn("your name", r["response"].lower())

    def test_ask_me_after_all_facts(self):
        self.b.observe("my name is Salman")
        self.b.observe("i am 25 years old")
        self.b.observe("i live in karachi")
        r = self.b.observe("ask me something")
        self.assertIn("?", r["response"])
        low = r["response"].lower()
        self.assertNotIn("your name", low)
        self.assertNotIn("how old", low)
        self.assertNotIn("where do you live", low)

    def test_ask_me_variants(self):
        for phrase in ["ask me anything", "ask me a question", "ask me"]:
            r = self.b.observe(phrase)
            self.assertIn("?", r["response"], f"failed for: {phrase}")

    def test_normal_message_not_hijacked(self):
        r = self.b.observe("hello")
        self.assertNotEqual(r["intent"], "question")
        r2 = self.b.observe("i love mangoes")
        self.assertIsNotNone(r2["response"])
        self.assertNotIn("what is your name", r2["response"].lower())
        self.assertNotIn("how old are you", r2["response"].lower())
        self.assertEqual(r2["intent"], "happy")


if __name__ == "__main__":
    unittest.main(verbosity=2)
