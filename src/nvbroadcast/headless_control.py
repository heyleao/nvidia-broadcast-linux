# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
#
"""Small GTK control window for headless services."""

from __future__ import annotations

import shutil
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

from nvbroadcast.core.config import apply_performance_profile, load_config, save_config
from nvbroadcast.core.constants import APP_ID
from nvbroadcast.vcam_service import MODE_MAP


APP_CONTROL_ID = f"{APP_ID}.HeadlessControl"
VCAM_SERVICE = "nvbroadcast-vcam.service"
AUDIO_SERVICE = "nvbroadcast-audio.service"

MODE_LABELS = {
    "doczeus": "DocZeus - qualidade maxima",
    "cuda_max": "CUDA Max - qualidade",
    "cuda_balanced": "CUDA Balanced - recomendado",
    "zeus": "Zeus - TensorRT balanceado",
    "killer": "Killer - max performance",
    "cuda_perf": "CUDA Performance",
    "cpu_quality": "CPU Quality",
    "cpu_light": "CPU Light",
    "cpu_low": "CPU Low",
}


def _apply_mode(config, mode: str) -> None:
    profile, compositing, tensorrt, fused, nvdec = MODE_MAP[mode]
    apply_performance_profile(config, profile)
    config.mode_key = mode
    config.compositing = compositing
    config.use_tensorrt = tensorrt
    config.use_fused_kernel = fused
    config.use_nvdec = nvdec


def _systemctl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["systemctl", "--user", *args],
        capture_output=True,
        text=True,
    )


def _active(service: str) -> bool:
    return _systemctl(["is-active", "--quiet", service]).returncode == 0


class HeadlessSettingsWindow(Adw.Window):
    def __init__(self, parent: "HeadlessControlWindow"):
        super().__init__(title="Configurar NV Broadcast", transient_for=parent, modal=True)
        self._parent = parent
        self.set_default_size(420, 520)
        self.set_resizable(False)
        self._config = load_config()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(18)
        root.set_margin_bottom(18)
        root.set_margin_start(18)
        root.set_margin_end(18)

        title = Gtk.Label(label="Configuracao headless")
        title.add_css_class("title-2")
        title.set_halign(Gtk.Align.START)
        root.append(title)

        self._mode = Gtk.ComboBoxText()
        for mode in MODE_MAP:
            self._mode.append(mode, MODE_LABELS.get(mode, mode))
        self._mode.set_active_id(self._config.mode_key or "cuda_balanced")
        root.append(self._row("Modo", self._mode))

        self._width = Gtk.SpinButton.new_with_range(320, 3840, 2)
        self._width.set_value(self._config.video.width)
        root.append(self._row("Largura", self._width))

        self._height = Gtk.SpinButton.new_with_range(180, 2160, 2)
        self._height.set_value(self._config.video.height)
        root.append(self._row("Altura", self._height))

        self._fps = Gtk.SpinButton.new_with_range(5, 120, 1)
        self._fps.set_value(self._config.video.fps)
        root.append(self._row("FPS", self._fps))

        self._background = Gtk.Switch()
        self._background.set_active(bool(self._config.video.background_removal))
        root.append(self._row("Remover fundo", self._background))

        self._background_mode = Gtk.ComboBoxText()
        for key, label in (
            ("remove", "Remover"),
            ("blur", "Desfocar"),
            ("replace", "Substituir"),
        ):
            self._background_mode.append(key, label)
        self._background_mode.set_active_id(self._config.video.background_mode)
        root.append(self._row("Modo do fundo", self._background_mode))

        self._mirror = Gtk.Switch()
        self._mirror.set_active(bool(self._config.video.mirror))
        root.append(self._row("Espelhar camera", self._mirror))

        self._noise = Gtk.Switch()
        self._noise.set_active(bool(self._config.audio.noise_removal))
        root.append(self._row("Remover ruido", self._noise))

        self._voice_fx = Gtk.Switch()
        self._voice_fx.set_active(bool(self._config.audio.voice_fx_enabled))
        root.append(self._row("Voice FX", self._voice_fx))

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions.set_halign(Gtk.Align.END)
        cancel = Gtk.Button(label="Cancelar")
        save = Gtk.Button(label="Salvar")
        save.add_css_class("suggested-action")
        cancel.connect("clicked", lambda _button: self.close())
        save.connect("clicked", self._on_save)
        actions.append(cancel)
        actions.append(save)
        root.append(actions)

        self.set_content(root)

    def _row(self, label: str, widget: Gtk.Widget) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.set_valign(Gtk.Align.CENTER)
        text = Gtk.Label(label=label)
        text.set_halign(Gtk.Align.START)
        text.set_hexpand(True)
        widget.set_halign(Gtk.Align.END)
        row.append(text)
        row.append(widget)
        return row

    def _on_save(self, _button):
        config = self._config
        mode = self._mode.get_active_id() or "cuda_balanced"
        _apply_mode(config, mode)
        config.video.width = self._width.get_value_as_int()
        config.video.height = self._height.get_value_as_int()
        config.video.fps = self._fps.get_value_as_int()
        config.video.background_removal = self._background.get_active()
        config.video.background_mode = self._background_mode.get_active_id() or "blur"
        config.video.mirror = self._mirror.get_active()
        config.audio.noise_removal = self._noise.get_active()
        config.audio.voice_fx_enabled = self._voice_fx.get_active()
        save_config(config)
        self._parent.apply_saved_config()
        self.close()


class HeadlessControlWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="NV Broadcast Headless")
        self.set_default_size(360, 390)
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
        self._settings_btn = Gtk.Button(label="Configurar")
        self._minimize_btn = Gtk.Button(label="Minimizar")
        self._quit_btn = Gtk.Button(label="Quit")

        grid.attach(self._both_btn, 0, 0, 2, 1)
        grid.attach(self._cam_btn, 0, 1, 1, 1)
        grid.attach(self._mic_btn, 1, 1, 1, 1)
        grid.attach(self._restart_btn, 0, 2, 1, 1)
        grid.attach(self._off_btn, 1, 2, 1, 1)
        grid.attach(self._logs_btn, 0, 3, 2, 1)
        grid.attach(self._settings_btn, 0, 4, 2, 1)
        grid.attach(self._minimize_btn, 0, 5, 2, 1)
        grid.attach(self._quit_btn, 0, 6, 2, 1)

        self._both_btn.connect("clicked", self._on_both)
        self._cam_btn.connect("clicked", self._on_cam)
        self._mic_btn.connect("clicked", self._on_mic)
        self._off_btn.connect("clicked", self._on_off)
        self._restart_btn.connect("clicked", self._on_restart)
        self._logs_btn.connect("clicked", self._on_logs)
        self._settings_btn.connect("clicked", self._on_settings)
        self._minimize_btn.connect("clicked", self._on_minimize)
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
            self._settings_btn,
            self._minimize_btn,
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

    def _on_settings(self, _button):
        HeadlessSettingsWindow(self).present()

    def _on_close_request(self, _window):
        self.set_visible(False)
        return True

    def _on_minimize(self, _button):
        self.set_visible(False)

    def _on_quit(self, _button):
        app = self.get_application()
        if app is not None:
            app.quit()

    def apply_saved_config(self):
        actions = []
        if _active(VCAM_SERVICE):
            actions.append((VCAM_SERVICE, "restart"))
        if _active(AUDIO_SERVICE):
            actions.append((AUDIO_SERVICE, "restart"))
        if actions:
            self._run_actions(actions, "Configuracao salva e aplicada")
        else:
            self._toast("Configuracao salva")

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
        self._tray_process = None

    def do_startup(self):
        Adw.Application.do_startup(self)
        self._start_tray()

    def do_activate(self):
        if self._window is None:
            self._window = HeadlessControlWindow(self)
        self._window.set_visible(True)
        self._window.present()

    def _start_tray(self) -> None:
        command = shutil.which("nvbroadcast-headless-tray")
        args = [command] if command else [sys.executable, "-m", "nvbroadcast.headless_tray"]
        try:
            self._tray_process = subprocess.Popen(args)
        except Exception as exc:
            print(f"[NV Broadcast Headless] Tray unavailable: {exc}", file=sys.stderr)


def main() -> int:
    app = HeadlessControlApp()
    return app.run([])


if __name__ == "__main__":
    raise SystemExit(main())
