# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
#
"""GTK3 AppIndicator tray helper for the headless control app.

The headless control window is GTK4/libadwaita. AppIndicator menus are GTK3, so
the tray runs in a tiny helper process to avoid mixing GTK3 and GTK4 in the same
Python process.
"""

from __future__ import annotations

import fcntl
import os
import signal
import shutil
import subprocess
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3 as AppIndicator
from gi.repository import GLib, Gtk

from nvbroadcast.core.resources import find_app_icon


VCAM_SERVICE = "nvbroadcast-vcam.service"
AUDIO_SERVICE = "nvbroadcast-audio.service"


def _systemctl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["systemctl", "--user", *args],
        capture_output=True,
        text=True,
    )


def _active(service: str) -> bool:
    return _systemctl(["is-active", "--quiet", service]).returncode == 0


def _lock() -> object | None:
    runtime_candidates = [
        Path(os.environ["XDG_RUNTIME_DIR"])
        for key in ("XDG_RUNTIME_DIR",)
        if os.environ.get(key)
    ]
    runtime_candidates.append(Path.home() / ".cache")

    lock_file = None
    for runtime_dir in runtime_candidates:
        try:
            runtime_dir.mkdir(parents=True, exist_ok=True)
            lock_file = (runtime_dir / "nvbroadcast-headless-tray.lock").open("w")
            break
        except OSError:
            continue
    if lock_file is None:
        return None

    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return None
    return lock_file


class HeadlessTray:
    def __init__(self):
        icon = find_app_icon()
        if icon is None:
            raise RuntimeError("NV Broadcast icon not found")

        self._indicator = AppIndicator.Indicator.new(
            "nvbroadcast-headless-control",
            str(icon),
            AppIndicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self._indicator.set_menu(self._build_menu())
        self._refresh()
        GLib.timeout_add_seconds(3, self._refresh)

    def _build_menu(self) -> Gtk.Menu:
        menu = Gtk.Menu()

        open_item = Gtk.MenuItem(label="Abrir controle")
        open_item.connect("activate", self._on_open_control)
        menu.append(open_item)

        menu.append(Gtk.SeparatorMenuItem())

        self._both_item = Gtk.MenuItem(label="Cam + Mic")
        self._cam_item = Gtk.MenuItem(label="Somente camera")
        self._mic_item = Gtk.MenuItem(label="Somente microfone")
        self._off_item = Gtk.MenuItem(label="Desligar")
        self._restart_item = Gtk.MenuItem(label="Reiniciar")

        self._both_item.connect("activate", lambda _item: self._set_services(cam=True, mic=True))
        self._cam_item.connect("activate", lambda _item: self._set_services(cam=True, mic=False))
        self._mic_item.connect("activate", lambda _item: self._set_services(cam=False, mic=True))
        self._off_item.connect("activate", lambda _item: self._set_services(cam=False, mic=False))
        self._restart_item.connect("activate", self._on_restart)

        menu.append(self._both_item)
        menu.append(self._cam_item)
        menu.append(self._mic_item)
        menu.append(self._off_item)
        menu.append(self._restart_item)

        menu.append(Gtk.SeparatorMenuItem())

        self._status_item = Gtk.MenuItem(label="Camera: ... | Mic: ...")
        self._status_item.set_sensitive(False)
        menu.append(self._status_item)

        logs_item = Gtk.MenuItem(label="Logs")
        logs_item.connect("activate", self._on_logs)
        menu.append(logs_item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="Sair da bandeja")
        quit_item.connect("activate", self._on_quit)
        menu.append(quit_item)

        menu.show_all()
        return menu

    def _on_open_control(self, _item) -> None:
        command = shutil.which("nvbroadcast-headless-control")
        if command:
            subprocess.Popen([command])
            return
        subprocess.Popen([sys.executable, "-m", "nvbroadcast.headless_control"])

    def _set_services(self, *, cam: bool, mic: bool) -> None:
        actions = [
            (VCAM_SERVICE, "start" if cam else "stop"),
            (AUDIO_SERVICE, "start" if mic else "stop"),
        ]
        for service, action in actions:
            _systemctl([action, service])
        self._refresh()

    def _on_restart(self, _item) -> None:
        for service in (VCAM_SERVICE, AUDIO_SERVICE):
            _systemctl(["restart", service])
        self._refresh()

    def _on_logs(self, _item) -> None:
        terminals = (
            ["cosmic-term", "-e"],
            ["kgx", "-e"],
            ["konsole", "-e"],
            ["x-terminal-emulator", "-e"],
        )
        command = "journalctl --user -u nvbroadcast-vcam.service -u nvbroadcast-audio.service -f"
        for terminal in terminals:
            try:
                subprocess.Popen([*terminal, command])
                return
            except FileNotFoundError:
                continue

    def _on_quit(self, _item) -> None:
        parent_pid = os.getppid()
        try:
            cmdline = Path(f"/proc/{parent_pid}/cmdline").read_text().replace("\x00", " ")
            if "nvbroadcast.headless_control" in cmdline:
                os.kill(parent_pid, signal.SIGTERM)
        except Exception:
            pass
        Gtk.main_quit()

    def _refresh(self):
        cam = _active(VCAM_SERVICE)
        mic = _active(AUDIO_SERVICE)
        self._status_item.set_label(
            f"Camera: {'ativa' if cam else 'desligada'} | "
            f"Mic: {'ativo' if mic else 'desligado'}"
        )
        self._both_item.set_sensitive(not (cam and mic))
        self._cam_item.set_sensitive(not (cam and not mic))
        self._mic_item.set_sensitive(not (mic and not cam))
        self._off_item.set_sensitive(cam or mic)
        return True


def main() -> int:
    lock_file = _lock()
    if lock_file is None:
        return 0
    Gtk.init(sys.argv)
    try:
        HeadlessTray()
    except Exception as exc:
        print(f"[NV Broadcast Headless Tray] {exc}", file=sys.stderr)
        return 1
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
