import unittest
from src.morphology import get_article, pluralize, conjugate_verb, get_pronoun

class TestMorphology(unittest.TestCase):
    def test_articles(self):
        self.assertEqual(get_article("apple"), "an")
        self.assertEqual(get_article("dog"), "a")
        self.assertEqual(get_article("hour"), "an")
        self.assertEqual(get_article("university"), "a")

    def test_plurals(self):
        self.assertEqual(pluralize("dog"), "dogs")
        self.assertEqual(pluralize("mango"), "mangoes")
        self.assertEqual(pluralize("baby"), "babies")
        self.assertEqual(pluralize("child"), "children")
        self.assertEqual(pluralize("leaf"), "leaves")

    def test_verb_conjugation(self):
        self.assertEqual(conjugate_verb("eat", "present", "i"), "eat")
        self.assertEqual(conjugate_verb("eat", "present", "he"), "eats")
        self.assertEqual(conjugate_verb("eat", "past"), "ate")
        self.assertEqual(conjugate_verb("play", "past"), "played")
        self.assertEqual(conjugate_verb("go", "future"), "will go")

    def test_pronouns(self):
        self.assertEqual(get_pronoun("i", "nominative"), "I")
        self.assertEqual(get_pronoun("i", "accusative"), "me")
        self.assertEqual(get_pronoun("i", "possessive"), "my")

if __name__ == "__main__":
    unittest.main(verbosity=2)
