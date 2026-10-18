import unittest
from src.brain import Brain

class TestBrainL5(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_transitive_reasoning(self):
        self.b.observe("salman is human")
        self.b.observe("human is mortal")
        
        # NSM should not just know this directly, it should INFER it.
        r = self.b.observe("is salman mortal")
        
        self.assertIn("Yes", r["response"])
        self.assertIn("because salman is human and human is mortal", r["response"])

    def test_reasoning_fails_honestly(self):
        self.b.observe("salman is human")
        
        # Should not hallucinate
        r = self.b.observe("is salman a bird")
        self.assertNotIn("Yes", r["response"])
        self.assertIn("don't know", r["response"].lower())

if __name__ == "__main__":
    unittest.main(verbosity=2)
