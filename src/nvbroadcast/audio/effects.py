# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
# Original author: doczeus
#
"""Audio noise removal using RNNoise.

Real-time GPU-accelerated noise suppression for microphone input.
Uses Mozilla's RNNoise via pyrnnoise (low-level C API).
"""

import numpy as np

from nvbroadcast.core.constants import MAXINE_AFX_PATH


class AudioEffects:
    """Real-time audio noise removal.

    Uses RNNoise algorithm: processes 480-sample frames (10ms at 48kHz)
    of int16 PCM audio.
    """

    def __init__(self, gpu_index: int = 1):
        self._gpu_index = gpu_index
        self._initialized = False
        self._state = None  # ctypes pointer to RNNoise state
        self._enabled = False
        self._intensity = 1.0
        self._pending_input = np.empty(0, dtype=np.float32)
        self._processed_output = np.empty(0, dtype=np.float32)
        self._speech_protection = 0.65
        self._noise_floor_boost = 0.2

    @property
    def available(self) -> bool:
        return self._initialized

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        if self._enabled != value:
            self._reset_frame_buffers()
        self._enabled = value
        if value and not self._initialized:
            self.initialize()

    @property
    def intensity(self) -> float:
        return self._intensity

    @intensity.setter
    def intensity(self, value: float):
        self._intensity = max(0.0, min(1.0, value))

    def initialize(self) -> bool:
        """Initialize the noise removal engine."""
        if self._initialized:
            return True

        try:
            from pyrnnoise import rnnoise
            self._rnnoise = rnnoise
            self._state = rnnoise.create()
            self._frame_size = rnnoise.FRAME_SIZE  # 480 samples
            self._initialized = True
            print("[NVIDIA Broadcast] Audio denoiser initialized (RNNoise)")
            return True
        except Exception as e:
            print(f"[NVIDIA Broadcast] Failed to initialize audio denoiser: {e}")
            return False

    def process_chunk(self, audio_data: np.ndarray, sample_rate: int = 48000) -> np.ndarray:
        """Process an audio chunk through the denoiser.

        Args:
            audio_data: Float32 mono audio samples
            sample_rate: Sample rate (48000 required for RNNoise)

        Returns:
            Denoised float32 audio samples
        """
        if not self._enabled or not self._initialized:
            return audio_data

        try:
            clean_input = np.nan_to_num(
                audio_data.astype(np.float32, copy=False),
                nan=0.0,
                posinf=0.98,
                neginf=-0.98,
            )
            peak = float(np.max(np.abs(clean_input))) if clean_input.size else 0.0
            if peak > 0.98:
                clean_input = clean_input * (0.98 / peak)

            output = np.zeros_like(clean_input)
            total_samples = len(clean_input)
            fs = self._frame_size  # 480
            if self._pending_input.size:
                process_input = np.concatenate((self._pending_input, clean_input))
            else:
                process_input = clean_input
            process_samples = (len(process_input) // fs) * fs
            processed_frames = np.empty(0, dtype=np.float32)

            if process_samples > 0:
                processed_frames = np.zeros(process_samples, dtype=np.float32)

            for i in range(0, process_samples, fs):
                frame = process_input[i:i + fs]

                # Convert float32 -> int16 for RNNoise
                frame_int16 = (frame * 32767).clip(-32768, 32767).astype(np.int16)

                # Process through RNNoise
                denoised_int16, vad_prob = self._rnnoise.process_mono_frame(
                    self._state, frame_int16
                )

                # Convert back to float32
                denoised = denoised_int16.astype(np.float32) / 32767.0

                mix = self._adaptive_mix(vad_prob)
                if mix < 1.0:
                    denoised = mix * denoised + (1 - mix) * frame

                processed_frames[i:i + fs] = np.clip(denoised, -0.98, 0.98)

            self._pending_input = process_input[process_samples:].copy()
            if processed_frames.size:
                if self._processed_output.size:
                    self._processed_output = np.concatenate((self._processed_output, processed_frames))
                else:
                    self._processed_output = processed_frames

            available = min(total_samples, len(self._processed_output))
            if available > 0:
                output[:available] = self._processed_output[:available]
                self._processed_output = self._processed_output[available:].copy()

            return output.astype(np.float32, copy=False)

        except Exception as e:
            print(f"[NVIDIA Broadcast] Audio processing error: {e}")
            return audio_data

    def _adaptive_mix(self, vad_prob: float) -> float:
        """Scale denoise amount by RNNoise speech probability.

        A linear wet/dry blend makes the useful range very narrow: enough
        denoise for keyboard noise can over-process speech. RNNoise exposes a
        VAD score, so keep speech drier and pauses/noise wetter.
        """
        try:
            vad = max(0.0, min(1.0, float(vad_prob)))
        except (TypeError, ValueError):
            vad = 0.0

        speech_preserve = self._speech_protection * vad
        noise_boost = self._noise_floor_boost * (1.0 - vad)
        return max(0.0, min(1.0, self._intensity * (1.0 - speech_preserve + noise_boost)))

    def _reset_frame_buffers(self) -> None:
        self._pending_input = np.empty(0, dtype=np.float32)
        self._processed_output = np.empty(0, dtype=np.float32)

    def cleanup(self):
        """Release resources."""
        self._reset_frame_buffers()
        if self._state is not None:
            try:
                self._rnnoise.destroy(self._state)
            except Exception:
                pass
            self._state = None
        self._initialized = False
