import unittest

import numpy as np

from nvbroadcast.audio.effects import AudioEffects


class _FakeRnnoise:
    @staticmethod
    def process_mono_frame(_state, frame):
        return frame, 0.5


class _HalfVolumeRnnoise:
    @staticmethod
    def process_mono_frame(_state, frame):
        return (frame // 2).astype(np.int16), 0.5


class _MuteWithVadRnnoise:
    def __init__(self, vad_values):
        self._vad_values = list(vad_values)

    def process_mono_frame(self, _state, frame):
        vad = self._vad_values.pop(0)
        return np.zeros_like(frame), vad


class AudioEffectsTests(unittest.TestCase):
    def test_denoiser_sanitizes_hot_input_before_output(self):
        effects = AudioEffects()
        effects._enabled = True
        effects._initialized = True
        effects._state = object()
        effects._rnnoise = _FakeRnnoise()
        effects._frame_size = 4

        audio = np.array([0.0, 2.0, -3.0, np.nan, np.inf], dtype=np.float32)

        result = effects.process_chunk(audio)

        self.assertEqual(result.dtype, np.float32)
        self.assertTrue(np.all(np.isfinite(result)))
        self.assertLessEqual(float(np.max(np.abs(result))), 0.98)

    def test_denoiser_buffers_unaligned_chunks(self):
        effects = AudioEffects()
        effects._enabled = True
        effects._initialized = True
        effects._state = object()
        effects._rnnoise = _HalfVolumeRnnoise()
        effects._frame_size = 4

        first = effects.process_chunk(np.array([0.1, 0.2, 0.3], dtype=np.float32))
        second = effects.process_chunk(np.array([0.4, 0.5, 0.6], dtype=np.float32))

        self.assertEqual(len(first), 3)
        self.assertEqual(len(second), 3)
        self.assertTrue(np.allclose(first, 0.0))
        self.assertFalse(np.allclose(second, [0.4, 0.5, 0.6]))

    def test_denoiser_preserves_speech_more_than_noise(self):
        effects = AudioEffects()
        effects._enabled = True
        effects._initialized = True
        effects._state = object()
        effects._rnnoise = _MuteWithVadRnnoise([1.0, 0.0])
        effects._frame_size = 4
        effects.intensity = 0.6

        audio = np.full(8, 0.5, dtype=np.float32)
        result = effects.process_chunk(audio)

        speech_frame = result[:4]
        noise_frame = result[4:]
        self.assertGreater(float(np.mean(speech_frame)), float(np.mean(noise_frame)))


if __name__ == "__main__":
    unittest.main()
