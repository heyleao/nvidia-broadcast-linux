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

    def test_transcriber_preload_waits_while_streaming(self):
        fake = SimpleNamespace(
            _meeting_active=False,
            _meeting_finalizing=False,
            _streaming=True,
            _preload_transcriber=mock.Mock(),
        )
        self.assertTrue(NVBroadcastApp._preload_transcriber_when_idle(fake))
        fake._preload_transcriber.assert_not_called()

    def test_transcriber_preload_runs_once_idle(self):
        fake = SimpleNamespace(
            _meeting_active=False,
            _meeting_finalizing=False,
            _streaming=False,
            _preload_transcriber=mock.Mock(),
        )
        self.assertFalse(NVBroadcastApp._preload_transcriber_when_idle(fake))
        fake._preload_transcriber.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
