import unittest
from src.brain import Brain

class TestRememberSystem(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_remember_virtual_brain(self):
        self.b.observe("remember this: you are a virtual brain")
        r = self.b.observe("what are you")
        self.assertIn("NSM VB", r["response"]) # Should give identity, not "you means..."

    def test_remember_custom_fact(self):
        self.b.observe("remember this: my favorite color is blue")
        # Should not pollute the dictionary with "remember" or "this"
        self.assertNotIn("remember", self.b.definitions)
        self.assertNotIn("this", self.b.definitions)

if __name__ == "__main__":
    unittest.main(verbosity=2)
