import os
import tempfile
import unittest
from unittest import mock

import numpy as np

import voice_gate.database as db_module


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.db_path = os.path.join(self.temp_dir.name, "test_db.pkl")
        patcher = mock.patch("voice_gate.database.DB_PATH", self.db_path)
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_load_db_returns_empty_when_file_missing(self):
        db = db_module.load_db()
        self.assertEqual(db, {})

    def test_save_and_load_roundtrip(self):
        original = {"alice": {"embedding": np.array([1.0, 2.0], dtype=np.float32)}}
        db_module.save_db(original)

        loaded = db_module.load_db()
        self.assertIn("alice", loaded)
        np.testing.assert_allclose(loaded["alice"]["embedding"], original["alice"]["embedding"])

    def test_create_user_persists_record(self):
        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        audio_files = ["sample_1.wav", "sample_2.wav"]

        user_data = db_module.create_user("alice", embedding, audio_files)
        self.assertIn("embedding", user_data)
        self.assertEqual(len(user_data["samples"]), 2)

        db = db_module.load_db()
        self.assertIn("alice", db)
        np.testing.assert_allclose(db["alice"]["embedding"], embedding)

    def test_delete_user_removes_files_and_record(self):
        embedding = np.array([0.5, 0.6], dtype=np.float32)
        sample_path = os.path.join(self.temp_dir.name, "sample.wav")
        with open(sample_path, "wb") as fp:
            fp.write(b"data")

        db_module.create_user("alice", embedding, [sample_path])
        db = db_module.load_db()

        removed = db_module.delete_user(db, "alice")
        self.assertTrue(removed)
        self.assertFalse(os.path.exists(sample_path))

        db_after = db_module.load_db()
        self.assertNotIn("alice", db_after)

    def test_delete_user_sample_updates_database(self):
        embedding = np.array([0.2, 0.3], dtype=np.float32)
        sample_path = os.path.join(self.temp_dir.name, "sample.wav")
        with open(sample_path, "wb") as fp:
            fp.write(b"data")

        db_module.create_user("alice", embedding, [sample_path])
        db = db_module.load_db()

        removed = db_module.delete_user_sample(db, "alice", sample_path)
        self.assertTrue(removed)
        self.assertFalse(os.path.exists(sample_path))
        self.assertEqual(db["alice"]["samples"], [])

    def test_add_user_sample_updates_embedding(self):
        embedding = np.array([0.1, 0.1], dtype=np.float32)
        db_module.create_user("alice", embedding, [])
        db = db_module.load_db()

        new_embedding = np.array([0.9, 0.9], dtype=np.float32)
        updated = db_module.add_user_sample(db, "alice", "sample_2.wav", new_embedding)
        self.assertTrue(updated)
        self.assertIn("sample_2.wav", db["alice"]["samples"])
        np.testing.assert_allclose(db["alice"]["embedding"], new_embedding)

    def test_get_user_stats_returns_expected_values(self):
        embedding = np.array([0.1, 0.2], dtype=np.float32)
        db_module.create_user("alice", embedding, ["s1.wav", "s2.wav"])
        db_module.create_user("bob", embedding, ["s3.wav"])

        db = db_module.load_db()
        stats = db_module.get_user_stats(db)

        self.assertEqual(stats["total_users"], 2)
        self.assertEqual(stats["total_samples"], 3)
        self.assertAlmostEqual(stats["avg_samples"], 1.5)


if __name__ == "__main__":
    unittest.main()
