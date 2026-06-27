<p align="center">
  <img src="data/icons/com.doczeus.NVBroadcast.svg" width="120" alt="NV Broadcast">
</p>

<h1 align="center">NV Broadcast</h1>

<p align="center">
  <strong>by DocZeus | AI Powered</strong>
</p>

<p align="center">
  <a href="https://github.com/Hkshoonya/nvidia-broadcast-linux/stargazers"><img src="https://img.shields.io/github/stars/Hkshoonya/nvidia-broadcast-linux?style=for-the-badge&color=76b900&labelColor=1a1a1a" alt="Stars"></a>
  <a href="https://github.com/Hkshoonya/nvidia-broadcast-linux/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-76b900?style=for-the-badge&labelColor=1a1a1a" alt="License"></a>
  <a href="https://github.com/Hkshoonya/nvidia-broadcast-linux/issues"><img src="https://img.shields.io/github/issues/Hkshoonya/nvidia-broadcast-linux?style=for-the-badge&color=76b900&labelColor=1a1a1a" alt="Issues"></a>
  <a href="https://github.com/Hkshoonya/nvidia-broadcast-linux/actions/workflows/build-packages.yml"><img src="https://img.shields.io/github/actions/workflow/status/Hkshoonya/nvidia-broadcast-linux/build-packages.yml?style=for-the-badge&color=76b900&labelColor=1a1a1a&label=Build" alt="Build"></a>
  <a href="https://github.com/sponsors/Hkshoonya"><img src="https://img.shields.io/badge/Sponsor-DocZeus-76b900?style=for-the-badge&logo=githubsponsors&logoColor=white&labelColor=1a1a1a" alt="Sponsor"></a>
</p>

<p align="center">
  <em>NV Broadcast — Unofficial NV Broadcast and other OS. Open source. GPU accelerated. Built with passion.</em>
</p>

---

## Why I Built This

I left Windows. Millions of Linux users left Windows. But we all missed one thing — **NVIDIA Broadcast**.

That one app that made every video call look professional. Background blur that actually worked. Virtual backgrounds that didn't look like a PowerPoint slide. Noise cancellation that silenced your mechanical keyboard.

On Linux? Nothing. You had to cobble together 5 different tools, fight with v4l2loopback configs, and still get janky edges. **That's over now.**

I built this because I believe Linux users deserve the same broadcast-quality experience. Not a half-baked wrapper. Not a "good enough" hack. A real, proper implementation that uses your NVIDIA GPU to do what NVIDIA Broadcast does on Windows — **but open source, and in some ways, better.**

> *"Not saying this is perfect. But I believe it will be."*
>
> This is fast. This is optimized. And the quality already rivals Windows Broadcast. With the community behind it, we'll surpass it.
>
> **— DocZeus**

---

## What's New

### Headless Services for OBS and Wayland

NV Broadcast can also run as user services without opening the full graphical
preview. This is useful for OBS, COSMIC/Wayland, and streaming setups where the
camera and microphone pipelines should stay alive in the background.

See [Headless Camera and Microphone Services](docs/HEADLESS_SERVICES.md).

### v1.1.11 — OBS Camera Compatibility and Packaging Reliability Patch

- **OBS White Preview Fixed** — The camera pipeline now handles cameras that expose raw video modes instead of MJPEG for the selected resolution
- **Safer Camera Auto-Detection** — Startup now avoids stale, metadata-only, and virtual-loopback camera nodes after reboot, reducing blank preview and “no effects” cases
- **Headless Virtual Camera Fixed Too** — `nvbroadcast-vcam` uses the same camera compatibility path as the main app, so OBS-only workflows get the same fix
- **CUDA Runtime Packaging Fixed** — Source, Debian, RPM, and amd64 Snap installs now use the correct package paths for the CUDA mode runtime
- **Regression Tests Added** — Release checks now cover raw-camera fallback, camera-node filtering, headless virtual camera behavior, and package metadata consistency

> If you are still on `v1.1.10` or older, update to `v1.1.11`. This is the recommended stable patch for OBS camera compatibility and package install reliability.

### v1.1.10 — Live Edge Quality and Compute Control Update

- **Cleaner Live Background Edges** — Background replace is steadier around hair, shoulders, raised hands, and finger gaps during motion
- **Less Edge Cleanup Cost** — The DocZeus/fused CUDA path now uses the same replace-mode foreground cleanup while the CPU fringe cleanup does less full-frame work
- **New Compute Selector** — Users can choose Auto, GPU Focused, or CPU Focused depending on whether they want automatic tuning, CUDA preference, or lower GPU load
- **CUDA Install Path Fixed** — Source, Debian, RPM, and amd64 Snap installs now install the CUDA mode runtime on NVIDIA systems instead of installing only CuPy and leaving ONNX inference on CPU
- **Clearer GPU Runtime Checks** — CUDA modes now require both CuPy compositing and the ONNX Runtime `CUDAExecutionProvider`, so the app no longer treats a partial GPU install as ready
- **Meeting Dependencies Stay Safe** — Packaged installs continue using the lighter `faster-whisper` runtime, and `openai-whisper` remains guarded for Python versions that support it
- **Sponsors Are Visible** — Public GitHub Sponsors now show in the README, dedicated sponsor wall, and About window so users can see who is backing the project

