# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
#
"""Command line setup and service manager for headless mode."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from nvbroadcast.core.config import (
    COMPOSITING_BACKENDS,
    PERFORMANCE_PROFILES,
    apply_performance_profile,
    detect_compositing_backends,
    detect_system_capabilities,
    load_config,
    save_config,
)
from nvbroadcast.core.constants import CONFIG_FILE, DEFAULT_FPS, DEFAULT_HEIGHT, DEFAULT_WIDTH
from nvbroadcast.core.resources import HEADLESS_APP_ICON, find_headless_app_icon
from nvbroadcast.audio.devices import list_microphones, list_speakers
from nvbroadcast.audio.voice_fx import VOICE_PRESETS, get_voice_fx_preset, normalize_voice_fx_preset_name
from nvbroadcast.vcam_service import MODE_MAP


SERVICE_DIR = Path.home() / ".config" / "systemd" / "user"
BIN_DIR = Path.home() / ".local" / "bin"
VCAM_SERVICE = SERVICE_DIR / "nvbroadcast-vcam.service"
AUDIO_SERVICE = SERVICE_DIR / "nvbroadcast-audio.service"
VCAM_BIN = BIN_DIR / "nvbroadcast-vcam"
AUDIO_BIN = BIN_DIR / "nvbroadcast-audio-headless"
CLI_BIN = BIN_DIR / "nvbroadcast-headless"
CONTROL_BIN = BIN_DIR / "nvbroadcast-headless-control"
TRAY_BIN = BIN_DIR / "nvbroadcast-headless-tray"
APPLICATIONS_DIR = Path.home() / ".local" / "share" / "applications"
CONTROL_DESKTOP = APPLICATIONS_DIR / "nvbroadcast-headless-control.desktop"
ICON_DIR = Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps"
HEADLESS_ICON = ICON_DIR / HEADLESS_APP_ICON

SERVICE_ENVIRONMENT = "Environment=GST_PLUGIN_PATH=/usr/lib64/gstreamer-1.0"
VOICE_PARAM_RANGES = {
    "voice_bass": (-1.0, 1.0, "voice_fx_bass_boost"),
    "voice_treble": (-1.0, 1.0, "voice_fx_treble"),
    "voice_warmth": (0.0, 1.0, "voice_fx_warmth"),
    "voice_compression": (0.0, 1.0, "voice_fx_compression"),
    "voice_gate": (0.0, 1.0, "voice_fx_gate_threshold"),
    "voice_gain": (-1.0, 1.0, "voice_fx_gain"),
}


def _run(command: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, capture_output=True, text=True)


def _print_result(label: str, ok: bool, detail: str = "") -> None:
    status = "ok" if ok else "missing"
    suffix = f" - {detail}" if detail else ""
    print(f"{label}: {status}{suffix}")


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _voice_settings_summary(config) -> str:
    a = config.audio
    return (
        f"preset={a.voice_fx_preset}, gpu={a.voice_fx_use_gpu}, "
        f"bass={a.voice_fx_bass_boost:.2f}, treble={a.voice_fx_treble:.2f}, "
        f"warmth={a.voice_fx_warmth:.2f}, compression={a.voice_fx_compression:.2f}, "
        f"gate={a.voice_fx_gate_threshold:.2f}, gain={a.voice_fx_gain:.2f}"
    )


def _apply_voice_preset(config, preset_name: str) -> None:
    normalized = normalize_voice_fx_preset_name(preset_name)
    preset = get_voice_fx_preset(normalized)
    if preset is None:
        valid = ", ".join(sorted(VOICE_PRESETS))
        raise SystemExit(f"Invalid voice preset '{preset_name}'. Valid presets: {valid}")
    config.audio.voice_fx_preset = normalized
    config.audio.voice_fx_bass_boost = preset.bass_boost
    config.audio.voice_fx_treble = preset.treble
    config.audio.voice_fx_warmth = preset.warmth
    config.audio.voice_fx_compression = preset.compression
    config.audio.voice_fx_gate_threshold = preset.gate_threshold
    config.audio.voice_fx_gain = preset.gain


def _print_microphones() -> list[dict[str, str]]:
    microphones = list_microphones()
    print("Available microphones")
    for index, mic in enumerate(microphones, start=1):
        device = mic.get("device", "")
        device_label = device or "(system default)"
        print(f"{index}. {mic.get('name', 'Unknown')} [{device_label}]")
    return microphones


def _print_speakers() -> list[dict[str, str]]:
    speakers = list_speakers()
    print("Available speakers")
    for index, speaker in enumerate(speakers, start=1):
        device = speaker.get("device", "")
        device_label = device or "(system default)"
        print(f"{index}. {speaker.get('name', 'Unknown')} [{device_label}]")
    return speakers


def _python_bin() -> str:
    return sys.executable


def _module_wrapper(module: str, *module_args: str) -> str:
    python = _python_bin()
    extra_args = " ".join(module_args)
    if extra_args:
        extra_args = f" {extra_args}"
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'exec "{python}" -m {module}{extra_args} "$@"\n'
    )


def _systemctl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return _run(["systemctl", "--user", *args])


def phase1_doctor(_args: argparse.Namespace) -> int:
    """Inspect host capabilities and service state."""
    caps = detect_system_capabilities()
    backends = detect_compositing_backends()

    print("Phase 1 - Doctor")
    print(f"Config: {CONFIG_FILE}")
    print(f"GPU: {caps['gpu_name']} ({caps['gpu_vram_mb']} MB)")
    _print_result("NVIDIA", bool(caps["has_nvidia"]))
    _print_result("CuPy", bool(backends.get("cupy")))
    _print_result("GStreamer GL", bool(backends.get("gstreamer_gl")))
    _print_result("v4l2loopback", Path("/dev/video10").exists(), "/dev/video10")
    _print_result("systemd user", shutil.which("systemctl") is not None)

    for service in ("nvbroadcast-vcam.service", "nvbroadcast-audio.service"):
        result = _systemctl(["is-active", service])
        print(f"{service}: {result.stdout.strip() or result.stderr.strip() or 'unknown'}")
    return 0


def _show_config() -> None:
    config = load_config()
    print("Current headless config")
    print(f"mode: {config.mode_key or '(profile)'}")
    print(f"profile: {config.performance_profile}")
    print(f"compositing: {config.compositing}")
    print(f"tensorrt: {config.use_tensorrt}")
    print(f"fused_kernel: {config.use_fused_kernel}")
    print(f"nvdec: {config.use_nvdec}")
    print(f"camera: {config.video.camera_device}")
    print(f"resolution: {config.video.width}x{config.video.height}@{config.video.fps}")
    print(f"background_removal: {config.video.background_removal}")
    print(f"background_mode: {config.video.background_mode}")
    print(f"mirror: {config.video.mirror}")
    print(f"mic: {config.audio.mic_device or '(default)'}")
    print(f"speaker: {config.audio.speaker_device or '(default)'}")
    print(f"noise_removal: {config.audio.noise_removal}")
    print(f"noise_intensity: {int(round(config.audio.noise_intensity * 100))}%")
    print(f"voice_fx_enabled: {config.audio.voice_fx_enabled}")
    print(f"voice_fx: {_voice_settings_summary(config)}")


def _apply_mode(config, mode: str) -> None:
    if mode not in MODE_MAP:
        valid = ", ".join(sorted(MODE_MAP))
        raise SystemExit(f"Invalid mode '{mode}'. Valid modes: {valid}")
    profile, compositing, tensorrt, fused, nvdec = MODE_MAP[mode]
    apply_performance_profile(config, profile)
    config.mode_key = mode
    config.compositing = compositing
    config.use_tensorrt = tensorrt
    config.use_fused_kernel = fused
    config.use_nvdec = nvdec


def phase2_config(args: argparse.Namespace) -> int:
    """Show or update saved headless configuration."""
    config = load_config()
    changed = False

    if args.list_mics:
        _print_microphones()
        return 0
    if args.list_speakers:
        _print_speakers()
        return 0

    if args.show:
        _show_config()
        return 0

    if args.mode:
        _apply_mode(config, args.mode)
        changed = True
    if args.profile:
        apply_performance_profile(config, args.profile)
        config.mode_key = ""
        changed = True
    if args.compositing:
        if args.compositing not in COMPOSITING_BACKENDS:
            raise SystemExit(f"Invalid compositing backend: {args.compositing}")
        config.compositing = args.compositing
        config.mode_key = ""
        changed = True
    if args.camera:
        config.video.camera_device = args.camera
        changed = True
    if args.width:
        config.video.width = args.width
        changed = True
    if args.height:
        config.video.height = args.height
        changed = True
    if args.fps:
        config.video.fps = args.fps
        changed = True
    if args.background is not None:
        config.video.background_removal = args.background == "on"
        changed = True
    if args.background_mode:
        config.video.background_mode = args.background_mode
        changed = True
    if args.mirror is not None:
        config.video.mirror = args.mirror == "on"
        changed = True
    if args.mic is not None:
        config.audio.mic_device = args.mic
        changed = True
    if args.mic_index is not None:
        microphones = list_microphones()
        if args.mic_index < 1 or args.mic_index > len(microphones):
            raise SystemExit(
                f"Invalid microphone index {args.mic_index}. "
                f"Use --list-mics to see valid values."
            )
        config.audio.mic_device = microphones[args.mic_index - 1].get("device", "")
        changed = True
    if args.speaker is not None:
        config.audio.speaker_device = args.speaker
        changed = True
    if args.speaker_index is not None:
        speakers = list_speakers()
        if args.speaker_index < 1 or args.speaker_index > len(speakers):
            raise SystemExit(
                f"Invalid speaker index {args.speaker_index}. "
                f"Use --list-speakers to see valid values."
            )
        config.audio.speaker_device = speakers[args.speaker_index - 1].get("device", "")
        changed = True
    if args.noise is not None:
        config.audio.noise_removal = args.noise == "on"
        changed = True
    if args.noise_intensity is not None:
        config.audio.noise_intensity = _clamp(args.noise_intensity, 0.0, 1.0)
        changed = True
    if args.voice_fx is not None:
        config.audio.voice_fx_enabled = args.voice_fx == "on"
        changed = True
    if args.voice_preset:
        _apply_voice_preset(config, args.voice_preset)
        changed = True
    if args.voice_gpu is not None:
        config.audio.voice_fx_use_gpu = args.voice_gpu == "on"
        changed = True
    for arg_name, (minimum, maximum, config_name) in VOICE_PARAM_RANGES.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            setattr(config.audio, config_name, _clamp(value, minimum, maximum))
            changed = True

    if not changed:
        _show_config()
        print("")
        print("Use --help to see editable fields.")
        return 0

    save_config(config)
    print(f"Saved config: {CONFIG_FILE}")
    _show_config()
    return 0


def _write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(0o755)


def _write_service(path: Path, description: str, exec_path: Path, after: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "[Unit]",
                f"Description={description}",
                f"After={after}",
                "PartOf=graphical-session.target",
                "",
                "[Service]",
                "Type=simple",
                f"ExecStart={exec_path}",
                "Restart=on-failure",
                "RestartSec=3",
                "TimeoutStopSec=5",
                "KillMode=mixed",
                SERVICE_ENVIRONMENT,
                "",
                "[Install]",
                "WantedBy=graphical-session.target",
                "",
            ]
        )
    )


def phase3_install(args: argparse.Namespace) -> int:
    """Install or remove user services."""
    if args.remove:
        for service in ("nvbroadcast-vcam.service", "nvbroadcast-audio.service"):
            _systemctl(["disable", "--now", service])
        for path in (
            VCAM_SERVICE,
            AUDIO_SERVICE,
            VCAM_BIN,
            AUDIO_BIN,
            CLI_BIN,
            CONTROL_BIN,
            TRAY_BIN,
            CONTROL_DESKTOP,
            HEADLESS_ICON,
        ):
            if path.exists():
                path.unlink()
        _systemctl(["daemon-reload"])
        print("Removed headless services and wrappers.")
        return 0

    _write_executable(VCAM_BIN, _module_wrapper("nvbroadcast.vcam_service", "--on-demand"))
    _write_executable(AUDIO_BIN, _module_wrapper("nvbroadcast.audio_service"))
    _write_executable(CLI_BIN, _module_wrapper("nvbroadcast.headless_cli"))
    _write_executable(CONTROL_BIN, _module_wrapper("nvbroadcast.headless_control"))
    _write_executable(TRAY_BIN, _module_wrapper("nvbroadcast.headless_tray"))
    icon = find_headless_app_icon()
    if icon is not None:
        ICON_DIR.mkdir(parents=True, exist_ok=True)
        if icon.resolve() != HEADLESS_ICON.resolve():
            shutil.copyfile(icon, HEADLESS_ICON)
    APPLICATIONS_DIR.mkdir(parents=True, exist_ok=True)
    CONTROL_DESKTOP.write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                "Name=NV Broadcast Headless Control",
                "Comment=Control NVIDIA Broadcast headless camera and microphone services",
                f"Exec={CONTROL_BIN}",
                "Icon=com.doczeus.NVBroadcast.Headless",
                "Terminal=false",
                "Categories=AudioVideo;",
                "StartupNotify=true",
                "",
            ]
        )
    )
    _write_service(
        VCAM_SERVICE,
        "NVIDIA Broadcast Headless Virtual Camera",
        VCAM_BIN,
        "graphical-session.target",
    )
    _write_service(
        AUDIO_SERVICE,
        "NVIDIA Broadcast Headless Virtual Microphone",
        AUDIO_BIN,
        "pipewire.service pipewire-pulse.service wireplumber.service",
    )
    _systemctl(["daemon-reload"])
    if args.enable:
        _systemctl(["enable", "--now", "nvbroadcast-vcam.service"])
        _systemctl(["enable", "--now", "nvbroadcast-audio.service"])
    print("Installed headless wrappers and user services.")
    if args.enable:
        print("Services enabled and started.")
    else:
        print("Run 'nvbroadcast-headless phase4 start' to start services.")
    return 0


def phase4_operate(args: argparse.Namespace) -> int:
    """Operate installed services."""
    services = ["nvbroadcast-vcam.service", "nvbroadcast-audio.service"]
    if args.action == "status":
        for service in services:
            result = _systemctl(["status", service, "--no-pager"])
            print(result.stdout or result.stderr)
        return 0
    if args.action == "logs":
        command = ["journalctl", "--user", "-u", "nvbroadcast-vcam.service", "-u", "nvbroadcast-audio.service", "-n", str(args.lines), "--no-pager"]
        result = _run(command)
        print(result.stdout or result.stderr)
        return result.returncode
    systemctl_action = {
        "start": "start",
        "stop": "stop",
        "restart": "restart",
        "enable": "enable",
        "disable": "disable",
    }[args.action]
    extra = ["--now"] if args.action in {"enable", "disable"} else []
    for service in services:
        result = _systemctl([systemctl_action, *extra, service])
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            return result.returncode
    print(f"Services: {args.action}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nvbroadcast-headless",
        description="Phased CLI for NVIDIA Broadcast headless camera/mic services.",
    )
    sub = parser.add_subparsers(dest="phase", required=True)

    p1 = sub.add_parser("phase1", help="doctor: inspect dependencies and services")
    p1.set_defaults(func=phase1_doctor)

    p2 = sub.add_parser("phase2", help="config: show or update saved settings")
    p2.add_argument("--show", action="store_true", help="show current config")
    p2.add_argument("--mode", choices=sorted(MODE_MAP), help="headless mode preset")
    p2.add_argument("--profile", choices=sorted(PERFORMANCE_PROFILES), help="performance profile")
    p2.add_argument("--compositing", choices=sorted(COMPOSITING_BACKENDS), help="compositing backend")
    p2.add_argument("--camera", help="source camera device, for example /dev/video0")
    p2.add_argument("--width", type=int, default=0, help=f"video width, default {DEFAULT_WIDTH}")
    p2.add_argument("--height", type=int, default=0, help=f"video height, default {DEFAULT_HEIGHT}")
    p2.add_argument("--fps", type=int, default=0, help=f"frames per second, default {DEFAULT_FPS}")
    p2.add_argument("--background", choices=["on", "off"], help="enable background processing")
    p2.add_argument("--background-mode", choices=["blur", "replace", "remove"], help="background mode")
    p2.add_argument("--mirror", choices=["on", "off"], help="mirror camera output")
    p2.add_argument("--list-mics", action="store_true", help="list available source microphones")
    p2.add_argument("--mic", help="source microphone device; empty string uses system default")
    p2.add_argument("--mic-index", type=int, help="select a microphone from --list-mics, starting at 1")
    p2.add_argument("--list-speakers", action="store_true", help="list available speaker outputs")
    p2.add_argument("--speaker", help="speaker output device; empty string uses system default")
    p2.add_argument("--speaker-index", type=int, help="select a speaker from --list-speakers, starting at 1")
    p2.add_argument("--noise", choices=["on", "off"], help="enable microphone noise removal")
    p2.add_argument("--noise-intensity", type=float, help="noise removal intensity, 0.0 to 1.0")
    p2.add_argument("--voice-fx", choices=["on", "off"], help="enable microphone voice processing")
    p2.add_argument("--voice-preset", choices=sorted(VOICE_PRESETS), help="voice preset")
    p2.add_argument("--voice-gpu", choices=["on", "off"], help="use GPU for voice processing when available")
    p2.add_argument("--voice-bass", type=float, help="bass cut/boost, -1.0 to 1.0")
    p2.add_argument("--voice-treble", type=float, help="treble cut/boost, -1.0 to 1.0")
    p2.add_argument("--voice-warmth", type=float, help="warmth/saturation, 0.0 to 1.0")
    p2.add_argument("--voice-compression", type=float, help="dynamic compression, 0.0 to 1.0")
    p2.add_argument("--voice-gate", type=float, help="noise gate threshold, 0.0 to 1.0")
    p2.add_argument("--voice-gain", type=float, help="output gain, -1.0 to 1.0")
    p2.set_defaults(func=phase2_config)

    p3 = sub.add_parser("phase3", help="install: install/remove user services")
    p3.add_argument("--enable", action="store_true", help="enable and start services after installing")
    p3.add_argument("--remove", action="store_true", help="remove wrappers and user services")
    p3.set_defaults(func=phase3_install)

    p4 = sub.add_parser("phase4", help="operate: start/stop/restart/status/logs")
    p4.add_argument("action", choices=["start", "stop", "restart", "status", "logs", "enable", "disable"])
    p4.add_argument("--lines", type=int, default=120, help="lines for logs action")
    p4.set_defaults(func=phase4_operate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
