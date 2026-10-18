import unittest
from src.brain import Brain
from src import database, persistence

class TestMultiUser(unittest.TestCase):
    def test_users_do_not_mix_data(self):
        # Setup fresh brains for two users
        u1_brain = Brain(auto_save_path=None)
        u2_brain = Brain(auto_save_path=None)

        # User 1 learns name is Salman
        u1_brain.observe("my name is Salman")
        database.save_brain("user_1", persistence.to_dict(u1_brain))

        # User 2 learns name is Rahul
        u2_brain.observe("my name is Rahul")
        database.save_brain("user_2", persistence.to_dict(u2_brain))

        # Reload from DB (simulating server restart or new session)
        u1_reload = Brain(auto_save_path=None)
        state1 = database.load_brain("user_1")
        if state1:
            persistence.from_dict(u1_reload, state1)

        u2_reload = Brain(auto_save_path=None)
        state2 = database.load_brain("user_2")
        if state2:
            persistence.from_dict(u2_reload, state2)

        # Check answers
        r1 = u1_reload.observe("what is my name")
        r2 = u2_reload.observe("what is my name")

        self.assertIn("Salman", r1["response"])
        self.assertIn("Rahul", r2["response"])
        self.assertNotIn("Salman", r2["response"])
        self.assertNotIn("Rahul", r1["response"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