> If you are still on `v1.1.9` or older, update to `v1.1.10`. This is the recommended stable update for live background edge quality, compute-mode clarity, and release packaging safety.

### v1.1.9 — Meeting Runtime Dependency Hotfix

- **Meeting Transcription Install Fixed** — The app now installs `faster-whisper` safely without skipping the support packages required for local transcription
- **Package Installers Fixed Too** — Debian, RPM, and macOS package install paths now use the same corrected meeting runtime recipe as the in-app installer
- **Clearer Recovery Steps** — Missing-transcription messages now show the complete command instead of only `pip install faster-whisper`
- **No OpenAI Whisper Regression** — `openai-whisper` remains optional and guarded on newer Python versions; the default packaged path stays on the lighter `faster-whisper` runtime

> If you are still on `v1.1.8` or older, update to `v1.1.9`. This is the recommended hotfix for meeting transcription dependency reliability.

### v1.1.8 — Audio Helper and Installer Reliability Patch

- **Fixed Echo-Like Mic Doubling** — Old background audio helpers now exit with the app and are cleaned up before a new helper starts, preventing stale helpers from feeding duplicate `nvbroadcast` mic audio into calls
- **CuPy Installer Flow Fixed** — The source installer no longer aborts the whole install when the optional CuPy verification step fails after package installation
- **Clearer Installer Errors** — Install failures now report the real exit code and show useful CuPy verification output for future troubleshooting
- **Sponsor Links Easier to Find** — The About window and README now point users to GitHub Sponsors more clearly

> If you are still on `v1.1.7` or older, update to `v1.1.8`. This is the recommended stable patch for microphone reliability and source-install GPU setup.

### v1.1.7 — Live Edge and Mic Reliability Patch

- **Cleaner Hair and Hand Edges** — Background replace now holds hair edges, finger gaps, and hands near the body more cleanly during motion
- **Better Live Quality Mode Behavior** — Quality profiles now stay closer to the fresher inline matte path, which reduces the “edges follow motion” look that showed up after the earlier lag fixes
- **Less Face-Effect Spill Into Hair** — Beautify and relighting now use tighter face-tone masks, so head hair and side hair look less bright and washed out
- **Stronger Live Processing Path** — The live GPU/background path, shared face-landmark worker flow, and fused face-overlay handling were tuned further for steadier real-time behavior
- **Mic Always Ready** — The exported `nvbroadcast` microphone now stays available even when voice effects and noise removal are turned off
- **Broader Release Verification** — This release was rechecked across video, audio, meeting transcription, summaries, packaging metadata, and release smoke before shipping

> If you are still on `v1.1.6` or older, update to `v1.1.7`. This is the recommended stable patch for current live edge quality and microphone reliability.

### v1.1.6 — Live Background Performance and Stability Patch

- **Fixed Background Reset Loops** — The live alpha path now uses one dedicated worker instead of bouncing inference across short-lived threads, which stops the CUDA invalid-resource-handle failures that could make replace mode collapse into repeated RVM resets
- **Lower Replace-Mode Live Cost** — Relighting now reuses the same-frame final matte instead of rebuilding it, and replace-mode matte work is cached more aggressively on the live path
- **Better Motion Handling Around Face Effects** — Beautify keeps GPU work local to the face ROI and preserves raw denoise history more carefully, reducing motion smear around the face and glasses
- **Safer Heavy Live Stack Behavior** — The app is better at keeping the background path responsive on heavier Meeting-style stacks instead of compounding lag with duplicate work

> If you are still on `v1.1.5` or older, update to `v1.1.6`. This is the recommended stable patch for the recent live background lag regression.

### v1.1.5 — Stability and Live Quality Patch

- **Safer Effect + Mode Switching** — Video pipeline rebuilds now wait for teardown properly, which reduces camera freezes, device-busy failures, and mode-switch crashes
- **TensorRT Detection Fixed** — Zeus and Killer now recognize current `tensorrt-cu12` installs correctly and handle the TensorRT handoff more safely
- **Duplicate Audio Devices Cleaned Up** — Stale `nvbroadcast` mic and speaker duplicates are deduped, and startup restore no longer churns the virtual-audio path as aggressively
- **Better Motion On Face + Glasses** — Beautify denoise is now limited to the face ROI and keeps raw history, which reduces motion smear and disappearing glasses during movement
- **Replace Mode Overlap Improved** — Raised hands near shoulders and underarms are less likely to blow false holes through the background during motion

> If you are still on `v1.1.4` or older, update to `v1.1.5`. This is the recommended stable patch for switch stability, TensorRT detection, and current live-quality fixes.

### v1.1.4 — Audio and Packaging Reliability Patch

- **Browser-Safe Processed Mic** — The Linux `nvbroadcast` microphone path is now stable for Chrome, Discord, Meet, and similar apps instead of hanging or opening with silence
- **Meeting Runtime Fixed** — The optional Whisper runtime installer now validates real imports before claiming success and includes the missing `httpx` dependency
- **Packaged Meeting Runtime** — Release installers now bundle the local meeting transcription runtime more consistently so packaged installs do not depend on the in-app runtime path as often
- **No External `ffmpeg` Requirement For Saved Meetings** — The app now reads its own saved WAV meeting capture directly for the final transcript pass
- **Release Checks Tightened** — Packaging CI is opted into Node 24 early, and release smoke now covers dependency-installer, transcriber, summarizer, meeting-store, and packaging metadata checks

