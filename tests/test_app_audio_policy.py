import unittest
from types import SimpleNamespace
from unittest import mock

from nvbroadcast.app import NVBroadcastApp


class AppAudioPolicyTests(unittest.TestCase):
    @staticmethod
    def _fake_app(*, noise_removal=False, voice_fx_enabled=False):
        fake = SimpleNamespace(
            config=SimpleNamespace(
                audio=SimpleNamespace(
                    noise_removal=noise_removal,
                    voice_fx_enabled=voice_fx_enabled,
                )
            )
        )
        fake._audio_pipeline_should_publish = lambda: NVBroadcastApp._audio_pipeline_should_publish(fake)
        return fake

    @mock.patch("nvbroadcast.app.has_virtual_mic_backend", return_value=True)
    def test_audio_pipeline_runs_as_passthrough_when_virtual_mic_backend_exists(self, _backend):
        fake = self._fake_app(noise_removal=False, voice_fx_enabled=False)
        self.assertTrue(NVBroadcastApp._audio_pipeline_should_publish(fake))
        self.assertTrue(NVBroadcastApp._audio_pipeline_should_run(fake))

    @mock.patch("nvbroadcast.app.has_virtual_mic_backend", return_value=False)
    def test_audio_pipeline_does_not_run_without_backend_or_effects(self, _backend):
        fake = self._fake_app(noise_removal=False, voice_fx_enabled=False)
        self.assertFalse(NVBroadcastApp._audio_pipeline_should_publish(fake))
        self.assertFalse(NVBroadcastApp._audio_pipeline_should_run(fake))

    @mock.patch("nvbroadcast.app.has_virtual_mic_backend", return_value=False)
    def test_audio_pipeline_runs_without_backend_when_effects_enabled(self, _backend):
        fake = self._fake_app(noise_removal=True, voice_fx_enabled=False)
        self.assertTrue(NVBroadcastApp._audio_pipeline_should_run(fake))


if __name__ == "__main__":
    unittest.main()
