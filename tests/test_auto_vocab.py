import unittest
from src.brain import Brain

class TestAutoVocab(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_unknown_word_added_silently(self):
        self.assertFalse(self.b.lexicon.has("zorblax"))
        self.b.observe("I saw a zorblax today")
        self.assertTrue(self.b.lexicon.has("zorblax"))

    def test_curiosity_only_on_first_encounter(self):
        # First time: should ask
        r1 = self.b.observe("I saw a zorblax")
        self.assertIn("zorblax", r1["response"].lower())

        # Second time: should NOT ask again (already in vocab)
        r2 = self.b.observe("I saw a zorblax again")
        self.assertNotIn("don't know the word 'zorblax'", r2["response"].lower())

    def test_multiple_words_in_sentence(self):
        self.b.observe("The quorb flibbles the zentrix")
        self.assertTrue(self.b.lexicon.has("quorb"))
        self.assertTrue(self.b.lexicon.has("zentrix"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
