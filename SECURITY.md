# Security Policy

## Supported Scope

This repository contains community patches and wrappers for `nvidia-broadcast-linux`
headless services. Security reports should focus on:

- credential leaks in scripts, docs, CI, or examples;
- unsafe service/unit behavior;
- unsafe file permissions;
- command injection risks in CLI/service helpers;
- accidental publication of local user configuration.

## Secrets Policy

Never commit or paste:

- Twitch stream keys;
- Twitch OAuth tokens;
- GitHub personal access tokens;
- OBS `service.json` files containing stream keys;
- local `~/.config/nvbroadcast/config.toml` if it identifies private devices or accounts;
- private logs containing account identifiers or tokens.

If a token or stream key was exposed, revoke and rotate it immediately.

## Reporting

Open a private security advisory on GitHub when available. If advisories are not
enabled, open an issue with minimal reproduction details and no secrets.

## Local Services

The headless services are user-level `systemd --user` units. They should not
require root at runtime. Any installation step that requires elevated privileges
must be explicit and documented.

## Dependencies

This patch does not vendor NVIDIA, Twitch, OBS, or upstream project secrets. It
expects users to install dependencies from their distribution or the upstream
project instructions.
