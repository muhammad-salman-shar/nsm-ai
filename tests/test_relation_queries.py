import unittest
from src.brain import Brain
from src.relations import parse_query


class TestParseQuery(unittest.TestCase):
    def test_is_a_animal(self):
        self.assertEqual(parse_query("is zebra an animal"), ("IS", "zebra", "animal"))

    def test_is_plain(self):
        self.assertEqual(parse_query("is zebra animal"), ("IS", "zebra", "animal"))

    def test_is_adjective(self):
        self.assertEqual(parse_query("is zebra a big animal"), ("IS", "zebra", "animal"))

    def test_does_have(self):
        self.assertEqual(parse_query("does zebra have stripes"), ("HAS", "zebra", "stripes"))

    def test_not_a_query(self):
        self.assertIsNone(parse_query("what is zebra"))
        self.assertIsNone(parse_query("hi"))
        self.assertIsNone(parse_query("is"))


class TestRelationQueries(unittest.TestCase):
    def setUp(self):
        self.b = Brain()
        self.b.observe("I saw a zebra")
        self.b.observe("zebra is a striped animal")

    def test_yes_is_query(self):
        r = self.b.observe("is zebra an animal")
        self.assertIn("Yes", r["response"])
        self.assertIn("zebra", r["response"].lower())
        self.assertIn("animal", r["response"].lower())

    def test_unknown_relation_honest(self):
        r = self.b.observe("is zebra a bird")
        self.assertIn("I know", r["response"])
        self.assertIn("animal", r["response"])
        self.assertIn("bird", r["response"])
        self.assertNotIn("Yes", r["response"])

    def test_unknown_subject(self):
        r = self.b.observe("is flarg an animal")
        self.assertIn("don't know", r["response"].lower())

    def test_has_query_positive(self):
        self.b.observe("I saw a zygot")
        self.b.observe("zygot has wheels")
        r = self.b.observe("does zygot have wheels")
        self.assertIn("Yes", r["response"])

    def test_has_query_negative(self):
        self.b.observe("I saw a zizzle")
        self.b.observe("zizzle has springs")
        r = self.b.observe("does zizzle have wings")
        self.assertIn("I know", r["response"])
        self.assertIn("springs", r["response"])
        self.assertIn("wings", r["response"])

    def test_definition_still_works(self):
        r = self.b.observe("what is zebra")
        self.assertIn("zebra", r["response"].lower())
        self.assertIn("animal", r["response"])

    def test_state_shows_relations(self):
        s = self.b.state()
        self.assertGreaterEqual(s["relations"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

class TestRelationQueryPriority(unittest.TestCase):
    def test_relation_query_not_blocked_by_unknown_word(self):
        b = Brain()
        b.observe("I saw a zebra")
        b.observe("zebra is a striped animal")
        b.observe("is zebra an animal")
        r = b.observe("is zebra a bird")
        self.assertNotIn("don't know the word", r["response"].lower())
        self.assertIn("I know", r["response"])
        self.assertIn("animal", r["response"])
        self.assertIn("bird", r["response"])

    def test_unknown_subject_relation_query(self):
        b = Brain()
        r = b.observe("is flarg an animal")
        self.assertNotIn("don't know the word", r["response"].lower())
        self.assertIn("don't know", r["response"].lower())
        self.assertIn("flarg", r["response"])

    def test_non_relation_still_asks(self):
        b = Brain()
        r = b.observe("I saw a flarg")
        self.assertIn("don't know the word", r["response"].lower())
        self.assertIn("flarg", r["response"])
