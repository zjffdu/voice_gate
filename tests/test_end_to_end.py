import os
import tempfile
import unittest
from unittest import mock

import numpy as np

from voice_gate import database
from voice_gate.audio_processor import calculate_prototype
from voice_gate.verifier import get_similarity_ranking, verify_voice


class TestEndToEndFlow(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.db_path = os.path.join(self.temp_dir.name, "voice_gate_e2e.pkl")
        patcher = mock.patch("voice_gate.database.DB_PATH", self.db_path)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_registration_and_verification_cycle(self):
        alice_samples = [
            np.array([0.9, 0.1, 0.0], dtype=np.float32),
            np.array([1.0, 0.0, 0.0], dtype=np.float32),
            np.array([0.95, 0.05, 0.0], dtype=np.float32),
        ]
        bob_samples = [
            np.array([0.1, 0.9, 0.0], dtype=np.float32),
            np.array([0.0, 1.0, 0.0], dtype=np.float32),
            np.array([0.05, 0.95, 0.0], dtype=np.float32),
        ]

        alice_proto = calculate_prototype(alice_samples)
        bob_proto = calculate_prototype(bob_samples)

        database.create_user("alice", alice_proto, ["alice_sample.wav"])
        database.create_user("bob", bob_proto, ["bob_sample.wav"])

        db = database.load_db()

        probe = alice_proto + np.array([0.01, -0.01, 0.0], dtype=np.float32)
        result = verify_voice(probe, db, threshold=0.6)

        self.assertTrue(result["passed"])
        self.assertEqual(result["matched_user"], "alice")

        ranking = get_similarity_ranking(result["all_similarities"], threshold=0.6)
        self.assertEqual(ranking[0]["user_id"], "alice")
        self.assertEqual(ranking[1]["user_id"], "bob")

        stats = database.get_user_stats(db)
        self.assertEqual(stats["total_users"], 2)
        self.assertEqual(stats["total_samples"], 2)

    def test_verification_failure_when_probe_far_from_any_user(self):
        prototype = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        database.create_user("alice", prototype, ["alice.wav"])
        db = database.load_db()

        probe = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        result = verify_voice(probe, db, threshold=0.9)

        self.assertEqual(result["matched_user"], "alice")
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