> If you are still on `v1.1.3` or older, update to `v1.1.4`. This is the recommended stable patch for meeting audio reliability and packaged runtime consistency.

### v1.1.3 — Meeting-First Live Quality Update

- **Lower Visible Delay** — Live video now prefers the newest frames instead of letting stale buffers build up, which reduces the odd “lips move late” effect in meetings
- **Auto - Adaptive Mode** — Hardware-aware tuning now persists across restart, warns on very weak devices, and can recommend lighter capture modes when real-time FPS collapses
- **Better Live Face Effects** — Face relighting is now fill-light biased instead of darkening the face, and eye contact is more conservative so it distorts less
- **Meeting-Selectable Mic** — The processed mic is exported as `nvbroadcast`, so Zoom, Meet, Teams, OBS, and similar apps can select it directly
- **Correct Speaker Routing** — Speaker denoise now honors the selected output device instead of whichever sink the system guessed
- **Release + Update Flow** — The app now surfaces platform-aware upgrade targets for GitHub releases, macOS `.pkg` downloads, and Snap installs

> If you are still on `v1.1.2` or older, update to `v1.1.3`. This is the recommended stable build for live meetings, adaptive tuning, and corrected audio routing.

### v1.1.2 — Priority Stability Update

- **Meeting Transcript Quality** — Better chunk cleanup and a stronger final full-audio pass improve saved transcripts and notes
- **No End-Meeting Freeze** — Meeting transcript, notes, and summary finalization now run off the UI thread
- **Persistent Speaker + Profile State** — Speaker selection and the active profile now restore correctly after restart
- **Reset to Defaults** — One-click recovery back to a known-good baseline
- **Mic Test Fixed** — Recording and playback are more reliable, with `30s`, `45s`, and `60s` capture options plus early stop

> If you are still on `v1.1.0` or `v1.1.1`, update to `v1.1.2`. It is the recommended stable patch for meeting quality, persistence, and audio test reliability.

### v1.1.1 — Stability Patch

- **Virtual Camera Stability** — Safer Linux `v4l2loopback` sink startup and retry handling
- **Lower Live Lag** — Shared face landmarks and face-ROI relighting reduce delay in heavier effect stacks
- **Better Replace Edges** — Tighter shoulders, ear-side hair, and under-arm gaps during background replace
- **Meeting Transcription Reliability** — Faster startup, shorter chunking, and cleaner saved meeting audio
- **Resolution Change Safety** — Resolution changes are saved safely and applied after restart instead of hanging the stream

> If you are still on `v1.1.0`, update to `v1.1.1`. It improved virtual-camera behavior, lower lag, and cleaner live compositing.

### v1.1.0 — Meeting Assistant Update

- **Meeting Assistant Sidebar** — Collapsible live transcript and rolling summary inside the app
- **Meeting History** — Local session history stays on-device for 7 days with automatic cleanup
- **Two-Way Meeting Audio** — Meeting capture records both sides for better local notes and transcripts
- **Background Runtime Installs** — Optional CUDA, TensorRT, and meeting runtimes install in the background with progress
- **Improved Setup Guidance** — First-run flow explains modes, downloads, and skip/install choices more clearly

### v1.0.0 — AI Release

- **AI Meeting Transcription** — Local Whisper speech-to-text (tiny/base/small/medium models, GPU-accelerated)
- **AI Meeting Summarizer** — Extracts action items, questions, key points from transcripts (fully local)
- **Voice Effects** — Bass boost, treble, warmth, compression, noise gate, gain (GPU + CPU)
- **6 Voice Presets** — Natural, Radio, Podcast, Deep Voice, Bright, Studio
- **Microphone Selection** — Full PipeWire/PulseAudio device enumeration
- **Speaker Detection** — All output devices via PipeWire
- **Audio Level Monitor** — Real-time VU meter with peak hold
- **Mic Test** — Record 30s / 45s / 60s and play back to test your setup
- **Meeting Mode** — Combined video+audio recording with live transcription and AI summary
- **Recording Fix** — MP4 now includes audio track (NVENC video + AAC audio)
- **Voice FX GPU Acceleration** — CuPy CUDA for warmth/gate/gain, scipy for filters (2.8ms/chunk)

### v0.3.0

- **Eye Contact Correction** — MediaPipe iris tracking redirects your gaze to look at camera
- **Face Relighting** — Fill light guided by the scene
- **Recording Mode** — NVENC hardware encode to MP4 (x264 fallback on non-NVIDIA)
- **Performance Overlay** — Real-time FPS, GPU usage, VRAM, temperature monitoring
- **User Profiles** — 5 built-in (Meeting, Streaming, Presentation, Gaming, Clean) + custom save/load
- **Multi-Camera Support** — Hot-switch between cameras without restarting
- **Apple-Inspired UI** — Glassmorphism cards, collapsible sections, smooth transitions
- **Shared FaceLandmarker** — Single MediaPipe instance shared across all face effects (3x faster)
- **macOS Support** — CPU modes with CoreML, AVFoundation camera, Homebrew installer
- **CI Pipeline** — GitHub Actions builds .deb, .rpm, .pkg + Swift Camera Extension on macOS

