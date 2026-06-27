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
        list_mics=False,
        mic="alsa_input.test",
        mic_index=None,
        list_speakers=False,
        speaker="alsa_output.test",
        speaker_index=None,
        noise="on",
        noise_intensity=1.5,
        voice_fx="on",
        voice_preset="Podcast",
        voice_gpu="off",
        voice_bass=None,
        voice_treble=None,
        voice_warmth=0.4,
        voice_compression=None,
        voice_gate=None,
        voice_gain=-2.0,
    )

    assert cli.phase2_config(args) == 0
    assert saved["config"].mode_key == "zeus"
    assert saved["config"].compositing == "cupy"
    assert saved["config"].video.camera_device == "/dev/video2"
    assert saved["config"].video.background_mode == "remove"
    assert saved["config"].video.mirror is False
    assert saved["config"].audio.mic_device == "alsa_input.test"
    assert saved["config"].audio.speaker_device == "alsa_output.test"
    assert saved["config"].audio.noise_removal is True
    assert saved["config"].audio.noise_intensity == 1.0
    assert saved["config"].audio.voice_fx_enabled is True
    assert saved["config"].audio.voice_fx_preset == "Podcast"
    assert saved["config"].audio.voice_fx_use_gpu is False
    assert saved["config"].audio.voice_fx_warmth == 0.4
    assert saved["config"].audio.voice_fx_gain == -1.0


def test_phase2_lists_microphones(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "list_microphones",
        lambda: [
            {"name": "USB Mic", "device": "alsa_input.usb"},
            {"name": "Analog Mic", "device": "alsa_input.analog"},
        ],
    )

    args = SimpleNamespace(list_mics=True, show=False)

    assert cli.phase2_config(args) == 0
    output = capsys.readouterr().out
    assert "1. USB Mic [alsa_input.usb]" in output
    assert "2. Analog Mic [alsa_input.analog]" in output


def test_phase2_lists_speakers(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "list_speakers",
        lambda: [
            {"name": "Headset", "device": "alsa_output.usb"},
            {"name": "Line Out", "device": "alsa_output.analog"},
        ],
    )

    args = SimpleNamespace(list_mics=False, list_speakers=True, show=False)

    assert cli.phase2_config(args) == 0
    output = capsys.readouterr().out
    assert "1. Headset [alsa_output.usb]" in output
    assert "2. Line Out [alsa_output.analog]" in output


def test_phase2_selects_microphone_by_index(monkeypatch):
    config = AppConfig()
    saved = {}

    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "save_config", lambda cfg: saved.setdefault("config", cfg))
    monkeypatch.setattr(
        cli,
        "list_microphones",
        lambda: [
            {"name": "USB Mic", "device": "alsa_input.usb"},
            {"name": "Analog Mic", "device": "alsa_input.analog"},
        ],
    )

    args = SimpleNamespace(
        show=False,
        list_mics=False,
        list_speakers=False,
        mode=None,
        profile=None,
        compositing=None,
        camera=None,
        width=0,
        height=0,
        fps=0,
        background=None,
        background_mode=None,
        mirror=None,
        mic=None,
        mic_index=2,
        speaker=None,
        speaker_index=None,
        noise=None,
        noise_intensity=None,
        voice_fx=None,
        voice_preset=None,
        voice_gpu=None,
        voice_bass=None,
        voice_treble=None,
        voice_warmth=None,
        voice_compression=None,
        voice_gate=None,
        voice_gain=None,
    )

    assert cli.phase2_config(args) == 0
    assert saved["config"].audio.mic_device == "alsa_input.analog"


def test_phase2_selects_speaker_by_index(monkeypatch):
    config = AppConfig()
    saved = {}

    monkeypatch.setattr(cli, "load_config", lambda: config)
    monkeypatch.setattr(cli, "save_config", lambda cfg: saved.setdefault("config", cfg))
    monkeypatch.setattr(
        cli,
        "list_speakers",
        lambda: [
            {"name": "Headset", "device": "alsa_output.usb"},
            {"name": "Line Out", "device": "alsa_output.analog"},
        ],
    )

    args = SimpleNamespace(
        show=False,
        list_mics=False,
        list_speakers=False,
        mode=None,
        profile=None,
        compositing=None,
        camera=None,
        width=0,
        height=0,
        fps=0,
        background=None,
        background_mode=None,
        mirror=None,
        mic=None,
        mic_index=None,
        speaker=None,
        speaker_index=1,
        noise=None,
        noise_intensity=None,
        voice_fx=None,
        voice_preset=None,
        voice_gpu=None,
        voice_bass=None,
        voice_treble=None,
        voice_warmth=None,
        voice_compression=None,
        voice_gate=None,
        voice_gain=None,
    )

    assert cli.phase2_config(args) == 0
    assert saved["config"].audio.speaker_device == "alsa_output.usb"


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
