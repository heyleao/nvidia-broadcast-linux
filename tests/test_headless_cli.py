from pathlib import Path
from types import SimpleNamespace

import nvbroadcast.headless_cli as cli
from nvbroadcast.core.config import AppConfig


def test_phase2_applies_mode_and_saved_config(monkeypatch):
    config = AppConfig()
    saved = {}

    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "save_config", lambda cfg: saved.setdefault("config", cfg))

    args = SimpleNamespace(
        show=False,
        mode="zeus",
        profile=None,
        compositing=None,
        camera="/dev/video2",
        width=640,
        height=360,
        fps=30,
        background="on",
        background_mode="remove",
        mirror="off",
        mic="alsa_input.test",
        noise="on",
        voice_fx="off",
    )

    assert cli.phase2_config(args) == 0
    assert saved["config"].mode_key == "zeus"
    assert saved["config"].compositing == "cupy"
    assert saved["config"].video.camera_device == "/dev/video2"
    assert saved["config"].video.background_mode == "remove"
    assert saved["config"].video.mirror is False
    assert saved["config"].audio.mic_device == "alsa_input.test"
    assert saved["config"].audio.noise_removal is True
    assert saved["config"].audio.voice_fx_enabled is False


def test_phase3_install_writes_wrappers_services_and_desktop(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "SERVICE_DIR", tmp_path / "systemd")
    monkeypatch.setattr(cli, "BIN_DIR", tmp_path / "bin")
    monkeypatch.setattr(cli, "APPLICATIONS_DIR", tmp_path / "applications")
    monkeypatch.setattr(cli, "VCAM_SERVICE", tmp_path / "systemd" / "nvbroadcast-vcam.service")
    monkeypatch.setattr(cli, "AUDIO_SERVICE", tmp_path / "systemd" / "nvbroadcast-audio.service")
    monkeypatch.setattr(cli, "VCAM_BIN", tmp_path / "bin" / "nvbroadcast-vcam")
    monkeypatch.setattr(cli, "AUDIO_BIN", tmp_path / "bin" / "nvbroadcast-audio-headless")
    monkeypatch.setattr(cli, "CLI_BIN", tmp_path / "bin" / "nvbroadcast-headless")
    monkeypatch.setattr(cli, "CONTROL_BIN", tmp_path / "bin" / "nvbroadcast-headless-control")
    monkeypatch.setattr(
        cli,
        "CONTROL_DESKTOP",
        tmp_path / "applications" / "nvbroadcast-headless-control.desktop",
    )
    monkeypatch.setattr(
        cli,
        "_systemctl",
        lambda args: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    assert cli.phase3_install(SimpleNamespace(remove=False, enable=False)) == 0

    assert cli.VCAM_BIN.exists()
    assert cli.AUDIO_BIN.exists()
    assert cli.CLI_BIN.exists()
    assert cli.CONTROL_BIN.exists()
    assert cli.VCAM_SERVICE.exists()
    assert cli.AUDIO_SERVICE.exists()
    assert cli.CONTROL_DESKTOP.exists()

    desktop = Path(cli.CONTROL_DESKTOP).read_text()
    assert "NV Broadcast Headless Control" in desktop
    assert "Categories=AudioVideo;" in desktop