### v0.2.0

### Premium GPU Modes
- **Killer Mode** — Fused CUDA kernel + 360p inference = **48fps at 1080p** (20ms/frame)
- **Zeus Mode** — 480p optimized inference = **33fps at 1080p** (30ms/frame)
- **DocZeus Mode** — Fused CUDA kernel compositing = **CUDA Max quality at 150x faster blend** (0.1ms vs 15ms)

### Edge Refinement Neural Network
- Toggle-activated second-pass inference at 720p for Zeus/Killer modes
- Uses RVM ResNet50 at full resolution with morphological edge band blending
- **89.9% quality recovery** — brings fast modes close to max quality edges

### Video Enhancement
- **5 independent effects**: Skin Smooth, Denoise, Enhance, Sharpen, Edge Darken
- **4 presets**: Natural, Broadcast, Glamour, Custom
- Per-effect toggle + intensity slider
- MediaPipe FaceLandmarker at half-res, every 5th frame
- GPU batch processing (CuPy) for enhance + sharpen + vignette

### Resolution & FPS Selector
- Auto-detects camera capabilities via v4l2
- Shows only supported resolutions (360p to 4K)
- FPS dropdown adapts per resolution (e.g., 4K shows 30fps, 1080p shows 30+60fps)
- Validated before pipeline start — no more cap negotiation hangs

### UI Improvements
- **Resizable preview** — drag the divider between preview and controls
- **Pause View** — freeze the preview display (camera keeps running)
- **Hide Preview** — collapse preview entirely for more control space
- **Mirror toggle** — horizontal flip for webcam view
- **Scrollable controls** — all settings accessible regardless of window size
- **Grouped cards** — Input, Processing, Background, Auto Frame, Beauty

### Performance Optimizations
- **Pre-downsampling**: Frames above 720p are downsampled before inference (124ms -> 29ms at 1080p)
- **Async effects processing**: Capture thread never blocks — zero preview latency
- **Python-side frame throttling**: No pipeline restart for mode/profile changes
- **Fused CUDA kernel**: Single GPU pass for alpha blend + enhance + vignette (0.1ms)

---

## What It Does

<table>
<tr>
<td width="50%">

### Camera Effects
- **Background Blur** — AI-powered, person stays crystal sharp
- **Background Replace** — Any image via native file picker
- **Green Screen** — Solid green for OBS chroma key
- **Auto Frame** — Face tracking with smooth zoom/pan
- **Video Enhancement** — Skin smooth, enhance, sharpen, denoise, vignette
- **Eye Contact Correction** — MediaPipe iris tracking redirects gaze to camera
- **Face Relighting** — Fill light guided by the scene
- **Recording to MP4** — NVENC hardware encode (x264 fallback)
- **User Profiles** — 5 built-in (Meeting, Streaming, etc.) + custom save/load
- **Performance Overlay** — Real-time FPS, GPU usage, VRAM, temperature
- **Multi-Model** — RVM (person), IS-Net (objects), BiRefNet (best edges)
- **Mirror** — Horizontal flip toggle

</td>
<td width="50%">

### Audio Effects
- **Mic Noise Removal** — Kills keyboard, fan, environment noise
- **Speaker Denoise** — Clean up incoming audio
- **Voice Effects** — Bass boost, treble, warmth, compression, noise gate, gain
- **6 Voice Presets** — Natural, Radio, Podcast, Deep Voice, Bright, Studio
- **Microphone Selection** — Full PipeWire/PulseAudio device enumeration
- **Speaker Detection** — All output devices via PipeWire
- **Audio Level Monitor** — Real-time VU meter with peak hold
- **Mic Test** — Record 30s / 45s / 60s and play back to test your setup
- **AI Meeting Transcription** — Local Whisper speech-to-text (GPU-accelerated)
- **AI Meeting Summarizer** — Action items, questions, key points (fully local)
- **Meeting Mode** — Video+audio recording with live transcription and AI summary

### System Integration
- **Virtual Camera** — Works in Chrome, Firefox, Zoom, Discord, OBS
- **Auto-Start** — Launches on login, runs in background
- **Setup Wizard** — Auto-detects system, configures optimally
- **Multi-GPU** — Select which GPU runs AI effects
- **Multi-Distro** — Ubuntu, Fedora, Arch, openSUSE, and more
- **Resolution/FPS** — 360p-4K, 15-60fps, auto-detected from camera

</td>
</tr>
</table>

---

## Processing Modes

9 modes from maximum speed to CPU fallback:

