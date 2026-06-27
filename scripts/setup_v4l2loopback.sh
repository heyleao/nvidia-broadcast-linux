#!/usr/bin/env bash
# Configure v4l2loopback for NVbroadcast virtual camera
set -e

DEVICE_NUM=10
LABEL="NVbroadcast"

echo "=== NVbroadcast Virtual Camera Setup ==="

# Make persistent across reboots
CONF_FILE="/etc/modprobe.d/nvbroadcast-v4l2loopback.conf"
if [ ! -f "$CONF_FILE" ] || grep -Eq 'card_label="(NVIDIA Broadcast|NVIDIA Broadcast Virtual Camera|NV Broadcast)"' "$CONF_FILE"; then
    echo "Creating persistent config at ${CONF_FILE}..."
    echo "options v4l2loopback devices=1 video_nr=${DEVICE_NUM} card_label=\"${LABEL}\" exclusive_caps=1 max_buffers=4" | sudo tee "$CONF_FILE"
    echo "v4l2loopback" | sudo tee /etc/modules-load.d/nvbroadcast-v4l2loopback.conf
    echo "Config saved. Virtual camera will persist across reboots."
fi

# Check if module is loaded
if lsmod | grep -q v4l2loopback; then
    echo "v4l2loopback is already loaded"
    if [ -e "/dev/video${DEVICE_NUM}" ]; then
        echo "Virtual camera device /dev/video${DEVICE_NUM} already exists"
        v4l2-ctl -d "/dev/video${DEVICE_NUM}" --all 2>/dev/null | head -5 || true
        echo "If the visible camera name is old, reboot or reload v4l2loopback when the camera is not in use."
        exit 0
    fi
fi

# Load module
echo "Loading v4l2loopback with device /dev/video${DEVICE_NUM}..."
sudo modprobe v4l2loopback \
    devices=1 \
    video_nr=${DEVICE_NUM} \
    card_label="${LABEL}" \
    exclusive_caps=1 \
    max_buffers=4

echo "Virtual camera created at /dev/video${DEVICE_NUM}"
