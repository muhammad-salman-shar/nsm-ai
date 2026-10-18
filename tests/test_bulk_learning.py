import unittest
from src.brain import Brain

class TestBulkLearning(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_bulk_learning(self):
        text = "salman likes mangoes. mangoes are sweet. salman has a dog."
        r = self.b.observe_bulk(text)
        
        self.assertEqual(r["intent"], "bulk_learning")
        self.assertIn("I read all 3 sentences", r["response"])
        
        # Test if the facts were actually learned
        r2 = self.b.observe("what does salman like")
        self.assertEqual(r2["response"], "Salman likes sweet mangoes.")
        
        r3 = self.b.observe("does salman have a dog")
        self.assertIn("Yes", r3["response"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