| Mode | Inference | Compositing | 1080p Speed | CPU | GPU | Best For |
|------|-----------|-------------|-------------|-----|-----|----------|
| **Killer** | 360p + fused CUDA | Fused kernel (0.1ms) | **20ms / 48fps** | 24% | 41% | Maximum speed |
| **Zeus** | 480p optimized | CuPy GPU | 30ms / 33fps | 22% | 39% | Speed + quality balance |
| **DocZeus** | 720p full quality | Fused kernel (0.1ms) | 44ms / 23fps | 22% | 46% | **Best quality/speed** |
| **CUDA Max** | 720p | CuPy GPU | 45ms / 22fps | 22% | 46% | Maximum quality |
| **CUDA Balanced** | 720p, skip 2 | CuPy GPU | 29ms / 34fps | 24% | 39% | Daily use |
| **CUDA Perf** | 720p, skip 2 | CuPy GPU | 30ms / 34fps | 23% | 39% | Light GPU load |
| **CPU Quality** | 720p | OpenCV SIMD | 66ms / 15fps | 17% | 27% | No CuPy fallback |
| **CPU Light** | 720p, skip 2 | OpenCV SIMD | 30ms / 34fps | 23% | 20% | Save GPU for games |
| **CPU Low End** | 720p, skip 3 | OpenCV SIMD | 27ms / 37fps | 21% | 20% | Older hardware |

> **Edge Refine** toggle available for Killer and Zeus modes — adds ~27ms but recovers 89.9% of max quality edges.
>
> Switch modes anytime from the **Mode** dropdown. No restart needed.
>
> CUDA modes require the CUDA mode runtime: CuPy for compositing plus ONNX Runtime with `CUDAExecutionProvider` for model inference. Source, `.deb`, `.rpm`, and amd64 Snap installs handle this automatically on NVIDIA systems. The arm64 Snap build stays CPU-safe because ONNX Runtime GPU wheels are not published for Linux arm64 yet.

---

## Architecture

```
                         NV Broadcast v1.0.0
                         ─────────────────────────────────

  ┌───────────┐      ┌──────────────────────────────────────────┐      ┌──────────────┐
  │  Webcam   │─────▶│           GStreamer Pipeline              │─────▶│ Virtual Cam  │
  │(360p-4K)  │      │                                          │      │ /dev/video10 │
  └───────────┘      │  JPEG Decode ─▶ Color Convert ─▶ appsink │      └──────┬───────┘
                     └──────────────────────┬───────────────────┘             │
                                            │                        ┌───────▼───────┐
                            ┌───────────────▼──────────────┐         │ Chrome / Zoom │
                            │    Async Effects Thread       │         │ Firefox / OBS │
                            │   (never blocks capture)      │         │ Discord/Meet  │
                            │                               │         └───────────────┘
                            │  ┌─────────────────────────┐  │
                            │  │   AI Segmentation        │  │
                            │  │                          │  │
                            │  │  Pre-downsample to 720p  │  │
                            │  │  (or 480/360 for Zeus/   │  │
                            │  │   Killer modes)          │  │
                            │  │                          │  │
                            │  │  ┌────┐ ┌─────┐ ┌────┐  │  │
                            │  │  │RVM │ │ISNet│ │BiR │  │  │
                            │  │  └──┬─┘ └──┬──┘ └─┬──┘  │  │
                            │  │     └───┬──┘      │     │  │
                            │  │         ▼         │     │  │
                            │  │   Alpha Refine    │     │  │
                            │  │  (sigmoid+dilate) │     │  │
                            │  └────────┬──────────┘     │  │
                            │           │                 │  │
                            │  ┌────────▼───────────────┐ │  │
                            │  │  Edge Refiner (opt.)   │ │  │
                            │  │  720p 2nd pass RVM     │ │  │
                            │  │  (Zeus/Killer only)    │ │  │
                            │  └────────┬───────────────┘ │  │
                            │           │                 │  │
                            │  ┌────────▼───────────────┐ │  │
                            │  │     Compositing        │ │  │
                            │  │                        │ │  │
                            │  │  ┌────────┐ ┌───────┐  │ │  │
                            │  │  │ Fused  │ │ CuPy  │  │ │  │
                            │  │  │ CUDA   │ │ CUDA  │  │ │  │
                            │  │  │ 0.1ms  │ │ 15ms  │  │ │  │
                            │  │  └────────┘ └───────┘  │ │  │
                            │  └────────────────────────┘ │  │
                            │           │                 │  │
                            │  ┌────────▼───────────────┐ │  │
                            │  │   Video Enhancement  │ │  │
                            │  │  5 effects + presets   │ │  │
                            │  │  GPU batch (CuPy)      │ │  │
                            │  └────────────────────────┘ │  │
                            │           │                 │  │
                            │  Mirror flip (optional)     │  │
                            └───────────┬─────────────────┘
                                        │
                            ┌───────────▼──────────────┐
                            │ Preview (GTK4 Texture)    │
                            │ Pause / Hide / Resize     │
                            └──────────────────────────┘

  ┌───────────┐      ┌─────────────────────────────────┐      ┌──────────────┐
  │    Mic    │─────▶│     RNNoise AI Denoise          │─────▶│ Virtual Mic  │
  │           │      │     (48kHz, 10ms frames)        │      │  (PipeWire)  │
  └───────────┘      └─────────────────────────────────┘      └──────────────┘
```

### Fused CUDA Kernel (DocZeus/Killer)

A custom CUDA kernel that performs alpha blend + enhance + sharpen + vignette in **one GPU pass**:

```cuda
// Single kernel: fg*alpha + bg*(1-alpha) + enhance + vignette
// 0.1ms at 1080p — 150x faster than CuPy's multi-kernel approach
extern "C" __global__ void fused_composite(
    fg, bg, alpha, face_mask, vignette, output,
    total_pixels, enhance_i, vignette_i, brightness, contrast, warmth
);
```

