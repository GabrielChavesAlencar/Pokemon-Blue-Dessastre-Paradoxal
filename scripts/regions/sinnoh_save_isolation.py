#!/usr/bin/env python3
"""S11 — read-only namespace checks for isolated Sinnoh QA saves.

The QA save namespace is derived from the 12-hex profile token and never
points to the normal Decades, Kanto, Johto or Hoenn save directory.
This module NEVER lists, opens, edits or deletes user save files.
"""
from __future__ import annotations

import re
from pathlib import Path

PROFILE_TOKEN = re.compile(r"[a-f0-9]{12}\Z")
QA_FOLDER = re.compile(r"game-sinnoh-qa-([a-f0-9]{12})\Z")
RESTRICTED_CONFIG_KEYS = ("save", "userdata")


def namespace(token: str) -> dict[str, str]:
    """Deterministic mkxp/Essentials namespace; no absolute filesystem paths."""
    if not isinstance(token, str) or not PROFILE_TOKEN.fullmatch(token):
        raise ValueError("S11: token QA deve ter 12 caracteres hexadecimais")
    return {
        "title": "Sinnoh QA " + token,
        "dataPathApp": "Sinnoh-QA-" + token,
        "dataPathOrg": "Dessastre-Sinnoh-QA-" + token,
    }


def validate_namespace(qa: Path, profile: object, config: object, ini: str,
                       *, project: Path, main_config: object = None) -> dict:
    """Fail closed if a private QA config can use a foreign/global save path.

    All arguments are pre-read structures. This function is PURE and does
    not run Game.exe, follow save paths or touch a user's AppData.
    """
    qa = Path(qa).absolute()
    project = Path(project).absolute()
    work = project / ".blue-work"
    if (project.is_symlink() or work.is_symlink() or qa.is_symlink()
            or not qa.is_relative_to(work) or not QA_FOLDER.fullmatch(qa.name)):
        raise ValueError("S11: pasta QA fora do espaco privado ou em symlink")
    token = QA_FOLDER.fullmatch(qa.name).group(1)
    expected = namespace(token)
    if type(profile) is not dict or profile != expected:
        raise ValueError("S11: namespace de save nao corresponde ao token QA")
    if type(config) is not dict:
        raise ValueError("S11: mkxp.json QA invalido")
    if any(any(word in key.casefold() for word in RESTRICTED_CONFIG_KEYS)
           for key in config if isinstance(key, str)):
        raise ValueError("S11: configuracao de save customizada nao auditada")
    if any(config.get(k) != expected[k] for k in ("dataPathApp", "dataPathOrg")):
        raise ValueError("S11: mkxp.json aponta para perfil diferente")
    if config.get("windowTitle") != expected["title"]:
        raise ValueError("S11: titulo mkxp nao corresponde ao perfil QA")
    if not isinstance(ini, str) or ini.count("Title=" + expected["title"]) != 1:
        raise ValueError("S11: Game.ini nao corresponde ao perfil QA")
    if type(main_config) is dict:
        if (expected["dataPathApp"] == main_config.get("dataPathApp")
                or expected["dataPathOrg"] == main_config.get("dataPathOrg")):
            raise ValueError("S11: namespace QA coincide com jogo principal")
    return {
        "save_namespace_verified": True,
        "profile_token": token,
        "private_data_path_app": expected["dataPathApp"],
        "private_data_path_org": expected["dataPathOrg"],
        "foreign_save_inherited": False,
        "native_save_reload_verified": False,
        "gameplay_approved": False,
    }
