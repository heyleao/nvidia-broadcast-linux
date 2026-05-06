import base64
import json
import unittest
from unittest import mock

from nvbroadcast.audio import service


class AudioServiceTests(unittest.TestCase):
    def test_service_stops_when_parent_pid_changes(self):
        state = base64.urlsafe_b64encode(
            json.dumps({"sample_rate": 48000}).encode("utf-8")
        ).decode("ascii")
        fake_pipeline = mock.Mock()
        fake_pipeline._running = True

        fake_event = mock.Mock()
        fake_event.wait.return_value = False

        with mock.patch("nvbroadcast.audio.service._build_pipeline", return_value=fake_pipeline), \
             mock.patch("nvbroadcast.audio.service.threading.Event", return_value=fake_event), \
             mock.patch("nvbroadcast.audio.service.os.getppid", return_value=999):
            rc = service.main(["--state-b64", state, "--parent-pid", "123"])

        self.assertEqual(rc, 0)
        fake_pipeline.start.assert_called_once_with()
        fake_pipeline.stop.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