### Edge Refinement Network

When Edge Refine is toggled ON (Zeus/Killer modes):

1. **Fast pass**: RVM at 360p/480p → coarse alpha (18-21ms)
2. **Refine pass**: RVM ResNet50 at 720p → quality alpha (30ms, every 2nd frame)
3. **Blend**: On refine frames use quality alpha; on skip frames 80% quality + 20% coarse for tracking
4. **Result**: 89.9% quality recovery with minimal cost

---

## AI Models

| Model | Segments | Speed (RTX 5060) | VRAM | License | Auto-Download |
|-------|----------|-----------------|------|---------|---------------|
| **RVM** (default) | Person only | ~29ms (720p) | 660 MB | GPL-3.0 | Yes |
| **IS-Net** | Any object | ~55ms | 1.8 GB | Apache 2.0 | Yes |
| **BiRefNet** | Best edges | ~187ms | 6+ GB | MIT | Yes |

### Quality Presets (RVM only)

| Preset | Backbone | Downsample | Best For |
|--------|----------|-----------|----------|
| Performance | MobileNetV3 | 0.25 | Video calls |
| Balanced | MobileNetV3 | 0.5 | Daily use |
| Quality | ResNet50 | 0.375 | Presentations |
| Ultra | ResNet50 | 0.5 | Recording |

---

## Requirements

### Hardware
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU** | NVIDIA GTX 1060 | RTX 3060 or newer |
| **VRAM** | 2 GB | 4 GB+ |
| **CPU** | 4 cores | 8+ cores (if using CPU compositing) |
| **Webcam** | Any USB camera | 720p+ with MJPEG or raw V4L2 modes |
| **Mic** | Any audio input | — |

### Software
- **Linux** with NVIDIA driver 525+ (Pop!_OS, Ubuntu, Fedora, Arch, openSUSE, etc.)
- **Python** 3.11+
- **PipeWire** (virtual microphone)
- **PulseAudio utilities** (`pactl`) for speaker-monitor routing and device resolution
- **GStreamer** 1.20+ with plugins-base, plugins-good, plugins-bad
- **GTK4** and **Libadwaita**
- **v4l2loopback** kernel module
- **DKMS** and **kernel headers** (to build v4l2loopback)

---

## Installation

### Linux — One Command Install

```bash
git clone https://github.com/Hkshoonya/nvidia-broadcast-linux.git
cd nvidia-broadcast-linux
./install.sh
```

### macOS — One Command Install

```bash
git clone https://github.com/Hkshoonya/nvidia-broadcast-linux.git
cd nvidia-broadcast-linux
./install_macos.sh
```

Requires macOS 12+, Homebrew, Python 3.11+. Installs GStreamer, GTK4 via Homebrew.
CPU modes with CoreML acceleration on Apple Silicon. GPU modes (Killer/Zeus/DocZeus/CUDA) are Linux-only and require an NVIDIA GPU.

### Linux — Snap Package

```bash
sudo snap install nvbroadcast
```

Snap users typically receive background refreshes from `snapd`. When the app sees a newer stable release, the in-app update button opens the Snap Store listing so the user can move directly into the store-managed upgrade path.

The amd64 Snap build includes the CUDA mode runtime for NVIDIA systems. The arm64 Snap build stays CPU-safe because the required ONNX Runtime GPU wheels are not available for Linux arm64 yet. If CUDA modes are still unavailable on amd64 Snap, use the source installer, `.deb`, or `.rpm` release package as the fallback.

Packaged releases are intended to include the local meeting transcription runtime. Source installs from this repo can still use the in-app runtime installer flow for optional components.

### Linux Installer Details

The installer:
1. **Detects your distro** and package manager
2. **Checks all requirements** (Python, PipeWire, GPU, DKMS, kernel headers)
3. **Installs missing packages** with the correct names for your distro
4. **Installs NVIDIA CUDA mode runtime packages** when an NVIDIA GPU is detected
5. **Asks about compositing** — CPU, GStreamer GL, or CuPy CUDA
6. **Sets up virtual camera**, launcher scripts, desktop entry, systemd service
7. **Verifies GPU acceleration** and writes initial config
8. **Lets optional runtimes install later** inside the app without blocking the rest of the UI

### Update Behavior

- **Git checkout / manual Linux packages** — the app checks GitHub Releases and opens the matching release download page when a newer stable build is available
- **macOS package installs** — the app prefers the latest `.pkg` release asset when one is published
- **Snap installs** — the app opens the Snap Store listing; stable refreshes are normally handled by `snapd`

### Optional: TensorRT (for Zeus/Killer modes)

```bash
.venv/bin/pip install tensorrt-cu12 onnx
```

TensorRT Python wheels are currently published for Python `3.8` through `3.13`
on Linux `x86_64`. If you are on Python `3.14+`, use `DocZeus` or the CUDA
modes instead.

### Supported Distros

| Distro | Package Manager | Status |
|--------|----------------|--------|
| Ubuntu, Debian, Pop!_OS, Mint | apt | Full auto-install |
| Fedora, RHEL, CentOS, Rocky | dnf/yum | Full auto-install |
| Arch, Manjaro, EndeavourOS | pacman | Full auto-install |
| openSUSE | zypper | Full auto-install |
| Gentoo, Void, NixOS | portage/xbps/nix | Manual instructions shown |

