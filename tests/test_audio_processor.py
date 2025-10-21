import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import voice_gate.audio_processor as audio_processor


class TestAudioProcessor(unittest.TestCase):
    def test_embed_audio_resamples_when_sample_rate_differs(self):
        fake_embedding = np.full(256, 0.5, dtype=np.float32)
        fake_encoder = mock.Mock()
        fake_encoder.embed_utterance.return_value = fake_embedding

        with mock.patch.object(audio_processor, "get_encoder", return_value=fake_encoder) as mocked_get:
            with mock.patch.object(audio_processor, "preprocess_wav", side_effect=lambda data, source_sr=None: data) as mocked_pre:
                audio = np.ones(8000, dtype=np.float32)
                result = audio_processor.embed_audio(audio, sr=8000)

        mocked_get.assert_called_once()
        mocked_pre.assert_called_once()
        # 8000Hz 情况应传入 source_sr 参数
        self.assertEqual(mocked_pre.call_args.kwargs.get("source_sr"), 8000)
        fake_encoder.embed_utterance.assert_called_once()
        np.testing.assert_allclose(result, fake_embedding)
        self.assertEqual(result.dtype, np.float32)

    def test_embed_audio_uses_direct_preprocess_when_sample_rate_matches(self):
        fake_embedding = np.arange(256, dtype=np.float32)
        fake_encoder = mock.Mock()
        fake_encoder.embed_utterance.return_value = fake_embedding

        with mock.patch.object(audio_processor, "get_encoder", return_value=fake_encoder):
            with mock.patch.object(audio_processor, "preprocess_wav", side_effect=lambda data, source_sr=None: data) as mocked_pre:
                audio = np.ones(audio_processor.MODEL_SAMPLE_RATE, dtype=np.float32)
                audio_processor.embed_audio(audio, sr=audio_processor.MODEL_SAMPLE_RATE)

        # 同采样率情况下，不应传递 source_sr
        self.assertIsNone(mocked_pre.call_args.kwargs.get("source_sr"))

    def test_save_audio_sample_writes_file_to_configured_directory(self):
        audio = np.zeros(16000, dtype=np.float32)

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.object(audio_processor, "AUDIO_DIR", tmpdir):
                Path(audio_processor.AUDIO_DIR).mkdir(parents=True, exist_ok=True)
                saved_path = audio_processor.save_audio_sample("alice", audio, 16000, 1)

            self.assertTrue(saved_path.startswith(tmpdir))
            self.assertTrue(os.path.exists(saved_path))
            self.assertTrue(Path(saved_path).name.startswith("alice_1_"))

    def test_calculate_prototype_returns_average(self):
        embeddings = [
            np.array([1.0, 2.0, 3.0], dtype=np.float32),
            np.array([3.0, 4.0, 5.0], dtype=np.float32),
        ]

        prototype = audio_processor.calculate_prototype(embeddings)
        np.testing.assert_allclose(prototype, np.array([2.0, 3.0, 4.0], dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
