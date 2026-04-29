import unittest
from unittest import mock
from types import SimpleNamespace

from nvbroadcast.app import NVBroadcastApp
from nvbroadcast.core.config import AppConfig


class AutoCaptureTuningTests(unittest.TestCase):
    def test_next_lower_capture_mode_steps_down_one_supported_mode(self):
        app = NVBroadcastApp.__new__(NVBroadcastApp)
        app.config = AppConfig()
        app.config.video.camera_device = "/dev/video0"
        app.config.video.width = 1280
        app.config.video.height = 720
        app.config.video.fps = 30

        modes = [
            {"width": 640, "height": 360, "fps": [30]},
            {"width": 800, "height": 600, "fps": [30]},
            {"width": 1280, "height": 720, "fps": [30]},
        ]

        with mock.patch("nvbroadcast.video.virtual_camera.list_camera_modes", return_value=modes):
            self.assertEqual(app._next_lower_capture_mode(), (800, 600, 30))

    def test_heavy_face_stack_prefers_async_alpha_even_on_max_quality(self):
        app = NVBroadcastApp.__new__(NVBroadcastApp)
        app.config = AppConfig()
        app.config.performance_profile = "max_quality"
        app.config.use_tensorrt = False
        app._video_effects = SimpleNamespace(enabled=True, mode="replace")
        app._beautifier = SimpleNamespace(enabled=True)
        app._eye_contact = SimpleNamespace(enabled=True)
        app._relighter = SimpleNamespace(enabled=True)
        app._autoframe = SimpleNamespace(enabled=False)

        self.assertFalse(app._compute_inline_inference())

    def test_tensorrt_keep_inline_alpha_for_replace_mode(self):
        app = NVBroadcastApp.__new__(NVBroadcastApp)
        app.config = AppConfig()
        app.config.performance_profile = "max_quality"
        app.config.use_tensorrt = True
        app._video_effects = SimpleNamespace(enabled=True, mode="replace")
        app._beautifier = SimpleNamespace(enabled=True)
        app._eye_contact = SimpleNamespace(enabled=True)
        app._relighter = SimpleNamespace(enabled=True)
        app._autoframe = SimpleNamespace(enabled=False)

        self.assertTrue(app._compute_inline_inference())


if __name__ == "__main__":
    unittest.main()
