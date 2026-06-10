# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
#
"""Headless virtual microphone service."""

import signal
import threading

from nvbroadcast.audio.pipeline import AudioPipeline
from nvbroadcast.audio.virtual_mic import create_virtual_mic
from nvbroadcast.audio.voice_fx import VoiceFXSettings
from nvbroadcast.core.config import load_config


def main() -> int:
    stop_event = threading.Event()

    def handle_signal(_signum, _frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    config = load_config()
    audio = config.audio

    if not create_virtual_mic():
        return 1

    pipeline = AudioPipeline(manage_virtual_mic=False, use_helper_process=False)
    pipeline.configure(mic_device=audio.mic_device, sample_rate=48000)
    pipeline.effects.enabled = bool(audio.noise_removal)
    pipeline.effects.intensity = float(audio.noise_intensity)
    pipeline.voice_fx.enabled = bool(audio.voice_fx_enabled)
    pipeline.voice_fx.use_gpu = bool(audio.voice_fx_use_gpu)
    pipeline.voice_fx.settings = VoiceFXSettings(
        bass_boost=float(audio.voice_fx_bass_boost),
        treble=float(audio.voice_fx_treble),
        warmth=float(audio.voice_fx_warmth),
        compression=float(audio.voice_fx_compression),
        gate_threshold=float(audio.voice_fx_gate_threshold),
        gain=float(audio.voice_fx_gain),
    )
    pipeline.build()
    pipeline.start()

    if not pipeline._running:
        return 1

    try:
        while not stop_event.wait(0.5):
            pass
    finally:
        pipeline.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
