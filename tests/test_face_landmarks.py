import threading
import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from nvbroadcast.video.face_landmarks import SharedFaceLandmarker


def _make_landmarker():
    lm = SharedFaceLandmarker.__new__(SharedFaceLandmarker)
    lm._landmarker = object()
    lm._initialized = True
    lm._last_frame_id = None
    lm._last_result = None
    lm._frames_since_infer = 0
    lm._lock = threading.Lock()
    lm._detect_lock = threading.Lock()
    lm._async_busy = False
    lm._pending_job = None
    lm._pending_frame_id = None
    lm._worker_event = mock.Mock()
    lm._worker_stop = False
    lm._worker_thread = None
    lm._mp = None
    return lm


class FaceLandmarkerTests(unittest.TestCase):
    def test_scale_detection_frame_caps_large_inputs(self):
        frame = np.zeros((576, 1024, 4), dtype=np.uint8)

        scaled = SharedFaceLandmarker._scale_detection_frame(frame)

        self.assertEqual(scaled.shape[:2], (288, 512))

    def test_request_async_replaces_pending_job_with_newest_frame(self):
        lm = _make_landmarker()
        lm._last_result = [SimpleNamespace(x=0.5, y=0.5)]
        frame_a = np.zeros((100, 120, 4), dtype=np.uint8)
        frame_b = np.zeros((100, 120, 4), dtype=np.uint8)

        lm.request_async(frame_a, reuse_frames=1)
        lm.request_async(frame_b, reuse_frames=1)

        self.assertTrue(lm._async_busy)
        self.assertEqual(lm._pending_frame_id, id(frame_b))
        self.assertEqual(lm._pending_job.shape, frame_b.shape)
        self.assertEqual(lm._worker_event.set.call_count, 2)

    def test_detect_returns_cached_result_for_reused_frame_budget(self):
        lm = _make_landmarker()
        cached = [SimpleNamespace(x=0.5, y=0.5)]
        lm._last_result = cached
        frame = np.zeros((100, 120, 4), dtype=np.uint8)

        result = lm.detect(frame, reuse_frames=3)

        self.assertEqual(result, cached)
        self.assertEqual(lm._frames_since_infer, 1)
        self.assertEqual(lm._last_frame_id, id(frame))

    def test_detect_runs_detection_when_reuse_budget_exhausted(self):
        lm = _make_landmarker()
        lm._last_result = [SimpleNamespace(x=0.5, y=0.5)]
        lm._frames_since_infer = 2
        frame = np.zeros((100, 120, 4), dtype=np.uint8)
        expected = [SimpleNamespace(x=0.4, y=0.4)]

        with mock.patch.object(lm, "_run_detection", return_value=expected) as run:
            result = lm.detect(frame, reuse_frames=3)

        self.assertEqual(result, expected)
        run.assert_called_once_with(frame)


if __name__ == "__main__":
    unittest.main()
