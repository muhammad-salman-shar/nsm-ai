import unittest
from src.brain import Brain

class TestSelfKnowledge(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_nsm_definition(self):
        r = self.b.observe("What is NSM")
        self.assertIn("neuro-symbolic", r["response"].lower())

    def test_company_definition(self):
        r = self.b.observe("Tell me about NeuraSaMu")
        self.assertIn("ai research", r["response"].lower())

    def test_founder_definition_multiword(self):
        # Tests multi-word extraction (Muhammad Salman)
        r = self.b.observe("Who is Muhammad Salman")
        self.assertIn("ceo", r["response"].lower())

    def test_define_trigger(self):
        r = self.b.observe("Define Akira")
        self.assertIn("muhammad salman", r["response"].lower())

if __name__ == "__main__":
    unittest.main()
