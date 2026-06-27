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
gi.require_version("Gst", "1.0")
from gi.repository import Adw, Gio, GLib, Gst, Gtk

from nvbroadcast.audio.devices import list_microphones, list_speakers
from nvbroadcast.audio.voice_fx import VOICE_PRESETS, get_voice_fx_preset
from nvbroadcast.core.config import apply_performance_profile, load_config, save_config
from nvbroadcast.core.constants import APP_ID
from nvbroadcast.vcam_service import MODE_MAP


APP_CONTROL_ID = f"{APP_ID}.HeadlessControl"
VCAM_SERVICE = "nvbroadcast-vcam.service"
AUDIO_SERVICE = "nvbroadcast-audio.service"
VIRTUAL_MIC_SOURCE = "nvbroadcast_mic"
FORK_RELEASES_URL = "https://github.com/heyleao/nvidia-broadcast-linux/releases/latest"

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


def _pactl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["pactl", *args], capture_output=True, text=True)


def _monitor_loopback_modules() -> list[str]:
    result = _pactl(["list", "modules", "short"])
    if result.returncode != 0:
        return []
    modules = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[1] == "module-loopback" and f"source={VIRTUAL_MIC_SOURCE}" in parts[2]:
            modules.append(parts[0])
    return modules


def _unload_monitor_loopbacks() -> bool:
    ok = True
    for module_id in _monitor_loopback_modules():
        result = _pactl(["unload-module", module_id])
        ok = ok and result.returncode == 0
    return ok


class HeadlessLogsWindow(Gtk.Window):
    def __init__(self, parent: "HeadlessControlWindow"):
        super().__init__(application=parent.get_application(), title="Logs NV Broadcast")
        self._parent = parent
        self.set_default_size(760, 460)
        self._process: subprocess.Popen[str] | None = None

        header = Gtk.HeaderBar()
        header.set_show_title_buttons(True)
        title = Gtk.Label(label="Logs NV Broadcast")
        title.add_css_class("heading")
        header.set_title_widget(title)
        self.set_titlebar(header)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        root.set_margin_start(12)
        root.set_margin_end(12)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        toolbar.set_halign(Gtk.Align.END)
        clear = Gtk.Button(label="Limpar")
        close = Gtk.Button(label="Fechar")
        clear.connect("clicked", self._on_clear)
        close.connect("clicked", lambda _button: self.close())
        toolbar.append(clear)
        toolbar.append(close)
        root.append(toolbar)

        self._buffer = Gtk.TextBuffer()
        self._view = Gtk.TextView(buffer=self._buffer)
        self._view.set_editable(False)
        self._view.set_monospace(True)
        self._view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        scroller.set_child(self._view)
        root.append(scroller)

        self.set_child(root)
        self.connect("close-request", self._on_close_request)
        self._start_tail()

    def _on_clear(self, _button) -> None:
        self._buffer.set_text("")

    def _append_line(self, line: str) -> bool:
        end = self._buffer.get_end_iter()
        self._buffer.insert(end, line)
        mark = self._buffer.create_mark(None, end, False)
        self._view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        self._buffer.delete_mark(mark)
        return False

    def _start_tail(self) -> None:
        command = [
            "journalctl",
            "--user",
            "-u",
            VCAM_SERVICE,
            "-u",
            AUDIO_SERVICE,
            "-n",
            "120",
            "-f",
            "--no-pager",
        ]
        try:
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            self._append_line(f"Falha ao abrir logs: {exc}\n")
            return

        def reader() -> None:
            if self._process is None or self._process.stdout is None:
                return
            for line in self._process.stdout:
                GLib.idle_add(self._append_line, line)

        threading.Thread(target=reader, daemon=True).start()

    def _stop_tail(self) -> None:
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    def _on_close_request(self, _window):
        self._stop_tail()
        self._parent._logs_window = None
        return False


