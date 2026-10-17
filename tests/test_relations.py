import unittest
from src.relations import extract, RelationStore


class TestExtraction(unittest.TestCase):
    def test_is_a_adjective_noun(self):
        rels = extract("zebra", "zebra is a striped animal")
        self.assertIn(("IS", "zebra", "animal"), rels)
        self.assertNotIn(("IS", "zebra", "striped"), rels)

    def test_is_plain(self):
        rels = extract("zebra", "zebra is animal")
        self.assertIn(("IS", "zebra", "animal"), rels)

    def test_is_an(self):
        rels = extract("apple", "apple is an fruit")
        self.assertIn(("IS", "apple", "fruit"), rels)

    def test_has_plain(self):
        rels = extract("zebra", "zebra has stripes")
        self.assertIn(("HAS", "zebra", "stripes"), rels)

    def test_has_a(self):
        rels = extract("zebra", "zebra has a tail")
        self.assertIn(("HAS", "zebra", "tail"), rels)

    def test_means(self):
        rels = extract("striped", "striped means lines")
        self.assertIn(("IS", "striped", "lines"), rels)

    def test_adjective_alone_no_relation(self):
        rels = extract("zebra", "zebra is beautiful")
        self.assertIn(("IS", "zebra", "beautiful"), rels)

    def test_no_verb_no_relation(self):
        rels = extract("zebra", "zebra striped animal")
        self.assertEqual(rels, [])

    def test_subject_not_duplicate(self):
        rels = extract("zebra", "zebra is a zebra")
        self.assertEqual(rels, [])


class TestRelationStore(unittest.TestCase):
    def test_add_get(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        rs.add("IS", "zebra", "mammal")
        self.assertEqual(rs.get("IS", "zebra"), ["animal", "mammal"])
        self.assertTrue(rs.has("IS", "zebra", "animal"))
        self.assertFalse(rs.has("IS", "zebra", "reptile"))

    def test_dedup(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        rs.add("IS", "zebra", "animal")
        self.assertEqual(rs.count(), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
