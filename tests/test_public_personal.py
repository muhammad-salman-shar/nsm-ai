import unittest
from src.brain import Brain
from src import database, persistence

class TestPublicPersonal(unittest.TestCase):
    def setUp(self):
        # Cleanup any previous test data
        database.delete_brain("public")
        database.delete_brain("user_A")
        database.delete_brain("user_B")

    def tearDown(self):
        database.delete_brain("public")
        database.delete_brain("user_A")
        database.delete_brain("user_B")

    def load_brain_with_readthrough(self, user_id):
        b = Brain(auto_save_path=None)
        public_state = database.load_brain("public")
        if public_state:
            persistence.from_dict(b, public_state)
        if user_id != "public":
            personal_state = database.load_brain(user_id)
            if personal_state:
                persistence.from_dict(b, personal_state)
        return b

    def test_read_through_and_isolation(self):
        # 1. Global Brain learns something
        global_brain = Brain(auto_save_path=None)
        global_brain.observe("delhi is in india")
        database.save_brain("public", persistence.to_dict(global_brain))

        # 2. User A comes, should know about Delhi (from global)
        user_a = self.load_brain_with_readthrough("user_A")
        r1 = user_a.observe("is delhi in india")
        self.assertIn("Yes", r1["response"])

        # 3. User A learns a personal fact
        user_a.observe("my name is Salman")
        database.save_brain("user_A", persistence.to_dict(user_a))

        # 4. User B comes, should know about Delhi, but NOT user A's name
        user_b = self.load_brain_with_readthrough("user_B")
        r2 = user_b.observe("is delhi in india")
        self.assertIn("Yes", r2["response"])
        
        r3 = user_b.observe("what is my name")
        self.assertIn("don't know", r3["response"].lower())

        # 5. User A comes back, should remember their name
        user_a_reload = self.load_brain_with_readthrough("user_A")
        r4 = user_a_reload.observe("what is my name")
        self.assertIn("Salman", r4["response"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