class AudioLevelMeter(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        Gst.init(None)
        self._pipeline: Gst.Pipeline | None = None
        self._bus = None
        self._active = False

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label(label="Nivel do microfone")
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        self._peak_label = Gtk.Label(label="sem sinal")
        self._peak_label.set_halign(Gtk.Align.END)
        header.append(label)
        header.append(self._peak_label)
        self.append(header)

        self._bar = Gtk.LevelBar()
        self._bar.set_min_value(0.0)
        self._bar.set_max_value(1.0)
        self._bar.add_offset_value("low", 0.35)
        self._bar.add_offset_value("high", 0.75)
        self._bar.add_offset_value("full", 0.95)
        self._bar.set_value(0.0)
        self.append(self._bar)

    def start(self) -> None:
        if self._active:
            return
        try:
            self._pipeline = Gst.parse_launch(
                f"pulsesrc device={VIRTUAL_MIC_SOURCE} ! "
                "audioconvert ! audioresample ! "
                "level interval=100000000 post-messages=true ! "
                "fakesink sync=false"
            )
        except GLib.Error:
            self._peak_label.set_label("indisponivel")
            self._bar.set_value(0.0)
            return

        self._bus = self._pipeline.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect("message::element", self._on_level_message)
        self._bus.connect("message::error", self._on_error)
        ret = self._pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            self.stop()
            self._peak_label.set_label("indisponivel")
            return
        self._active = True

    def stop(self) -> None:
        if self._bus is not None:
            try:
                self._bus.remove_signal_watch()
            except Exception:
                pass
            self._bus = None
        if self._pipeline is not None:
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
        self._active = False
        self._bar.set_value(0.0)
        self._peak_label.set_label("sem sinal")

    def _on_error(self, _bus, _message) -> None:
        self.stop()
        self._peak_label.set_label("erro")

    def _on_level_message(self, _bus, message) -> None:
        structure = message.get_structure()
        if structure is None or structure.get_name() != "level":
            return
        peak_db = self._first_db_value(structure.get_value("peak"))
        if peak_db is None:
            peak_db = self._first_db_value(structure.get_value("rms"))
        if peak_db is None:
            return

        value = self._db_to_level(peak_db)
        self._bar.set_value(value)
        if peak_db <= -59.5:
            self._peak_label.set_label("-60 dB")
        else:
            self._peak_label.set_label(f"{peak_db:.0f} dB")

    @staticmethod
    def _first_db_value(values) -> float | None:
        if values is None:
            return None
        try:
            return max(float(value) for value in values)
        except TypeError:
            try:
                return float(values)
            except (TypeError, ValueError):
                return None
        except ValueError:
            return None

    @staticmethod
    def _db_to_level(db_value: float) -> float:
        if db_value <= -60.0:
            return 0.0
        if db_value >= 0.0:
            return 1.0
        return (db_value + 60.0) / 60.0


class HeadlessSettingsWindow(Gtk.Window):
    def __init__(self, parent: "HeadlessControlWindow"):
        super().__init__(application=parent.get_application(), title="Configurar NV Broadcast")
        self._parent = parent
        self.set_default_size(520, 720)
        self.set_resizable(True)
        self._config = load_config()

        header = Gtk.HeaderBar()
        header.set_show_title_buttons(True)
        title_widget = Gtk.Label(label="Configurar NV Broadcast")
        title_widget.add_css_class("heading")
        header.set_title_widget(title_widget)
        self.set_titlebar(header)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(18)
        root.set_margin_bottom(18)
        root.set_margin_start(18)
        root.set_margin_end(18)

        title = Gtk.Label(label="Configuracao headless")
        title.add_css_class("title-2")
        title.set_halign(Gtk.Align.START)
        root.append(title)

        root.append(self._section("Camera"))

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

        root.append(self._section("Microfone e voz"))

        self._mic_combo = Gtk.ComboBoxText()
        self._mic_map = self._populate_device_combo(
            self._mic_combo,
            list_microphones(),
            self._config.audio.mic_device,
            "Entrada padrao do sistema",
        )
        root.append(self._row("Entrada de audio", self._mic_combo))

        self._speaker_combo = Gtk.ComboBoxText()
        self._speaker_map = self._populate_device_combo(
            self._speaker_combo,
            list_speakers(),
            self._config.audio.speaker_device,
            "Saida padrao do sistema",
        )
        root.append(self._row("Saida de audio", self._speaker_combo))

        self._noise = Gtk.Switch()
        self._noise.set_active(bool(self._config.audio.noise_removal))
        self._noise.connect("notify::active", self._on_noise_toggled)
        root.append(self._row("Remocao de ruido do mic", self._noise))

        self._noise_intensity = self._percent_scale(self._config.audio.noise_intensity)
        root.append(self._row("Quantidade de reducao (%)", self._noise_intensity))
        self._sync_noise_controls()

        self._voice_fx = Gtk.Switch()
        self._voice_fx.set_active(bool(self._config.audio.voice_fx_enabled))
        self._voice_fx.connect("notify::active", self._on_voice_fx_toggled)
        root.append(self._row("Processamento de voz", self._voice_fx))

        self._voice_preset = Gtk.ComboBoxText()
        for preset_name in sorted(VOICE_PRESETS):
            self._voice_preset.append(preset_name, preset_name)
        self._voice_preset.set_active_id(self._config.audio.voice_fx_preset)
        self._voice_preset.connect("changed", self._on_voice_preset_changed)
        root.append(self._row("Preset de voz", self._voice_preset))

        self._voice_gpu = Gtk.Switch()
        self._voice_gpu.set_active(bool(self._config.audio.voice_fx_use_gpu))
        root.append(self._row("Usar GPU na voz", self._voice_gpu))

        audio = self._config.audio
        self._voice_sliders = {
            "bass_boost": self._scale(-1.0, 1.0, audio.voice_fx_bass_boost),
            "treble": self._scale(-1.0, 1.0, audio.voice_fx_treble),
            "warmth": self._scale(0.0, 1.0, audio.voice_fx_warmth),
            "compression": self._scale(0.0, 1.0, audio.voice_fx_compression),
            "gate_threshold": self._scale(0.0, 1.0, audio.voice_fx_gate_threshold),
            "gain": self._scale(-1.0, 1.0, audio.voice_fx_gain),
        }
        root.append(self._row("Graves", self._voice_sliders["bass_boost"]))
        root.append(self._row("Agudos", self._voice_sliders["treble"]))
        root.append(self._row("Calor", self._voice_sliders["warmth"]))
        root.append(self._row("Compressao", self._voice_sliders["compression"]))
        root.append(self._row("Gate de ruido", self._voice_sliders["gate_threshold"]))
        root.append(self._row("Ganho de saida", self._voice_sliders["gain"]))
        self._sync_voice_controls()

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions.set_halign(Gtk.Align.END)
        cancel = Gtk.Button(label="Cancelar")
        apply = Gtk.Button(label="Aplicar")
        save = Gtk.Button(label="Salvar e fechar")
        save.add_css_class("suggested-action")
        cancel.connect("clicked", lambda _button: self.close())
        apply.connect("clicked", self._on_apply)
        save.connect("clicked", self._on_save)
        actions.append(cancel)
        actions.append(apply)
        actions.append(save)
        root.append(actions)

        scroller = Gtk.ScrolledWindow()
        scroller.set_child(root)
        self.set_child(scroller)

    def _section(self, label: str) -> Gtk.Label:
        text = Gtk.Label(label=label)
        text.add_css_class("heading")
        text.set_halign(Gtk.Align.START)
        text.set_margin_top(8)
        return text

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

    def _scale(self, minimum: float, maximum: float, value: float) -> Gtk.Scale:
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, minimum, maximum, 0.01)
        scale.set_value(value)
        scale.set_digits(2)
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_hexpand(False)
        scale.set_size_request(230, -1)
        return scale

    def _percent_scale(self, value: float) -> Gtk.Scale:
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 100.0, 1.0)
        scale.set_value(max(0.0, min(100.0, value * 100.0)))
        scale.set_digits(0)
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_hexpand(False)
        scale.set_size_request(230, -1)
        return scale

    def _populate_device_combo(
        self,
        combo: Gtk.ComboBoxText,
        devices: list[dict[str, str]],
        selected_device: str,
        default_label: str,
    ) -> dict[str, str]:
        device_map = {"__default__": ""}
        combo.append("__default__", default_label)
        active_id = "__default__"
        seen = {""}
        for index, device in enumerate(devices, start=1):
            device_id = device.get("device", "")
            if device_id in seen:
                continue
            seen.add(device_id)
            row_id = f"device:{index}"
            name = device.get("name", device_id or "Dispositivo")
            combo.append(row_id, name)
            device_map[row_id] = device_id
            if device_id == selected_device:
                active_id = row_id
        if selected_device and selected_device not in seen:
            combo.append("__saved__", f"Salvo: {selected_device}")
            device_map["__saved__"] = selected_device
            active_id = "__saved__"
        combo.set_active_id(active_id)
        return device_map

    def _selected_device(self, combo: Gtk.ComboBoxText, device_map: dict[str, str]) -> str:
        return device_map.get(combo.get_active_id() or "__default__", "")

    def _sync_voice_controls(self) -> None:
        enabled = self._voice_fx.get_active()
        self._voice_preset.set_sensitive(enabled)
        self._voice_gpu.set_sensitive(enabled)
        for slider in self._voice_sliders.values():
            slider.set_sensitive(enabled)

    def _sync_noise_controls(self) -> None:
        self._noise_intensity.set_sensitive(self._noise.get_active())

    def _on_noise_toggled(self, _switch, _param) -> None:
        self._sync_noise_controls()

    def _on_voice_fx_toggled(self, _switch, _param) -> None:
        self._sync_voice_controls()

    def _on_voice_preset_changed(self, combo) -> None:
        preset = get_voice_fx_preset(combo.get_active_id())
        if preset is None:
            return
        self._voice_sliders["bass_boost"].set_value(preset.bass_boost)
        self._voice_sliders["treble"].set_value(preset.treble)
        self._voice_sliders["warmth"].set_value(preset.warmth)
        self._voice_sliders["compression"].set_value(preset.compression)
        self._voice_sliders["gate_threshold"].set_value(preset.gate_threshold)
        self._voice_sliders["gain"].set_value(preset.gain)

    def _save(self) -> None:
        config = self._config
        mode = self._mode.get_active_id() or "cuda_balanced"
        _apply_mode(config, mode)
        config.video.width = self._width.get_value_as_int()
        config.video.height = self._height.get_value_as_int()
        config.video.fps = self._fps.get_value_as_int()
        config.video.background_removal = self._background.get_active()
        config.video.background_mode = self._background_mode.get_active_id() or "blur"
        config.video.mirror = self._mirror.get_active()
        config.audio.mic_device = self._selected_device(self._mic_combo, self._mic_map)
        config.audio.speaker_device = self._selected_device(self._speaker_combo, self._speaker_map)
        config.audio.noise_removal = self._noise.get_active()
        config.audio.noise_intensity = self._noise_intensity.get_value() / 100.0
        config.audio.voice_fx_enabled = self._voice_fx.get_active()
        config.audio.voice_fx_preset = self._voice_preset.get_active_id() or "Flat"
        config.audio.voice_fx_use_gpu = self._voice_gpu.get_active()
        config.audio.voice_fx_bass_boost = self._voice_sliders["bass_boost"].get_value()
        config.audio.voice_fx_treble = self._voice_sliders["treble"].get_value()
        config.audio.voice_fx_warmth = self._voice_sliders["warmth"].get_value()
        config.audio.voice_fx_compression = self._voice_sliders["compression"].get_value()
        config.audio.voice_fx_gate_threshold = self._voice_sliders["gate_threshold"].get_value()
        config.audio.voice_fx_gain = self._voice_sliders["gain"].get_value()
        save_config(config)
        self._parent.apply_saved_config()

    def _on_apply(self, _button):
        self._save()

    def _on_save(self, _button):
        self._save()
        self.close()


class HeadlessControlWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Adw.Application):
        super().__init__(application=app, title="NV Broadcast Headless")
        self.set_default_size(380, 520)
        self.set_resizable(True)
        self.connect("close-request", self._on_close_request)
        self._monitor_module_id: str | None = None
        self._logs_window: HeadlessLogsWindow | None = None

        header = Gtk.HeaderBar()
        header.set_show_title_buttons(True)
        title_widget = Gtk.Label(label="NV Broadcast Headless")
        title_widget.add_css_class("heading")
        header.set_title_widget(title_widget)
        self.set_titlebar(header)

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

        self._level_meter = AudioLevelMeter()
        root.append(self._level_meter)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        grid.set_column_homogeneous(True)
        root.append(grid)

        self._both_btn = Gtk.Button(label="Cam + Mic")
        self._cam_btn = Gtk.Button(label="Cam")
        self._mic_btn = Gtk.Button(label="Mic")
        self._off_btn = Gtk.Button(label="Desligar")
        self._restart_btn = Gtk.Button(label="Reiniciar")
        self._monitor_btn = Gtk.Button(label="Ouvir mic")
        self._logs_btn = Gtk.Button(label="Logs")
        self._settings_btn = Gtk.Button(label="Configurar")
        self._update_btn = Gtk.Button(label="Atualizar")
        self._minimize_btn = Gtk.Button(label="Minimizar")
        self._quit_btn = Gtk.Button(label="Quit")

        grid.attach(self._both_btn, 0, 0, 2, 1)
        grid.attach(self._cam_btn, 0, 1, 1, 1)
        grid.attach(self._mic_btn, 1, 1, 1, 1)
        grid.attach(self._restart_btn, 0, 2, 1, 1)
        grid.attach(self._off_btn, 1, 2, 1, 1)
        grid.attach(self._monitor_btn, 0, 3, 2, 1)
        grid.attach(self._logs_btn, 0, 4, 2, 1)
        grid.attach(self._settings_btn, 0, 5, 2, 1)
        grid.attach(self._update_btn, 0, 6, 2, 1)
        grid.attach(self._minimize_btn, 0, 7, 2, 1)
        grid.attach(self._quit_btn, 0, 8, 2, 1)

        self._both_btn.connect("clicked", self._on_both)
        self._cam_btn.connect("clicked", self._on_cam)
        self._mic_btn.connect("clicked", self._on_mic)
        self._off_btn.connect("clicked", self._on_off)
        self._restart_btn.connect("clicked", self._on_restart)
        self._monitor_btn.connect("clicked", self._on_monitor)
        self._logs_btn.connect("clicked", self._on_logs)
        self._settings_btn.connect("clicked", self._on_settings)
        self._update_btn.connect("clicked", self._on_update)
        self._minimize_btn.connect("clicked", self._on_minimize)
        self._quit_btn.connect("clicked", self._on_quit)

        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_child(root)
        self.set_child(self._toast_overlay)

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
            self._monitor_btn,
            self._logs_btn,
            self._settings_btn,
            self._update_btn,
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
        self._set_services(cam=True, mic=False)

    def _on_mic(self, _button):
        self._set_services(cam=False, mic=True)

    def _on_off(self, _button):
        self._set_services(cam=False, mic=False)

    def _on_restart(self, _button):
        self._run_actions(
            [(VCAM_SERVICE, "restart"), (AUDIO_SERVICE, "restart")],
            "Servicos reiniciados",
        )

    def _on_logs(self, _button):
        if self._logs_window is None:
            self._logs_window = HeadlessLogsWindow(self)
        self._logs_window.present()

    def _on_monitor(self, _button):
        if self._monitor_module_id or _monitor_loopback_modules():
            self._stop_audio_monitor()
        else:
            self._start_audio_monitor()

    def _start_audio_monitor(self) -> None:
        if not _active(AUDIO_SERVICE):
            self._toast("Ligue o microfone antes de ouvir o retorno")
            return
        config = load_config()
        sink = config.audio.speaker_device or "@DEFAULT_SINK@"
        result = _pactl(
            [
                "load-module",
                "module-loopback",
                f"source={VIRTUAL_MIC_SOURCE}",
                f"sink={sink}",
                "latency_msec=60",
            ]
        )
        if result.returncode != 0:
            self._toast(result.stderr.strip() or "Falha ao ativar retorno do mic")
            return
        self._monitor_module_id = result.stdout.strip()
        self._monitor_btn.set_label("Parar retorno")
        self._toast("Retorno do microfone ativado")

    def _stop_audio_monitor(self) -> None:
        self._monitor_module_id = None
        if not _unload_monitor_loopbacks():
            self._toast("Falha ao desligar retorno do mic")
        self._monitor_btn.set_label("Ouvir mic")

    def _on_settings(self, _button):
        HeadlessSettingsWindow(self).present()

    def _on_update(self, _button):
        try:
            Gio.AppInfo.launch_default_for_uri(FORK_RELEASES_URL, None)
            self._toast("Abrindo releases do fork")
        except Exception as exc:
            self._toast(f"Falha ao abrir update: {exc}")

    def _on_close_request(self, _window):
        self.set_visible(False)
        return True

    def _on_minimize(self, _button):
        self.set_visible(False)

    def _on_quit(self, _button):
        self._stop_audio_monitor()
        self._level_meter.stop()
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
        if mic:
            self._level_meter.start()
        else:
            self._level_meter.stop()
        self._cam_btn.set_sensitive(not (cam and not mic))
        self._mic_btn.set_sensitive(not (mic and not cam))
        self._both_btn.set_sensitive(not (cam and mic))
        self._off_btn.set_sensitive(cam or mic)
        self._monitor_btn.set_label("Parar retorno" if _monitor_loopback_modules() else "Ouvir mic")
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
