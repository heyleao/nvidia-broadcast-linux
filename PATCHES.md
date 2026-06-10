# Patch Manifest

Branch:

```text
headless-services-cli
```

Base observed locally:

```text
1d545bb Improve CUDA Fast replace edge freshness
```

## Functional Summary

- Adds headless camera and microphone user services.
- Adds `nvbroadcast-headless` phased CLI.
- Adds `nvbroadcast-headless-control` lightweight GTK control window.
- Adds a persistent tray helper with a rounded headless icon.
- Adds an on-demand virtual camera mode that keeps `/dev/video10` visible while
  starting the physical camera and GPU effects only when an app consumes it.
- Keeps `nvbroadcast_mic` stable across audio service stop/start.
- Adds a headless settings window for mode, resolution, FPS, background, mirror,
  microphone noise removal, and voice FX.
- Adds `install-headless.sh` for Debian/Ubuntu, Fedora, Arch/CachyOS/Manjaro,
  and openSUSE-style systems.

## Main Commits

```text
570853c Add headless service controls
dce6caf Add persistent headless control and on-demand camera
e722554 Add headless tray indicator
b33de72 Add minimize button to headless control
43472ba Add headless settings window
e55828b Add rounded headless tray icon
```

## Local Validation Performed

```bash
python -m py_compile \
  src/nvbroadcast/vcam_service.py \
  src/nvbroadcast/audio_service.py \
  src/nvbroadcast/headless_cli.py \
  src/nvbroadcast/headless_control.py \
  src/nvbroadcast/headless_tray.py

git diff --check
```

Runtime validation performed on CachyOS + COSMIC/Wayland + NVIDIA + OBS:

- camera service active and consumed by OBS;
- audio service active and consumed by OBS;
- tray icon visible;
- control window toggles services without freezing;
- on-demand camera starts effects when consumed and returns to idle;
- `nvbroadcast_mic` remains visible while audio service is stopped;
- restarting audio reconnects processed stream to `nvbroadcast_sink`.
