import unittest
from src.morphology import swap_pronouns

class TestPronounSwap(unittest.TestCase):
    def test_my_to_your(self):
        self.assertEqual(swap_pronouns("muskan is my crush"), "muskan is your crush")

    def test_i_am(self):
        self.assertEqual(swap_pronouns("I am sad"), "you are sad")

    def test_im(self):
        self.assertEqual(swap_pronouns("I'm happy"), "you are happy")

    def test_me_to_you(self):
        self.assertEqual(swap_pronouns("you like me"), "you like you")

    def test_mine_to_yours(self):
        self.assertEqual(swap_pronouns("this is mine"), "this is yours")

    def test_no_change(self):
        self.assertEqual(swap_pronouns("mango is sweet"), "mango is sweet")

if __name__ == "__main__":
    unittest.main(verbosity=2)
