# Changelog

## v1.1.11-headless.4 - Headless fork consolidated release

This release consolidates the earlier headless test tags into one user-facing build.
It is intended to replace `v1.1.11-headless.1`, `v1.1.11-headless.2`, and
`v1.1.11-headless.3`.

### What changed for users

- Added a lightweight headless control panel for camera, microphone, logs, settings,
  monitoring, restart, minimize, and quit.
- Added live microphone level feedback so users can see signal/noise in real time
  while tuning the microphone.
- Added microphone return monitoring, so users can listen to the processed virtual
  microphone while adjusting voice and noise settings.
- Added live log viewing with a movable/resizable logs window and real-time tail.
- Added movable/resizable app windows so the control panel, settings, and logs can
  be arranged around OBS or other meeting tools.
- Added microphone and speaker selectors in the headless settings flow.
- Added voice preset controls with clearer voice shaping options.
- Added noise reduction intensity control and safer audio limiting to reduce
  clipping/crackling when the input gets loud.
- Added real-time app resource usage below `Quit`: CPU, memory, GPU, and VRAM for
  NV Broadcast processes only.
- Removed noisy status text and duplicate/non-functional controls from the main
  headless screen.
- Kept camera/microphone services available when closing the panel; use `Desligar`
  or `Quit` when you really want to stop services.

### CUDA and TensorRT behavior

- Fixed CUDA Balanced falling back to CPU when the CPU `onnxruntime` package was
  installed alongside `onnxruntime-gpu`.
- Linux installs now prefer `onnxruntime-gpu==1.24.4`, avoiding accidental CPU
  runtime shadowing.
- Fixed saved GPU index handling so an invalid `compute_gpu` value no longer makes
  ONNX Runtime reject CUDA and fall back to CPU.
- Confirmed CUDA Balanced loads on the NVIDIA GPU with `CUDAExecutionProvider`.
- Fixed `DocZeus` so it actually uses TensorRT max quality instead of CUDA fused
  compositing.
- Kept existing profile meanings clear:
  - `cpu_quality`, `cpu_light`, `cpu_low`: CPU modes.
  - `cuda_max`, `cuda_balanced`, `cuda_perf`: CUDA modes.
  - `doczeus`, `zeus`, `killer`: TensorRT modes.

### Update flow

- The headless `Atualizar` button now checks the fork release, verifies the release
  tag SHA against GitHub, fetches the tag locally, verifies the local tag SHA, and
  only then asks the user to accept the update.
- The updater refuses to apply if the local checkout has uncommitted changes, so it
  does not overwrite local work.
- After a verified update is accepted, services are restarted so OBS/meeting apps
  pick up the new code.

### Packaging and install safety

- Package metadata now includes the headless control app, CLI wrappers, desktop
  entry, services, and icon.
- Debian/RPM install scripts include the headless services and stop them cleanly
  during package removal.
- Packaging tests now verify the headless entrypoints and Linux GPU runtime
  dependency selection.

### Validation

- Verified current runtime logs show TensorRT when selecting `DocZeus` or `Zeus`.
- Verified `pip check` reports no broken requirements after using
  `onnxruntime-gpu`.
- Focused test coverage passed for headless CLI, update helpers, packaging metadata,
  audio effects, audio pipeline, voice FX, dependency checks, architecture support,
  auto mode tuning, background overlay, and TensorRT RVM.

## v1.1.11-headless.3 - Service lifecycle correction

This tag fixed the behavior introduced in `.2`.

- Closing the panel no longer stops the virtual camera/microphone services.
- `Minimizar` hides the panel.
- `Desligar` stops camera and microphone services.
- `Quit` stops the services and exits the app.
- This keeps OBS and meeting apps from losing the virtual camera just because the
  control panel was closed.

## v1.1.11-headless.2 - Stop services on close

This tag tried to make close behavior more explicit, but it was too aggressive for
OBS/headless usage.

- Closing the control panel stopped the headless services.
- This avoided orphan services, but it broke the expected headless workflow where
  services should keep running after the panel closes.
- Superseded by `.3` and the consolidated `.4` behavior.

## v1.1.11-headless.1 - Initial headless control release

First packaged headless build on top of upstream `v1.1.11`.

- Added headless wrappers and systemd user services.
- Added headless control app and tray integration.
- Added audio controls, voice presets, noise reduction tuning, and log access.
- Added package metadata for Debian/RPM headless assets.
- Added tests for packaging metadata and the new headless runtime surface.
