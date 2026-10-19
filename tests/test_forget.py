import unittest
from src.brain import Brain

class TestForgetSystem(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_forget_name(self):
        self.b.observe("my name is salman")
        r1 = self.b.observe("what is my name")
        self.assertIn("salman", r1["response"].lower())
        
        self.b.observe("forget my name")
        r2 = self.b.observe("what is my name")
        self.assertNotIn("salman", r2["response"].lower())
        self.assertIn("don't know", r2["response"].lower())

    def test_forget_word(self):
        self.b.observe("tiger is a mammal")
        self.b.observe("forget tiger")
        r = self.b.observe("what is tiger")
        self.assertIn("don't know", r["response"].lower())

if __name__ == "__main__":
    unittest.main(verbosity=2)
