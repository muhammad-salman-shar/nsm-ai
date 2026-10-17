import unittest
from src.facts import extract, query, format_answer, FactStore


class TestExtract(unittest.TestCase):
    def test_my_name_is(self):
        self.assertEqual(extract("my name is salman"), ("name", "Salman"))
        self.assertEqual(extract("My name is Salman"), ("name", "Salman"))

    def test_remember_my_name_is(self):
        self.assertEqual(extract("remember my name is salman"), ("name", "Salman"))

    def test_call_me(self):
        self.assertEqual(extract("call me sam"), ("name", "Sam"))

    def test_i_am_name(self):
        self.assertEqual(extract("i am salman"), ("name", "Salman"))

    def test_i_am_adjective_no_fact(self):
        self.assertIsNone(extract("i am happy"))
        self.assertIsNone(extract("i am hungry"))
        self.assertIsNone(extract("i am human"))

    def test_age(self):
        self.assertEqual(extract("i am 25 years old"), ("age", 25))
        self.assertEqual(extract("my age is 30"), ("age", 30))

    def test_location(self):
        self.assertEqual(extract("i live in karachi"), ("location", "Karachi"))
        self.assertEqual(extract("i am from lahore"), ("location", "Lahore"))

    def test_no_fact(self):
        self.assertIsNone(extract("what is your name"))
        self.assertIsNone(extract("hello there"))
        self.assertIsNone(extract("i like mangoes"))


class TestQuery(unittest.TestCase):
    def test_name_query(self):
        self.assertEqual(query("what is my name"), "name")
        self.assertEqual(query("What is my name?"), "name")
        self.assertEqual(query("what's my name"), "name")

    def test_age_query(self):
        self.assertEqual(query("how old am i"), "age")

    def test_location_query(self):
        self.assertEqual(query("where do i live"), "location")

    def test_no_query(self):
        self.assertIsNone(query("hello"))
        self.assertIsNone(query("is zebra animal"))


class TestFormatAnswer(unittest.TestCase):
    def test_name(self):
        self.assertEqual(format_answer("name", "Salman"), "Your name is Salman.")

    def test_age(self):
        self.assertEqual(format_answer("age", 25), "You are 25 years old.")

    def test_location(self):
        self.assertEqual(format_answer("location", "Karachi"), "You live in Karachi.")


class TestFactStore(unittest.TestCase):
    def test_set_get(self):
        fs = FactStore()
        fs.set("name", "Salman")
        self.assertEqual(fs.get("name"), "Salman")
        self.assertTrue(fs.has("name"))
        self.assertFalse(fs.has("age"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
