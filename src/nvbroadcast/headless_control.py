# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
#
"""Small GTK control window for headless services."""

from __future__ import annotations

import subprocess
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

from nvbroadcast.core.constants import APP_ID


APP_CONTROL_ID = f"{APP_ID}.HeadlessControl"
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


class HeadlessControlWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="NV Broadcast Headless")
        self.set_default_size(360, 310)
        self.set_resizable(False)
        self.connect("close-request", self._on_close_request)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(18)
        root.set_margin_bottom(18)
        root.set_margin_start(18)
        root.set_margin_end(18)

        title = Gtk.Label(label="NV Broadcast Headless")
        title.add_css_class("title-2")
        title.set_halign(Gtk.Align.START)
        root.append(title)

        self._status = Gtk.Label(label="")
        self._status.set_halign(Gtk.Align.START)
        self._status.set_wrap(True)
        root.append(self._status)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        grid.set_column_homogeneous(True)
        root.append(grid)

        self._both_btn = Gtk.Button(label="Cam + Mic")
        self._cam_btn = Gtk.Button(label="Cam")
        self._mic_btn = Gtk.Button(label="Mic")
        self._off_btn = Gtk.Button(label="Desligar")
        self._restart_btn = Gtk.Button(label="Reiniciar")
        self._logs_btn = Gtk.Button(label="Logs")
        self._quit_btn = Gtk.Button(label="Quit")

        grid.attach(self._both_btn, 0, 0, 2, 1)
        grid.attach(self._cam_btn, 0, 1, 1, 1)
        grid.attach(self._mic_btn, 1, 1, 1, 1)
        grid.attach(self._restart_btn, 0, 2, 1, 1)
        grid.attach(self._off_btn, 1, 2, 1, 1)
        grid.attach(self._logs_btn, 0, 3, 2, 1)
        grid.attach(self._quit_btn, 0, 4, 2, 1)

        self._both_btn.connect("clicked", self._on_both)
        self._cam_btn.connect("clicked", self._on_cam)
        self._mic_btn.connect("clicked", self._on_mic)
        self._off_btn.connect("clicked", self._on_off)
        self._restart_btn.connect("clicked", self._on_restart)
        self._logs_btn.connect("clicked", self._on_logs)
        self._quit_btn.connect("clicked", self._on_quit)

        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_child(root)
        self.set_content(self._toast_overlay)

        self._busy = False
        self._refresh()
        GLib.timeout_add_seconds(3, self._refresh)

    def _toast(self, message: str) -> None:
        self._toast_overlay.add_toast(Adw.Toast.new(message))

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for button in (
            self._both_btn,
            self._cam_btn,
            self._mic_btn,
            self._off_btn,
            self._restart_btn,
            self._logs_btn,
        ):
            button.set_sensitive(not busy)
        if busy:
            self._status.set_label("Aplicando alteracao...")

    def _run_actions(self, actions: list[tuple[str, str]], done_message: str) -> None:
        if self._busy:
            return
        self._set_busy(True)

        def worker():
            errors = []
            for service, action in actions:
                result = _systemctl([action, service])
                if result.returncode != 0:
                    errors.append(result.stderr.strip() or f"{action} failed: {service}")

            def finish():
                self._set_busy(False)
                self._refresh()
                if errors:
                    self._toast(errors[0])
                else:
                    self._toast(done_message)
                return False

            GLib.idle_add(finish)

        threading.Thread(target=worker, daemon=True).start()

    def _set_services(self, *, cam: bool, mic: bool) -> None:
        self._run_actions(
            [
                (VCAM_SERVICE, "start" if cam else "stop"),
                (AUDIO_SERVICE, "start" if mic else "stop"),
            ],
            "Servicos atualizados",
        )

    def _service_action(self, service: str, action: str) -> None:
        result = _systemctl([action, service])
        if result.returncode != 0:
            self._toast(result.stderr.strip() or f"{action} failed: {service}")

    def _on_both(self, _button):
        self._set_services(cam=True, mic=True)

    def _on_cam(self, _button):
        self._set_services(cam=False, mic=True)

    def _on_mic(self, _button):
        self._set_services(cam=True, mic=False)

    def _on_off(self, _button):
        self._set_services(cam=False, mic=False)

    def _on_restart(self, _button):
        self._run_actions(
            [(VCAM_SERVICE, "restart"), (AUDIO_SERVICE, "restart")],
            "Servicos reiniciados",
        )

    def _on_logs(self, _button):
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
        self._toast("Nenhum terminal encontrado para abrir logs")

    def _on_close_request(self, _window):
        self.set_visible(False)
        return True

    def _on_quit(self, _button):
        app = self.get_application()
        if app is not None:
            app.quit()

    def _refresh(self):
        if self._busy:
            return True
        cam = _active(VCAM_SERVICE)
        mic = _active(AUDIO_SERVICE)
        self._status.set_label(
            f"Camera: {'ativa' if cam else 'desligada'}\n"
            f"Microfone: {'ativo' if mic else 'desligado'}"
        )
        self._cam_btn.set_sensitive(not (cam and not mic))
        self._mic_btn.set_sensitive(not (mic and not cam))
        self._both_btn.set_sensitive(not (cam and mic))
        self._off_btn.set_sensitive(cam or mic)
        return True


class HeadlessControlApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_CONTROL_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self._window = None

    def do_activate(self):
        if self._window is None:
            self._window = HeadlessControlWindow(self)
        self._window.set_visible(True)
        self._window.present()


def main() -> int:
    app = HeadlessControlApp()
    return app.run([])


if __name__ == "__main__":
    raise SystemExit(main())