<details>
<summary>Click to expand manual install steps</summary>

```bash
# 1. System dependencies
sudo apt install -y \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-4.0 gir1.2-adw-1 \
    gir1.2-gstreamer-1.0 gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    v4l-utils v4l2loopback-dkms \
    pipewire-bin pulseaudio-utils

# 2. Python venv
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# 3. Install
pip install -e .

# For NVIDIA GPU acceleration, install the CUDA extra instead:
pip install -e ".[cuda]"

# 4. Optional: CuPy-only retry for GPU compositing
pip install cupy-cuda12x nvidia-cuda-nvrtc-cu12

# 5. Virtual camera
sudo modprobe v4l2loopback devices=1 video_nr=10 \
    card_label="NVbroadcast" exclusive_caps=1 max_buffers=4

# 6. Run
python -m nvbroadcast
```

</details>

---

## Usage

### Setup Once, Forget Forever

```bash
nvbroadcast          # Launch GUI (first time: setup wizard)
```

1. **Setup wizard** detects your system and configures the best mode
2. App starts and auto-begins streaming
3. Configure effects, select resolution/FPS/mode
4. **Close the window** — app minimizes to background, virtual camera stays active
5. Open **Chrome / Zoom / Discord / OBS** — select **"NVbroadcast"** as your camera
6. **Next login** — app starts automatically with all your settings remembered

### Controls

| Control | Description |
|---------|-------------|
| **Resolution** | 360p to 4K — auto-detected from camera, applied safely after restart |
| **FPS** | 15-60fps — adapts to selected resolution |
| **Mode** | 9 modes: Killer, Zeus, DocZeus, CUDA, CPU |
| **Mirror** | Horizontal flip on/off |
| **Edge Refine** | Neural edge refinement (Zeus/Killer) |
| **Pause View** | Freeze preview display |
| **Hide Preview** | Collapse preview for more control space |
| **Drag Divider** | Resize preview vs controls area |

### Headless Mode

```bash
nvbroadcast-vcam                    # No GUI, just the virtual camera
nvbroadcast-vcam --format i420      # Firefox-compatible format
```

### As a System Service

```bash
systemctl --user enable nvbroadcast-vcam
systemctl --user start nvbroadcast-vcam
```

---

## Troubleshooting

<details>
<summary><strong>Chrome doesn't see the virtual camera</strong></summary>

1. Go to `chrome://flags`
2. Search **"PipeWire"**
3. **Disable** "PipeWire Camera" flag
4. Restart Chrome

</details>

<details>
<summary><strong>"Device busy" error</strong></summary>

Another app is using the camera. Close it or run:
```bash
fuser -k /dev/video0
```

</details>

<details>
<summary><strong>No GPU acceleration (running on CPU)</strong></summary>

From the source checkout, install the CUDA extra. This installs the ONNX Runtime GPU provider and CUDA runtime libraries used by the CUDA modes:
```bash
.venv/bin/pip install --upgrade ".[cuda]"
```

