import unittest

import numpy as np

from nvbroadcast.video.relighting import FaceRelighter


class _Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


def _face_landmarks():
    return [
        _Point(0.28, 0.28),
        _Point(0.72, 0.28),
        _Point(0.72, 0.72),
        _Point(0.28, 0.72),
    ]


class FaceRelightingTests(unittest.TestCase):
    def test_fill_light_does_not_darken_face_when_background_is_darker(self):
        frame = np.full((96, 96, 4), 40, dtype=np.uint8)
        frame[:, :, 3] = 255
        frame[24:72, 24:72, :3] = 190

        relighter = FaceRelighter()
        relighter.enabled = True
        relighter.intensity = 1.0
        relighter._bg_luminance = 50.0

        output = relighter.process_frame(frame, landmarks=_face_landmarks())

        before = float(frame[24:72, 24:72, :3].mean())
        after = float(output[24:72, 24:72, :3].mean())
        self.assertGreaterEqual(after, before - 1.0)

    def test_fill_light_brightens_face_when_background_is_brighter(self):
        frame = np.full((96, 96, 4), 60, dtype=np.uint8)
        frame[:, :, 3] = 255
        frame[24:72, 24:72, :3] = 100

        relighter = FaceRelighter()
        relighter.enabled = True
        relighter.intensity = 1.0
        relighter._bg_luminance = 220.0

        output = relighter.process_frame(frame, landmarks=_face_landmarks())

        before = float(frame[24:72, 24:72, :3].mean())
        after = float(output[24:72, 24:72, :3].mean())
        self.assertGreater(after, before + 8.0)

    def test_hairline_taper_reduces_upper_face_mask_strength(self):
        mask = np.ones((20, 20), dtype=np.float32)

        tapered = FaceRelighter._apply_hairline_taper(mask, top=2, face_height=12)

        self.assertLess(float(tapered[2, 10]), float(tapered[10, 10]))
        self.assertGreater(float(tapered[10, 10]), 0.8)

    def test_tone_mask_stays_lower_and_inward_vs_base_mask(self):
        mask = np.ones((24, 24), dtype=np.float32)

        tone_mask = FaceRelighter._build_tone_mask(mask, top=4, face_height=14)

        self.assertLess(float(tone_mask[4, 12]), float(tone_mask[12, 12]))
        self.assertLess(float(tone_mask[6, 1]), float(tone_mask[6, 12]))
        self.assertLess(float(tone_mask[4, 12]), 0.70)


if __name__ == "__main__":
    unittest.main()
