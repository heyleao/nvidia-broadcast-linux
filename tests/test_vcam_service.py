import unittest
from unittest import mock

from nvbroadcast.vcam_service import build_pipeline


class VCamServicePipelineTests(unittest.TestCase):
    def test_build_pipeline_uses_raw_source_without_jpeg_decode(self):
        with mock.patch(
            "nvbroadcast.vcam_service.select_camera_capture_format",
            return_value="raw",
        ), mock.patch("nvbroadcast.vcam_service.Gst.parse_launch", return_value=mock.Mock()) as parse_launch:
            build_pipeline("/dev/video1", "/dev/video10", 640, 480, 30, "yuy2")

        pipeline_str = parse_launch.call_args.args[0]
        self.assertIn("video/x-raw,width=640,height=480,framerate=30/1", pipeline_str)
        self.assertNotIn("image/jpeg", pipeline_str)
        self.assertNotIn("jpegdec", pipeline_str)


if __name__ == "__main__":
    unittest.main()
