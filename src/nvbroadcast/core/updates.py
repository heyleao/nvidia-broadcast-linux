# NVIDIA Broadcast for Linux
# Copyright (c) 2026 doczeus (https://github.com/Hkshoonya)
# Licensed under GPL-3.0 - see LICENSE file
#
"""Release update checks against GitHub Releases."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


LATEST_RELEASE_URL = "https://api.github.com/repos/Hkshoonya/nvidia-broadcast-linux/releases/latest"
HEADLESS_FORK_RELEASE_URL = "https://api.github.com/repos/heyleao/nvidia-broadcast-linux/releases/latest"
DEFAULT_CHECK_INTERVAL_SECONDS = 6 * 60 * 60
SNAP_STORE_URL = "https://snapcraft.io/nvbroadcast"


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str


@dataclass
class ReleaseInfo:
    tag_name: str
    version: str
    html_url: str
    published_at: str = ""
    assets: list[ReleaseAsset] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateTarget:
    button_label: str
    tooltip: str
    url: str


@dataclass(frozen=True)
class VerifiedSourceUpdate:
    repo_dir: Path
    remote: str
    tag_name: str
    version: str
    commit_sha: str
    current_sha: str


@dataclass(frozen=True)
class SourceUpdateResult:
    ok: bool
    message: str
    version: str = ""
    commit_sha: str = ""


def _version_key(version: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", version)
    return tuple(int(part) for part in parts) if parts else (0,)


def is_newer_version(latest: str, current: str) -> bool:
    return _version_key(latest) > _version_key(current)


def should_check_for_updates(config, now: int | None = None,
                             interval_seconds: int = DEFAULT_CHECK_INTERVAL_SECONDS) -> bool:
    if not getattr(config, "check_for_updates", True):
        return False
    if now is None:
        now = int(time.time())
    last_check = int(getattr(config, "last_update_check", 0) or 0)
    return (now - last_check) >= interval_seconds


def find_release_asset(release: ReleaseInfo, suffix: str) -> ReleaseAsset | None:
    suffix = suffix.lower()
    for asset in release.assets:
        if asset.name.lower().endswith(suffix):
            return asset
    return None


def resolve_update_target(release: ReleaseInfo) -> UpdateTarget:
    """Choose the most useful user-facing update target for this install."""
    if os.environ.get("SNAP"):
        return UpdateTarget(
            button_label="Open Snap Update",
            tooltip="Open the Snap Store page for the latest stable refresh",
            url=SNAP_STORE_URL,
        )

    if sys.platform == "darwin":
        pkg_asset = find_release_asset(release, ".pkg")
        if pkg_asset is not None:
            return UpdateTarget(
                button_label="Download macOS Update",
                tooltip=f"Download the macOS package for v{release.version}",
                url=pkg_asset.download_url,
            )

    if release.html_url:
        return UpdateTarget(
            button_label="Open Release Update",
            tooltip=f"Open the release downloads for v{release.version}",
            url=release.html_url,
        )

    return UpdateTarget(
        button_label="Update Available",
        tooltip=f"Open the latest release information for v{release.version}",
        url=LATEST_RELEASE_URL,
    )


def release_info_from_payload(payload: dict) -> ReleaseInfo:
    tag_name = str(payload.get("tag_name", "")).strip()
    version = tag_name[1:] if tag_name.startswith("v") else tag_name
    assets: list[ReleaseAsset] = []
    raw_assets = payload.get("assets", [])
    if isinstance(raw_assets, list):
        for asset in raw_assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name", "")).strip()
            download_url = str(asset.get("browser_download_url", "")).strip()
            if name and download_url:
                assets.append(ReleaseAsset(name=name, download_url=download_url))
    return ReleaseInfo(
        tag_name=tag_name,
        version=version,
        html_url=str(payload.get("html_url", "")).strip(),
        published_at=str(payload.get("published_at", "")).strip(),
        assets=assets,
    )


def fetch_latest_release(timeout: int = 5, url: str = LATEST_RELEASE_URL) -> ReleaseInfo | None:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "nvbroadcast-update-checker",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, TimeoutError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    return release_info_from_payload(payload)


def _run_git(repo_dir: Path, args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def find_git_checkout(start: Path | None = None) -> Path | None:
    if start is None:
        start = Path(__file__).resolve()
    directory = start if start.is_dir() else start.parent
    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        return None
    path = Path(result.stdout.strip())
    return path if path.exists() else None


def _remote_names(repo_dir: Path) -> list[str]:
    result = _run_git(repo_dir, ["remote"], timeout=5)
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _remote_url(repo_dir: Path, remote: str) -> str:
    result = _run_git(repo_dir, ["remote", "get-url", remote], timeout=5)
    return result.stdout.strip() if result.returncode == 0 else ""


def select_update_remote(repo_dir: Path) -> str | None:
    remotes = _remote_names(repo_dir)
    for remote in remotes:
        if "heyleao/nvidia-broadcast-linux" in _remote_url(repo_dir, remote):
            return remote
    for preferred in ("heyleao", "origin"):
        if preferred in remotes:
            return preferred
    return remotes[0] if remotes else None


def _tag_commit_from_ls_remote(output: str, tag_name: str) -> str | None:
    plain_ref = f"refs/tags/{tag_name}"
    peeled_ref = f"{plain_ref}^{{}}"
    plain_sha = None
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        sha, ref = parts[0], parts[1]
        if ref == peeled_ref:
            return sha
        if ref == plain_ref:
            plain_sha = sha
    return plain_sha


def _remote_tag_commit(repo_dir: Path, remote: str, tag_name: str) -> str | None:
    result = _run_git(repo_dir, ["ls-remote", "--tags", remote, f"refs/tags/{tag_name}"], timeout=20)
    if result.returncode != 0:
        return None
    return _tag_commit_from_ls_remote(result.stdout, tag_name)


def _local_tag_commit(repo_dir: Path, tag_name: str) -> str | None:
    result = _run_git(repo_dir, ["rev-parse", f"{tag_name}^{{commit}}"], timeout=5)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def prepare_verified_source_update(
    release: ReleaseInfo,
    *,
    repo_dir: Path | None = None,
    remote: str | None = None,
) -> SourceUpdateResult | VerifiedSourceUpdate:
    repo_dir = repo_dir or find_git_checkout()
    if repo_dir is None:
        return SourceUpdateResult(False, "Instalacao atual nao parece ser um checkout git.")
    remote = remote or select_update_remote(repo_dir)
    if remote is None:
        return SourceUpdateResult(False, "Nenhum remote git encontrado para atualizar.")
    tag_name = release.tag_name.strip()
    if not tag_name:
        return SourceUpdateResult(False, "Release sem tag valida.")

    remote_sha = _remote_tag_commit(repo_dir, remote, tag_name)
    if not remote_sha:
        return SourceUpdateResult(False, f"Nao foi possivel verificar a tag {tag_name} no GitHub.")

    fetch = _run_git(repo_dir, ["fetch", "--force", remote, f"refs/tags/{tag_name}:refs/tags/{tag_name}"], timeout=60)
    if fetch.returncode != 0:
        return SourceUpdateResult(False, fetch.stderr.strip() or f"Falha ao baixar a tag {tag_name}.")

    local_sha = _local_tag_commit(repo_dir, tag_name)
    if local_sha != remote_sha:
        return SourceUpdateResult(False, "SHA da tag local nao bate com o SHA remoto. Atualizacao bloqueada.")

    current = _run_git(repo_dir, ["rev-parse", "HEAD"], timeout=5)
    if current.returncode != 0:
        return SourceUpdateResult(False, "Nao foi possivel identificar o SHA atual.")
    current_sha = current.stdout.strip()
    if current_sha == remote_sha:
        return SourceUpdateResult(True, f"Ja esta atualizado em {tag_name}.", release.version, remote_sha)

    return VerifiedSourceUpdate(
        repo_dir=repo_dir,
        remote=remote,
        tag_name=tag_name,
        version=release.version,
        commit_sha=remote_sha,
        current_sha=current_sha,
    )


def apply_verified_source_update(plan: VerifiedSourceUpdate) -> SourceUpdateResult:
    status = _run_git(plan.repo_dir, ["status", "--porcelain"], timeout=5)
    if status.returncode != 0:
        return SourceUpdateResult(False, "Nao foi possivel verificar o estado do checkout.")
    if status.stdout.strip():
        return SourceUpdateResult(
            False,
            "Existem alteracoes locais no checkout. Atualizacao bloqueada para nao sobrescrever arquivos.",
        )

    local_sha = _local_tag_commit(plan.repo_dir, plan.tag_name)
    if local_sha != plan.commit_sha:
        return SourceUpdateResult(False, "A tag mudou depois da verificacao. Atualizacao bloqueada.")

    checkout = _run_git(plan.repo_dir, ["checkout", "--detach", plan.commit_sha], timeout=30)
    if checkout.returncode != 0:
        return SourceUpdateResult(False, checkout.stderr.strip() or "Falha ao aplicar checkout da versao.")

    return SourceUpdateResult(
        True,
        f"Atualizado para {plan.tag_name} ({plan.commit_sha[:12]}). Reinicie o painel se necessario.",
        plan.version,
        plan.commit_sha,
    )
