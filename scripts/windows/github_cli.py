"""GitHub CLI portátil gerenciada pelo Blue-Story; nenhuma configuração manual de terminal.

Baixa somente o executável oficial da release cli/cli, exige o SHA256
publicado pela release e não altera PATH, Registro ou credenciais de usuário.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

RELEASE_URL = "https://api.github.com/repos/cli/cli/releases/latest"
RELEASE_DOWNLOAD = "https://github.com/cli/cli/releases/download/"
MAX_DOWNLOAD = 90_000_000
USER_AGENT = "Blue-Story-Johto-Publisher/1.0"


def _request(url: str):
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})


def _read(url: str, max_bytes: int) -> bytes:
    with urllib.request.urlopen(_request(url), timeout=50) as response:
        blob = response.read(max_bytes + 1)
    if len(blob) > max_bytes:
        raise RuntimeError("Download GitHub maior que o limite de segurança")
    return blob


def _expected_hash(release: dict, asset: dict) -> str:
    digest = asset.get("digest") or ""
    if re.fullmatch(r"sha256:[a-fA-F0-9]{64}", digest):
        return digest[7:].lower()
    sums = next((a for a in release.get("assets", [])
                 if re.fullmatch(r"gh_[^\s/]+_checksums\.txt", a.get("name", ""))), None)
    if sums is None or not sums.get("browser_download_url", "").startswith(RELEASE_DOWNLOAD):
        raise RuntimeError("Release oficial sem SHA-256 verificável")
    checksums = _read(sums["browser_download_url"], 400_000).decode("utf-8")
    for line in checksums.splitlines():
        match = re.fullmatch(r"([a-fA-F0-9]{64})\s+\*?(.+)", line.strip())
        if match and match.group(2).lstrip("./") == asset["name"]:
            return match.group(1).lower()
    raise RuntimeError("SHA-256 do pacote gh.exe ausente na release oficial")


def ensure_cli(project: Path, *, install: bool = True) -> str:
    """Retorna gh.exe funcional. Se ausente, instala no projeto sem janela de terminal."""
    project = Path(project).resolve()
    target = project / "tools/gh/gh.exe"
    if target.is_file() and not target.is_symlink():
        return str(target)
    existing = shutil.which("gh")
    if existing:
        return existing
    if not install or os.name != "nt":
        raise RuntimeError("GitHub CLI não instalada. Abra o Blue-Story para baixar os componentes.")
    release = json.loads(_read(RELEASE_URL, 3_000_000))
    architecture = os.environ.get("PROCESSOR_ARCHITECTURE", "AMD64").upper()
    platform = "arm64" if architecture == "ARM64" else "amd64"
    assets = [a for a in release.get("assets", [])
              if re.fullmatch(r"gh_[0-9][^/]*_windows_" + platform + r"\.zip", a.get("name", ""))]
    if len(assets) != 1:
        raise RuntimeError("Nenhum pacote oficial da GitHub CLI para Windows " + platform)
    asset = assets[0]
    url = asset.get("browser_download_url", "")
    if not url.startswith(RELEASE_DOWNLOAD) or not url.endswith("/" + asset["name"]):
        raise RuntimeError("Origem da GitHub CLI não é a release oficial")
    expected = _expected_hash(release, asset)
    work = project / ".blue-work"
    work.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="blue-gh-", dir=work))
    try:
        archive = folder / "cli.zip"
        archive.write_bytes(_read(url, MAX_DOWNLOAD))
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("A GitHub CLI baixada falhou na verificação SHA-256")
        with zipfile.ZipFile(archive) as zip_file:
            matches = [item for item in zip_file.infolist()
                       if item.filename.replace("\\", "/").split("/")[-2:] == ["bin", "gh.exe"]
                       and not item.is_dir()]
            if len(matches) != 1 or matches[0].file_size > 80_000_000:
                raise RuntimeError("gh.exe ausente ou inválido no pacote oficial")
            staged = folder / "gh.exe"
            with zip_file.open(matches[0]) as src, staged.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        test = subprocess.run([str(staged), "--version"], capture_output=True,
                              text=True, timeout=15,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if test.returncode != 0 or "gh version" not in test.stdout.lower():
            raise RuntimeError("gh.exe não executou após a instalação")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            raise RuntimeError("O destino de gh.exe é um symlink")
        os.replace(staged, target)
        return str(target)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
