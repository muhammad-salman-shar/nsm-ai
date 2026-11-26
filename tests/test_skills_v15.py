"""Tests for NSM VB v1.5 Teach Skills Engine (Prompt-to-Skill Import, Export, Toggle, Workflows)."""

import unittest

from src import skills
from src.brain import Brain


SAMPLE_SKILL_PACK = {
    "nsm_version": "1.5",
    "package_type": "skill_pack",
    "skill": {
        "id": "git_doctor",
        "name": "Git Doctor",
        "version": "1.0.0",
        "author": "AI Generated",
        "description": "Diagnoses and fixes common Git merge and push issues.",
        "enabled": True,
        "trigger_keywords": ["git", "merge conflict", "rebase"],
        "facts": [
            {
                "relation": "CAUSES",
                "agent": "divergent branches",
                "patient": "non-fast-forward push rejection",
                "polarity": 1,
            },
            {
                "relation": "USED_FOR",
                "agent": "git stash",
                "patient": "temporarily shelving uncommitted local changes",
                "polarity": 1,
            },
        ],
        "patterns": [
            {
                "id": "git_fix_cmd",
                "kind": "question",
                "qtype": "QUERY_PURPOSE",
                "pattern": r"^what\s+does\s+(.+?)\s+do\s+in\s+git$",
                "slots": {"subject": 1},
                "meta": {"relation": "USED_FOR"},
            }
        ],
        "workflows": [
            {
                "id": "wf_git_conflict",
                "trigger": "resolve a git merge conflict",
                "steps": [
                    "Run git status to list conflicted files.",
                    "Edit the conflict markers and keep the intended code.",
                    "Stage resolved files with git add and finish with git commit.",
                ],
            }
        ],
        "mcp_tools": [],
    },
}


class TestTeachSkillsV15(unittest.TestCase):
    def test_prompt_template_and_install_query_workflow(self):
        self.assertIn("package_type", skills.AI_SKILL_GENERATOR_PROMPT)
        self.assertIn("skill_pack", skills.AI_SKILL_GENERATOR_PROMPT)

        brain = Brain(seed_core=True)
        res = skills.install_skill_package(brain, SAMPLE_SKILL_PACK)
        self.assertTrue(res["ok"])
        self.assertEqual(res["installed"][0]["id"], "git_doctor")

        # 1. Fact learned from skill
        q_fact = brain.observe_bulk("What causes non-fast-forward push rejection?")
        self.assertEqual(q_fact["mode"], "stored")
        self.assertIn("divergent branches", q_fact["response"].lower())

        # 2. Custom regex pattern learned from skill
        q_pat = brain.observe_bulk("What does git stash do in git?")
        self.assertEqual(q_pat["mode"], "stored")
        self.assertIn("shelving uncommitted local changes", q_pat["response"].lower())

        # 3. Multi-step workflow learned from skill
        q_wf = brain.observe_bulk("How to resolve a git merge conflict?")
        self.assertEqual(q_wf["mode"], "stored")
        self.assertEqual(q_wf["intent"], "skill_workflow")
        self.assertIn("Step 1:", q_wf["response"])

    def test_toggle_export_and_delete_skill(self):
        brain = Brain(seed_core=True)
        skills.install_skill_package(brain, SAMPLE_SKILL_PACK)

        # Export single skill pack
        exp = skills.export_skills_package(brain, "git_doctor")
        self.assertTrue(exp["ok"])
        self.assertEqual(exp["package"]["package_type"], "skill_pack")

        # Toggle OFF -> frames & workflow disappear cleanly
        tog_off = skills.toggle_skill(brain, "git_doctor", False)
        self.assertTrue(tog_off["ok"])
        q_off = brain.observe_bulk("What is git stash used for?")
        self.assertEqual(q_off["mode"], "unknown")

        # Toggle ON -> frames & workflow return
        tog_on = skills.toggle_skill(brain, "git_doctor", True)
        self.assertTrue(tog_on["ok"])
        q_on = brain.observe_bulk("What is git stash used for?")
        self.assertEqual(q_on["mode"], "stored")

        # Delete skill completely
        d_res = skills.delete_skill(brain, "git_doctor")
        self.assertTrue(d_res["ok"])
        self.assertEqual(len(skills.list_skills_summary(brain)), 0)


if __name__ == "__main__":
    unittest.main()
