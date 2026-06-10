# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
# Original author: doczeus | AI Powered
#
"""Headless virtual camera service with video effects.

Runs the saved camera/effects configuration without starting the GTK UI:

    physical camera -> VideoPipeline -> VideoEffects -> /dev/video10

This keeps OBS/browser integrations stable while preserving the same
background removal mode used by the full application.
"""

import argparse
import signal
import sys

import cv2
import gi
import numpy as np

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst

from nvbroadcast.core.config import PERFORMANCE_PROFILES, load_config
from nvbroadcast.core.constants import (
    DEFAULT_FPS,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    VIRTUAL_CAM_DEVICE,
)
from nvbroadcast.video.effects import VideoEffects
from nvbroadcast.video.pipeline import VideoPipeline
from nvbroadcast.video.virtual_camera import ensure_virtual_camera, list_camera_devices


OUTPUT_FORMATS = {
    "yuy2": "YUY2",
    "yuyv": "YUY2",
    "i420": "I420",
    "yuv420": "I420",
    "nv12": "NV12",
}

MODE_MAP = {
    "doczeus": ("max_quality", "cupy", False, True, False),
    "cuda_max": ("max_quality", "cupy", False, False, False),
    "cuda_balanced": ("balanced", "cupy", False, False, False),
    "zeus": ("balanced", "cupy", True, False, False),
    "killer": ("performance", "cupy", True, True, True),
    "cuda_perf": ("performance", "cupy", False, True, False),
    "cpu_quality": ("max_quality", "cpu", False, False, False),
    "cpu_light": ("performance", "cpu", False, False, False),
    "cpu_low": ("potato", "cpu", False, False, False),
}

MODE_QUALITY_PRESETS = {
    "doczeus": "quality",
    "cuda_max": "quality",
    "cuda_balanced": "balanced",
    "zeus": "balanced",
    "killer": "performance",
    "cuda_perf": "performance",
    "cpu_quality": "quality",
    "cpu_light": "performance",
    "cpu_low": "performance",
}


