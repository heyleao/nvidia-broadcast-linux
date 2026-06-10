#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${NVBROADCAST_VENV:-$ROOT_DIR/.venv}"
PYTHON_BIN="${PYTHON:-python3}"
INSTALL_SYSTEM_DEPS=1
ENABLE_SERVICES=1

usage() {
    cat <<'EOF'
Usage: ./install-headless.sh [options]

Install NVIDIA Broadcast Linux headless services, control app, and tray helper.

Options:
  --no-system-deps   Do not install distro packages
  --no-enable        Install wrappers/services but do not enable/start them
  --venv PATH        Virtualenv path (default: ./.venv)
  -h, --help         Show this help

Supported package managers:
  apt, dnf, pacman, zypper
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-system-deps)
            INSTALL_SYSTEM_DEPS=0
            shift
            ;;
        --no-enable)
            ENABLE_SERVICES=0
            shift
            ;;
        --venv)
            VENV_DIR="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

have() {
    command -v "$1" >/dev/null 2>&1
}

run_sudo() {
    if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

install_system_deps() {
    if [[ "$INSTALL_SYSTEM_DEPS" -eq 0 ]]; then
        return
    fi

    if have apt-get; then
        run_sudo apt-get update
        run_sudo apt-get install -y \
            python3 python3-venv python3-pip python3-gi python3-gi-cairo \
            gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gstreamer-1.0 \
            gir1.2-ayatanaappindicator3-0.1 \
            gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
            gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
            v4l2loopback-dkms pipewire pipewire-pulse wireplumber
    elif have dnf; then
        run_sudo dnf install -y \
            python3 python3-pip python3-gobject gtk4 libadwaita \
            gstreamer1 gstreamer1-plugins-base gstreamer1-plugins-good \
            gstreamer1-plugins-bad-free gstreamer1-plugins-ugly-free \
            libayatana-appindicator-gtk3 v4l2loopback pipewire pipewire-pulseaudio wireplumber
    elif have pacman; then
        run_sudo pacman -S --needed --noconfirm \
            python python-pip python-gobject gtk4 libadwaita \
            gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly \
            libayatana-appindicator v4l2loopback-dkms pipewire pipewire-pulse wireplumber
    elif have zypper; then
        run_sudo zypper install -y \
            python3 python3-pip python3-gobject gtk4 libadwaita-1-0 \
            typelib-1_0-Gtk-4_0 typelib-1_0-Adw-1 typelib-1_0-Gst-1_0 \
            typelib-1_0-AyatanaAppIndicator3-0_1 \
            gstreamer gstreamer-plugins-base gstreamer-plugins-good \
            gstreamer-plugins-bad gstreamer-plugins-ugly \
            v4l2loopback-kmp-default pipewire pipewire-pulseaudio wireplumber
    else
        echo "No supported package manager found. Re-run with --no-system-deps after installing dependencies manually." >&2
        exit 1
    fi
}

install_python_package() {
    "$PYTHON_BIN" -m venv --system-site-packages "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --upgrade pip wheel
    "$VENV_DIR/bin/python" -m pip install -e "$ROOT_DIR" --no-build-isolation
}

install_headless_services() {
    local phase3_args=()
    if [[ "$ENABLE_SERVICES" -eq 1 ]]; then
        phase3_args+=(--enable)
    fi
    "$VENV_DIR/bin/python" -m nvbroadcast.headless_cli phase3 "${phase3_args[@]}"
}

main() {
    install_system_deps
    install_python_package
    install_headless_services

    if have gtk-update-icon-cache; then
        gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
    fi

    cat <<EOF

Headless install complete.

Open the control app:
  nvbroadcast-headless-control

Inspect services:
  nvbroadcast-headless phase4 status

EOF
}

main
