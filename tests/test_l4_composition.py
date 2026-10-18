import unittest
from src.brain import Brain

class TestL4Composition(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_composition_sweet_mangoes(self):
        # Learn SVO and property
        self.b.observe("salman likes mangoes")
        self.b.observe("mangoes are sweet")
        
        # Ask the question
        r = self.b.observe("what does salman like")
        
        # Expect composed sentence
        self.assertEqual(r["response"], "Salman likes sweet mangoes.")

    def test_composition_fast_car(self):
        self.b.observe("salman wants a car")
        self.b.observe("car is fast")
        
        r = self.b.observe("what does salman want")
        self.assertEqual(r["response"], "Salman wants fast car.")

    def test_composition_fallback(self):
        # No property known for car
        self.b.observe("salman wants a car")
        
        r = self.b.observe("what does salman want")
        self.assertEqual(r["response"], "Salman wants car.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