Verify that ONNX Runtime can see the GPU provider:
```bash
.venv/bin/python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

The output should include `CUDAExecutionProvider`. On Python `3.14+`, TensorRT may still be unavailable, but CUDA modes can run when the CUDA extra installs successfully.

</details>

<details>
<summary><strong>Resolution changes do not apply immediately</strong></summary>

Resolution changes are now saved safely and applied after you stop and start the app again. This avoids the live-pipeline hang path that some cameras and loopback setups hit during hot restarts.

If a camera still behaves oddly after restart, verify its real supported modes:
```bash
v4l2-ctl -d /dev/video0 --list-formats-ext   # Check supported resolutions
```

</details>

---

## Project Structure

```
nvidia-broadcast-linux/
├── src/nvbroadcast/
│   ├── __init__.py              # Package version (1.1.11)
│   ├── app.py                   # GTK4 app: modes, effects, pipeline management
│   ├── vcam_service.py          # Headless virtual camera service
│   ├── core/
│   │   ├── config.py            # TOML config, performance profiles, compositing backends
│   │   ├── constants.py         # App ID, paths, GPU config
│   │   └── gpu.py               # GPU detection, CUDA device mapping
│   ├── video/
│   │   ├── effects.py           # Multi-model engine, fused CUDA kernel, edge refiner
│   │   ├── pipeline.py          # GStreamer pipeline, async effects, frame throttling
│   │   ├── beautify.py          # Video enhancement (5 effects + GPU batch)
│   │   ├── autoframe.py         # MediaPipe face tracking with smooth zoom/pan
│   │   └── virtual_camera.py    # v4l2loopback + camera capability query
│   ├── audio/
│   │   ├── effects.py           # RNNoise denoiser
│   │   ├── pipeline.py          # GStreamer audio pipeline
│   │   ├── monitor.py           # Speaker output denoise
│   │   └── virtual_mic.py       # PipeWire virtual microphone
│   └── ui/
│       ├── window.py            # Main window: resizable paned layout, 9 modes
│       ├── setup_wizard.py      # First-run wizard
│       ├── controls.py          # Effect toggles, sliders, file picker
│       ├── device_selector.py   # Dropdown selector (single-connect fix)
│       ├── video_preview.py     # Live video preview
│       └── style.css            # App styling with Adwaita/system theme integration
├── models/                      # AI models (auto-downloaded)
│   ├── rvm_mobilenetv3_fp32.onnx
│   ├── rvm_resnet50_fp32.onnx
│   ├── rvm_mobilenetv3_fp16.onnx   # Lightweight refiner model
│   ├── rvm_resnet50_fp32_trt.onnx  # TensorRT shape-inferred
│   └── rvm_mobilenetv3_fp32_trt.onnx
├── install.sh                   # Multi-distro installer
├── uninstall.sh                 # Clean removal
├── pyproject.toml               # Package config (v1.1.11)
└── README.md
```

---

## Contributing

Contributions, feedback, and ideas are **warmly welcome**.

### How to Contribute

1. **Fork** this repository
2. **Create a branch** (`git checkout -b feature/amazing-thing`)
3. **Commit** with clear messages
4. **Open a Pull Request**

### Report Issues

Found a bug? [Open an issue](https://github.com/Hkshoonya/nvidia-broadcast-linux/issues/new).

### Ideas for Contribution

- [x] Eye contact correction *(v0.3.0)*
- [x] Virtual lighting / face relighting *(v0.3.0)*
- [x] System tray indicator *(v0.2.0)*
- [x] Multi-camera support *(v0.3.0)*
- [x] Recording mode *(v0.3.0)*
- [x] Performance overlay (FPS, GPU usage) *(v0.3.0)*
- [x] GStreamer NVDEC/NVENC hardware codec pipeline *(v0.3.0)*
- [ ] NVIDIA Maxine SDK integration
- [ ] Flatpak packaging
- [x] Snap packaging

## Future Upgrades

- **Meeting lip-sync compensation** — explicit audio/video delay calibration so heavy live video stacks still land naturally in calls
- **Per-device auto benchmark** — benchmark each camera mode and effect stack once, then pin the best stable settings for that machine
- **Speaker diarization** — separate “me” vs “remote speaker” in live meeting transcripts and saved notes
- **Local live captions** — optional on-screen captions and confidence-aware subtitle output for streams and calls
- **Multi-person framing** — presenter mode for interviews, podcasts, and side-by-side calls
- **AI meeting memory** — on-device semantic search across prior meetings, summaries, action items, and decisions
- **Scene-aware relighting** — stronger face light that reacts to background direction, exposure, and skin tone without flattening the face
- **Quality advisor** — explain exactly which effect, resolution, or backend is costing FPS on the current hardware

---

## Sponsor This Project

If NV Broadcast saves you from going back to Windows, consider sponsoring.

This project takes ongoing work across GPU runtimes, packaging, camera/audio compatibility, meeting features, and cross-distro bug fixes. Sponsorship helps keep that work moving without turning the app into adware or locking core features behind a paywall.

- **Individual sponsors** help fund day-to-day fixes, release maintenance, and new features
- **Creator and business sponsors** help cover hardware testing, distro support, packaging, and priority reliability work
- **All sponsors** help keep the Linux version improving instead of stagnating behind Windows-only tools

<p align="center">
  <a href="https://github.com/sponsors/Hkshoonya">
    <img src="https://img.shields.io/badge/Sponsor_DocZeus-Support_Development-76b900?style=for-the-badge&logo=githubsponsors&logoColor=white&labelColor=1a1a1a" alt="Sponsor">
  </a>
</p>

### 💎 Featured Sponsors

<!-- featured --><em>No featured sponsors yet - <a href="https://github.com/sponsors/Hkshoonya">become a Creator-tier sponsor</a> and your logo appears here.</em><!-- featured -->

### 💚 Backers &amp; Supporters

<!-- sponsors --><a href="https://github.com/Mattsky" title="Mattsky"><img src="https://avatars.githubusercontent.com/u/2619664?u=a3e9b73765da4dd8f3472520e40c9588c65a7803&v=4" width="55" alt="Mattsky"></a>&nbsp;<!-- sponsors -->

<p align="center">
  <a href="https://github.com/sponsors/Hkshoonya">GitHub Sponsors</a> ·
  <a href="https://github.com/Hkshoonya/nvidia-broadcast-linux/issues">Report bugs</a> ·
  <a href="https://github.com/Hkshoonya/nvidia-broadcast-linux/discussions">Share ideas</a>
</p>

---

## License

- **Python app & Linux code:** GPL-3.0 — see [LICENSE](LICENSE)
- **macOS Camera Extension** (`macos/`): Proprietary — see [macos/LICENSE](macos/LICENSE)

Any redistribution or derivative work **must retain the original author attribution**.

---

<p align="center">
  <img src="data/icons/doczeus-logo.svg" width="48" alt="DocZeus">
</p>

<p align="center">
  <strong>Created with passion by <a href="https://github.com/Hkshoonya">DocZeus</a></strong><br>
  <em>Because Linux users deserve broadcast-quality video too.</em>
</p>

<p align="center">
  <sub>Copyright (c) 2026 DocZeus. All rights reserved under GPL-3.0.</sub>
</p>
