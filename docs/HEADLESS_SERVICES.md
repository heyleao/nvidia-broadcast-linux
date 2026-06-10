# Headless Camera and Microphone Services

This mode runs NVIDIA Broadcast processing without opening the full GTK UI.
It is useful for OBS, COSMIC/Wayland sessions, stream setups, and systems where
the graphical preview is less stable than the camera and microphone pipelines.

## Commands

The CLI is split into phases so users can repeat only the step they need.

### Phase 1 - Doctor

Check GPU/runtime support, v4l2loopback, and service status.

```bash
nvbroadcast-headless phase1
```

### Phase 2 - Configure

Show the current saved config.

```bash
nvbroadcast-headless phase2 --show
```

Common streaming setup:

```bash
nvbroadcast-headless phase2 \
  --mode zeus \
  --camera /dev/video0 \
  --width 640 \
  --height 360 \
  --fps 30 \
  --background on \
  --background-mode remove \
  --noise on
```

Available headless modes:

- `doczeus`
- `cuda_max`
- `cuda_balanced`
- `zeus`
- `killer`
- `cuda_perf`
- `cpu_quality`
- `cpu_light`
- `cpu_low`

### Phase 3 - Install Services

Install user-level wrappers, services, and the small control app.

```bash
nvbroadcast-headless phase3 --enable
```

This installs:

- `~/.local/bin/nvbroadcast-headless`
- `~/.local/bin/nvbroadcast-headless-control`
- `~/.local/bin/nvbroadcast-vcam`
- `~/.local/bin/nvbroadcast-audio-headless`
- `~/.config/systemd/user/nvbroadcast-vcam.service`
- `~/.config/systemd/user/nvbroadcast-audio.service`
- `~/.local/share/applications/nvbroadcast-headless-control.desktop`

Remove the headless setup:

```bash
nvbroadcast-headless phase3 --remove
```

### Phase 4 - Operate

Start, stop, restart, inspect, or view logs.

```bash
nvbroadcast-headless phase4 start
nvbroadcast-headless phase4 stop
nvbroadcast-headless phase4 restart
nvbroadcast-headless phase4 status
nvbroadcast-headless phase4 logs
```

## Control App

Launch the small taskbar-friendly control window:

```bash
nvbroadcast-headless-control
```

It can switch between:

- Camera + microphone
- Camera only
- Microphone only
- Off
- Restart services

The control app does not run the heavy preview UI. It only controls the
background services. The virtual microphone device is kept stable when the
audio service is stopped so apps such as OBS do not lose their selected input.

## OBS

Select these devices in OBS:

- Camera: `/dev/video10` or `NVIDIA Broadcast`
- Microphone: `nvbroadcast_mic`

If OBS is already open and the services were restarted, refresh/reselect the
camera source if needed.