class HeadlessEffectsCamera:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.config = load_config()
        self.loop = GLib.MainLoop()
        self.pipeline: VideoPipeline | None = None
        self.effects: VideoEffects | None = None
        self.inline_inference = False
        self.use_nvdec = False

    def _resolve_mode(self) -> tuple[str, str, bool, bool, bool]:
        mode_key = self.config.mode_key or ""
        if mode_key in MODE_MAP:
            return MODE_MAP[mode_key]
        return (
            self.config.performance_profile,
            self.config.compositing,
            bool(self.config.use_tensorrt),
            bool(self.config.use_fused_kernel),
            bool(self.config.use_nvdec),
        )

    def _profile_infer_height(
        self,
        profile_name: str,
        *,
        use_tensorrt: bool,
        use_fused_kernel: bool,
    ) -> int:
        profile = PERFORMANCE_PROFILES.get(profile_name, {})
        scale = float(profile.get("process_scale", 1.0))
        source_h = max(1, int(self.config.video.height))
        infer_h = int(round(source_h * scale)) & ~1
        infer_h = max(240, min(720, infer_h))
        if profile_name == "performance" and use_fused_kernel and not use_tensorrt:
            infer_h = min(source_h, max(480, infer_h))
        return infer_h

    def _effects_fps(self, profile_name: str) -> int:
        profile = PERFORMANCE_PROFILES.get(profile_name, {})
        ratio = float(profile.get("effects_ratio", 1.0))
        return max(5, int(ratio * int(self.config.video.fps)))

    def _configure_effects(self) -> None:
        profile_name, compositing, use_tensorrt, use_fused_kernel, use_nvdec = self._resolve_mode()
        mode_key = self.config.mode_key or ""
        quality = MODE_QUALITY_PRESETS.get(mode_key, self.config.video.quality_preset)

        self.use_nvdec = use_nvdec
        self.inline_inference = profile_name in ("max_quality", "balanced")

        effects = VideoEffects(
            gpu_index=int(self.config.compute_gpu),
            edge_config=self.config.video.edge,
            compositing=compositing,
        )
        effects.set_model(self.config.video.model)
        effects.quality = quality
        effects.set_engine_mode(use_tensorrt, use_fused_kernel)
        effects.set_profile_infer_height(
            self._profile_infer_height(
                profile_name,
                use_tensorrt=use_tensorrt,
                use_fused_kernel=use_fused_kernel,
            )
        )
        profile = PERFORMANCE_PROFILES.get(profile_name, {})
        effects._skip_interval = profile.get("skip_interval", 1)
        effects._apply_edge_config(self.config.video.edge)
        effects._edge_refine_enabled = (
            bool(self.config.premium_edge_refine) and mode_key in ("killer", "zeus")
        )

        effects.mode = self.config.video.background_mode
        effects.intensity = float(self.config.video.blur_intensity)
        if self.config.video.background_image:
            effects.set_background_image(self.config.video.background_image)
        effects.enabled = bool(self.config.video.background_removal)
        self.effects = effects

        print(
            "[NVIDIA Broadcast VCam] Effects: "
            f"mode={mode_key or profile_name} profile={profile_name} "
            f"quality={quality} trt={use_tensorrt} fused={use_fused_kernel} "
            f"compositing={compositing} inline={self.inline_inference}",
            flush=True,
        )

    def _update_alpha(self, frame_data: bytes, width: int, height: int) -> None:
        if self.effects is not None:
            self.effects.update_alpha(frame_data, width, height)

    def _process_frame(self, frame_data: bytes, width: int, height: int) -> bytes:
        if self.effects is None or not self.effects.enabled:
            return frame_data

        frame = np.frombuffer(frame_data, dtype=np.uint8).reshape(height, width, 4)
        if not frame.flags.writeable:
            frame = frame.copy()

        if self.inline_inference:
            result = self.effects.process_frame_array(frame, width, height)
        else:
            result = self.effects.composite_only_array(frame, width, height)

        if self.config.video.mirror:
            result = cv2.flip(result, 1)
        return result.tobytes()

    def _resolve_source_device(self) -> str:
        source_device = self.args.device or self.config.video.camera_device
        if not source_device or source_device == "/dev/video0":
            cameras = list_camera_devices()
            if cameras:
                print(
                    "[NVIDIA Broadcast VCam] Auto-detected camera: "
                    f"{cameras[0]['name']} ({cameras[0]['device']})",
                    flush=True,
                )
                return cameras[0]["device"]
            return "/dev/video0"
        return source_device

    def start(self) -> None:
        Gst.init(None)
        self._configure_effects()

        source_device = self._resolve_source_device()
        vcam_device = self.args.vcam
        width = self.args.width or self.config.video.width or DEFAULT_WIDTH
        height = self.args.height or self.config.video.height or DEFAULT_HEIGHT
        fps = self.args.fps or self.config.video.fps or DEFAULT_FPS
        output_format = OUTPUT_FORMATS.get(self.args.format.lower(), "YUY2")
        profile_name, *_ = self._resolve_mode()

        try:
            vcam_device = ensure_virtual_camera()
        except RuntimeError as e:
            print(f"[NVIDIA Broadcast VCam] Error: {e}", file=sys.stderr)
            raise SystemExit(1) from e

        print(f"[NVIDIA Broadcast VCam] Source: {source_device} ({width}x{height}@{fps}fps)")
        print(f"[NVIDIA Broadcast VCam] Virtual camera: {vcam_device} ({output_format})")

        pipeline = VideoPipeline()
        pipeline.configure(
            source_device=source_device,
            vcam_device=vcam_device,
            width=width,
            height=height,
            fps=fps,
            output_format=output_format,
            effects_fps=self._effects_fps(profile_name),
            prefer_hw_decode=self.use_nvdec,
        )
        pipeline.set_effect_callback(self._process_frame)
        pipeline.set_alpha_callback(self._update_alpha)
        pipeline.set_alpha_worker_enabled(not self.inline_inference)
        if self.effects is not None and self.effects.enabled:
            pipeline._effects_active = True

        pipeline.build(vcam_enabled=True)
        pipeline.start()
        self.pipeline = pipeline

        print("[NVIDIA Broadcast VCam] Streaming with saved effects config", flush=True)

    def stop(self) -> None:
        if self.pipeline is not None:
            self.pipeline.shutdown_sync()
            self.pipeline = None
        if self.effects is not None:
            self.effects.cleanup()
            self.effects = None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="NVIDIA Broadcast Virtual Camera Service - headless effects pipeline"
    )
    parser.add_argument("--device", "-d", help="Source camera device")
    parser.add_argument(
        "--vcam",
        default=VIRTUAL_CAM_DEVICE,
        help=f"Virtual camera device (default: {VIRTUAL_CAM_DEVICE})",
    )
    parser.add_argument("--width", "-W", type=int, default=0, help="Video width")
    parser.add_argument("--height", "-H", type=int, default=0, help="Video height")
    parser.add_argument("--fps", type=int, default=0, help="Frames per second")
    parser.add_argument(
        "--format",
        "-f",
        choices=list(OUTPUT_FORMATS.keys()),
        default="yuy2",
        help="Output pixel format (default: yuy2)",
    )
    args = parser.parse_args()

    service = HeadlessEffectsCamera(args)

    def shutdown(_signum, _frame):
        print("\n[NVIDIA Broadcast VCam] Shutting down...", flush=True)
        service.stop()
        service.loop.quit()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    service.start()
    try:
        service.loop.run()
    finally:
        service.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
