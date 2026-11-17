"""Atomic Sinnoh-only LOCAL staging: dry run, stage, verify and rollback.

This helper does NOT import RMXP maps, remap IDs, compile Ruby/PBS, touch
game/, or authorize redistribution. It stages caller-provided transformed
bytes inside ignored .blue-work/sinnoh-stage/ for later manual audit.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

LABEL = re.compile(r"[a-z][a-z0-9_-]{0,31}\Z")
ALLOWED = re.compile(
    r"(?:Data/(?:Map[0-9]{3,5}|MapInfos|Tilesets)\.rxdata|"
    r"Graphics/(?:Tilesets|Autotiles|Characters)/[A-Za-z0-9_ .()-]{1,120}\.(?:png|gif))\Z"
)
MAX_FILES = 5000
MAX_TOTAL_BYTES = 512 * 1024 * 1024


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def stage_root(project: Path) -> Path:
    project = Path(project).absolute()
    if project.is_symlink() or not project.is_dir():
        raise ValueError("Raiz de projeto inválida")
    work = project / ".blue-work"
    stage = work / "sinnoh-stage"
    for entry in (work, stage):
        if entry.is_symlink():
            raise ValueError("Workspace de Sinnoh não pode usar symlinks")
    if not stage.resolve().is_relative_to(project.resolve()):
        raise ValueError("Stage fora do projeto")
    return stage


def preview(project: Path, label: str, files: dict[str, bytes]) -> dict:
    stage_root(project)  # validate workspace, WITHOUT creating it
    if not isinstance(label, str) or not LABEL.fullmatch(label):
        raise ValueError("Identificador de staging inválido")
    if not isinstance(files, dict) or not files or len(files) > MAX_FILES:
        raise ValueError("Staging vazio ou com arquivos demais")
    records = []
    total = 0
    names = set()
    for relative, raw in sorted(files.items()):
        if (not isinstance(relative, str) or not ALLOWED.fullmatch(relative)
                or relative.casefold() in names or
                not isinstance(raw, bytes) or not raw):
            raise ValueError("Nome/conteúdo de arquivo de staging inválido")
        names.add(relative.casefold())
        total += len(raw)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("Staging excede limite total seguro")
        records.append({"path": relative, "bytes": len(raw), "sha256": digest(raw)})
    summary = {"label": label, "files": records}
    signature = digest(json.dumps(summary, ensure_ascii=True,
                                  sort_keys=True, separators=(",", ":")).encode("ascii"))
    return {
        "schema": 1, "region": "SINNOH", "mode": "DRY_RUN_NO_WRITES",
        "label": label, "plan_sha256": signature,
        "files": records, "total_bytes": total,
        "stage_relative_path": f".blue-work/sinnoh-stage/{label}-{signature[:16]}",
        "writes_to_main_game": False, "may_install_into_game": False,
        "source_rights_verified": False, "mapping_verified": False,
    }


def stage(project: Path, label: str, files: dict[str, bytes],
          expected_plan_sha256: str) -> dict:
    plan = preview(project, label, files)
    if not isinstance(expected_plan_sha256, str) or expected_plan_sha256 != plan["plan_sha256"]:
        raise ValueError("Plan SHA-256 não corresponde ao dry-run")
    root = stage_root(project)
    root.mkdir(parents=True, exist_ok=True)
    destination = Path(project).absolute() / plan["stage_relative_path"]
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("Stage anterior já existe; não sobrescrever")
    temp = Path(tempfile.mkdtemp(prefix=".sinnoh-staging-", dir=root))
    try:
        for row in plan["files"]:
            target = temp / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(files[row["path"]])
                handle.flush()
                os.fsync(handle.fileno())
            if digest(target.read_bytes()) != row["sha256"]:
                raise ValueError("Hash alterado durante staging")
        manifest = {**plan, "mode": "LOCAL_STAGE_ONLY"}
        with (temp / "stage-manifest.json").open("x", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("Stage foi criado em paralelo")
        temp.rename(destination)
    except BaseException:
        if temp.exists():
            shutil.rmtree(temp)
        raise
    return {**plan, "mode": "LOCAL_STAGE_ONLY", "stage_created": True}


def rollback(project: Path, label: str, plan_sha256: str) -> dict:
    # Keep deletion limited to the ONE stage from a known immutable plan.
    if (not isinstance(label, str) or not LABEL.fullmatch(label)
            or not isinstance(plan_sha256, str)
            or not re.fullmatch(r"[a-f0-9]{64}", plan_sha256)):
        raise ValueError("Identidade de rollback inválida")
    root = stage_root(project)
    folder = root / f"{label}-{plan_sha256[:16]}"
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Stage de rollback não encontrado")
    manifest_file = folder / "stage-manifest.json"
    if manifest_file.is_symlink() or not manifest_file.is_file():
        raise ValueError("Manifesto do stage não localizado")
    manifest = json.loads(manifest_file.read_text("utf-8"))
    if (manifest.get("plan_sha256") != plan_sha256 or manifest.get("label") != label
            or manifest.get("mode") != "LOCAL_STAGE_ONLY"):
        raise ValueError("Manifesto do stage foi alterado")
    rows = manifest.get("files")
    # A self-consistent immutable receipt is required before ANY deletion.
    # Without this, an edited JSON could re-label files as legitimate stage
    # contents. Even with a recomputed receipt this is only a local integrity
    # check, not a cryptographic authorization for third-party maps.
    expected_keys = {
        "schema", "region", "mode", "label", "plan_sha256",
        "files", "total_bytes", "stage_relative_path",
        "writes_to_main_game", "may_install_into_game",
        "source_rights_verified", "mapping_verified",
    }
    if (type(manifest) is not dict or set(manifest)!=expected_keys or
        manifest.get("schema")!=1 or manifest.get("region")!="SINNOH" or
        manifest.get("writes_to_main_game") is not False or
        manifest.get("may_install_into_game") is not False or
        manifest.get("source_rights_verified") is not False or
        manifest.get("mapping_verified") is not False or
        not isinstance(rows,list) or not rows or len(rows)>MAX_FILES):
        raise ValueError("Manifesto do stage inválido")
    canonical=[]
    seen=set()
    total=0
    allowed_dirs=set()
    for row in rows:
        if (type(row) is not dict or set(row)!={"path","bytes","sha256"} or
            not isinstance(row["path"],str) or
            not ALLOWED.fullmatch(row["path"]) or
            row["path"].casefold() in seen or
            type(row["bytes"]) is not int or row["bytes"]<=0 or
            not isinstance(row["sha256"],str) or
            not re.fullmatch(r"[a-f0-9]{64}",row["sha256"])):
            raise ValueError("Arquivos de rollback inválidos")
        seen.add(row["path"].casefold())
        total+=row["bytes"]
        if total>MAX_TOTAL_BYTES:
            raise ValueError("Stage excede limite")
        canonical.append(row)
        path=Path(row["path"])
        allowed_dirs.update(str(v.as_posix()) for v in path.parents if str(v)!=".")
    if canonical!=sorted(canonical,key=lambda row:row["path"]):
        raise ValueError("Manifesto do stage fora da ordem canônica")
    signed=digest(json.dumps(
        {"label":label,"files":canonical},ensure_ascii=True,sort_keys=True,
        separators=(",",":")).encode("ascii"))
    if (signed!=plan_sha256 or manifest.get("total_bytes")!=total or
        manifest.get("stage_relative_path")!=
        f".blue-work/sinnoh-stage/{label}-{plan_sha256[:16]}"):
        raise ValueError("Assinatura do plano ou destino alterado")
    permitted={row["path"] for row in rows}
    permitted.add("stage-manifest.json")
    actual=set()
    for item in folder.rglob("*"):
        if item.is_symlink():
            raise ValueError("Stage contém link simbólico; rollback bloqueado")
        relative=item.relative_to(folder).as_posix()
        if item.is_dir() and relative not in allowed_dirs:
            raise ValueError("Stage contém pasta inesperada; não apagar")
        if item.is_file():
            actual.add(relative)
    if actual != permitted:
        raise ValueError("Stage modificado: conteúdo extra/ausente; não apagar")
    for row in rows:
        target = folder / row["path"]
        if (not target.is_file() or target.stat().st_size!=row["bytes"] or
                digest(target.read_bytes())!=row["sha256"]):
            raise ValueError("Stage modificado: hash divergente; não apagar")
    shutil.rmtree(folder)
    return {"region": "SINNOH", "mode": "LOCAL_ROLLBACK",
            "removed_only_stage": True, "plan_sha256": plan_sha256}
