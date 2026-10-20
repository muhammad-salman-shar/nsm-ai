import unittest
from src.memory_index import MemoryIndex

class TestMemoryIndex(unittest.TestCase):
    def setUp(self):
        self.mi = MemoryIndex()

    def test_keyword_extraction(self):
        text = "I went to Karachi to meet Dr Ahmed"
        kws = self.mi.extract_keywords(text)
        self.assertIn("karachi", kws)
        self.assertIn("ahmed", kws)
        self.assertNotIn("to", kws) # Stopword

    def test_save_and_search(self):
        self.mi.save_memory("Salman likes sweet mangoes from Multan")
        self.mi.save_memory("Ahmed lives in Karachi and works at Google")
        
        # Search for mangoes
        results = self.mi.search("tell me about mangoes")
        self.assertEqual(len(results), 1)
        self.assertIn("mangoes", results[0]["text"].lower())
        
        # Search for Ahmed
        results2 = self.mi.search("where is ahmed")
        self.assertEqual(len(results2), 1)
        self.assertIn("karachi", results2[0]["text"].lower())

if __name__ == "__main__":
    unittest.main(verbosity=2)
