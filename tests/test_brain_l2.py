import os
import tempfile
import unittest
from src.brain import Brain


class TestBrainL2(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_remember_name(self):
        r = self.b.observe("remember my name is Salman")
        self.assertIn("name", r["response"].lower())
        self.assertIn("salman", r["response"].lower())
        self.assertEqual(self.b.fact_store.get("name"), "Salman")

    def test_ask_name_after_learning(self):
        self.b.observe("my name is Salman")
        r = self.b.observe("what is my name")
        self.assertIn("Salman", r["response"])

    def test_i_am_name(self):
        r = self.b.observe("i am Salman")
        self.assertIn("salman", r["response"].lower())
        self.assertEqual(self.b.fact_store.get("name"), "Salman")

    def test_i_am_adjective_not_name(self):
        r = self.b.observe("i am happy")
        self.assertIsNone(self.b.fact_store.get("name"))
        self.assertNotEqual(r["intent"], "statement")

    def test_age(self):
        self.b.observe("i am 25 years old")
        r = self.b.observe("how old am i")
        self.assertIn("25", r["response"])

    def test_location(self):
        self.b.observe("i live in karachi")
        r = self.b.observe("where do i live")
        self.assertIn("Karachi", r["response"])

    def test_unknown_fact(self):
        r = self.b.observe("what is my name")
        self.assertIn("don't know", r["response"].lower())

    def test_facts_persist(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        path = tmp.name
        tmp.close()
        os.remove(path)
        try:
            b1 = Brain(auto_save_path=path)
            b1.observe("my name is Salman")
            b1.observe("i am 25 years old")

            b2 = Brain(auto_save_path=path)
            self.assertEqual(b2.fact_store.get("name"), "Salman")
            self.assertEqual(b2.fact_store.get("age"), 25)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_state_shows_facts(self):
        self.b.observe("my name is Salman")
        s = self.b.state()
        self.assertEqual(s["facts"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
