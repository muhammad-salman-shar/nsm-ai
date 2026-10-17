import os
import tempfile
import unittest
from src.brain import Brain
from src import persistence


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.path = self.tmp.name
        os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        tmpfile = self.path + ".tmp"
        if os.path.exists(tmpfile):
            os.remove(tmpfile)

    def test_save_load_roundtrip(self):
        b = Brain()
        b.observe("I saw a zork")
        b.observe("zork is animal")
        b.observe("i love mangoes")
        definitions = dict(b.definitions)
        relations = b.relations.get("IS", "zork")
        episodes = b.episodic.size()

        persistence.save(b, self.path)
        self.assertTrue(os.path.exists(self.path))

        b2 = Brain()
        loaded = persistence.load(b2, self.path)
        self.assertTrue(loaded)
        self.assertEqual(b2.definitions, definitions)
        self.assertEqual(b2.relations.get("IS", "zork"), relations)
        self.assertEqual(b2.episodic.size(), episodes)
        self.assertEqual(b2.turn, b.turn)

    def test_load_nonexistent_returns_false(self):
        b = Brain()
        result = persistence.load(b, "/tmp/definitely_not_here_xyz.json")
        self.assertFalse(result)

    def test_atomic_write(self):
        b = Brain()
        b.observe("hello")
        persistence.save(b, self.path)
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_reset(self):
        b = Brain()
        b.observe("hello")
        persistence.save(b, self.path)
        self.assertTrue(os.path.exists(self.path))
        persistence.reset(self.path)
        self.assertFalse(os.path.exists(self.path))

    def test_recall_works_after_reload(self):
        b = Brain()
        b.observe("I love mangoes")
        b.observe("pizza is food")
        persistence.save(b, self.path)

        b2 = Brain()
        persistence.load(b2, self.path)
        r = b2.observe("mangoes")
        self.assertIsNotNone(r["recall"])
        self.assertIn("mangoes", r["recall"])

    def test_relations_persist(self):
        b = Brain()
        b.observe("I saw a zork")
        b.observe("zork is animal")
        b.observe("actually zork is bird")
        persistence.save(b, self.path)

        b2 = Brain()
        persistence.load(b2, self.path)
        self.assertEqual(b2.relations.get("IS", "zork"), ["bird"])
        hist = b2.relations.history("IS", "zork")
        self.assertTrue(hist["animal"]["superseded"])

    def test_definition_query_after_reload(self):
        b = Brain()
        b.observe("I saw a zork")
        b.observe("zork is a striped animal")
        persistence.save(b, self.path)

        b2 = Brain()
        persistence.load(b2, self.path)
        r = b2.observe("what is zork")
        self.assertIn("zork", r["response"].lower())
        self.assertIn("animal", r["response"])

    def test_affect_persists(self):
        b = Brain()
        b.observe("hi")
        b.observe("hello")
        mood = b.affect.mood()
        persistence.save(b, self.path)

        b2 = Brain()
        persistence.load(b2, self.path)
        self.assertEqual(b2.affect.mood(), mood)


if __name__ == "__main__":
    unittest.main(verbosity=2)
