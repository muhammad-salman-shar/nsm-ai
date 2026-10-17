import unittest
from src.relations import extract, RelationStore


def _tuples(rels):
    return [(r["type"], r["subject"], r["object"]) for r in rels]


class TestExtraction(unittest.TestCase):
    def test_is_a_adjective_noun(self):
        rels = _tuples(extract("zebra", "zebra is a striped animal"))
        self.assertIn(("IS", "zebra", "animal"), rels)
        self.assertNotIn(("IS", "zebra", "striped"), rels)

    def test_is_plain(self):
        self.assertIn(("IS", "zebra", "animal"),
                      _tuples(extract("zebra", "zebra is animal")))

    def test_is_an(self):
        self.assertIn(("IS", "apple", "fruit"),
                      _tuples(extract("apple", "apple is an fruit")))

    def test_has_plain(self):
        self.assertIn(("HAS", "zebra", "stripes"),
                      _tuples(extract("zebra", "zebra has stripes")))

    def test_has_a(self):
        self.assertIn(("HAS", "zebra", "tail"),
                      _tuples(extract("zebra", "zebra has a tail")))

    def test_means(self):
        self.assertIn(("IS", "striped", "lines"),
                      _tuples(extract("striped", "striped means lines")))

    def test_adjective_alone_no_relation(self):
        rels = _tuples(extract("zebra", "zebra is beautiful"))
        self.assertIn(("IS", "zebra", "beautiful"), rels)

    def test_no_verb_no_relation(self):
        self.assertEqual(extract("zebra", "zebra striped animal"), [])

    def test_subject_not_duplicate(self):
        self.assertEqual(extract("zebra", "zebra is a zebra"), [])

    def test_correction_flag_set(self):
        rels = extract("zebra", "actually zebra is mammal")
        self.assertTrue(rels and rels[0]["correct"])

    def test_plain_no_correction(self):
        rels = extract("zebra", "zebra is mammal")
        self.assertFalse(rels and rels[0]["correct"])


class TestRelationStore(unittest.TestCase):
    def test_add_get(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        rs.add("IS", "zebra", "mammal")
        self.assertEqual(rs.get("IS", "zebra"), ["animal", "mammal"])

    def test_dedup(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        rs.add("IS", "zebra", "animal")
        self.assertEqual(rs.count(), 1)

    def test_correction_supersedes(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        rs.add("IS", "zebra", "mammal", correct=True)
        self.assertEqual(rs.get("IS", "zebra"), ["mammal"])
        self.assertEqual(rs.get("IS", "zebra", include_superseded=True),
                         ["animal", "mammal"])

    def test_query_yes(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        status, _ = rs.query("IS", "zebra", "animal")
        self.assertEqual(status, "yes")

    def test_query_unknown(self):
        rs = RelationStore()
        status, _ = rs.query("IS", "zebra", "animal")
        self.assertEqual(status, "unknown_subject")

    def test_query_no(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        status, detail = rs.query("IS", "zebra", "bird")
        self.assertEqual(status, "no")
        self.assertIn("animal", detail)


if __name__ == "__main__":
    unittest.main(verbosity=2)
