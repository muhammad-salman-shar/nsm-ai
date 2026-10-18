import unittest
from src.text_utils import split_sentences

class TestTextUtils(unittest.TestCase):
    def test_split_basic(self):
        text = "Hello there. How are you? I am fine!"
        result = split_sentences(text)
        self.assertEqual(result, ["Hello there.", "How are you?", "I am fine!"])

    def test_split_newlines(self):
        text = "My name is Salman.\nI like mangoes.\nMangoes are sweet."
        result = split_sentences(text)
        self.assertEqual(len(result), 3)

    def test_single_sentence(self):
        text = "Just one sentence."
        result = split_sentences(text)
        self.assertEqual(result, ["Just one sentence."])

if __name__ == "__main__":
    unittest.main(verbosity=2)
