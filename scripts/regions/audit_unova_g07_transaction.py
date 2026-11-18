#!/usr/bin/env python3
"""Unova G07.3: in-memory ONLY CAS, staged incremental preview and rollback.

Consumes the strict G07.2 manifest validator. There is deliberately NO
filesystem write, ZIP extraction, HTTP, installer, Game.exe, JoiPlay, or
save-file path in this module. "Commit" is a returned Python dictionary only.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any, Mapping

import audit_unova_g07_incremental_manifest as g72

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = "data/regions/unova-g07-transaction-contract.json"
SCOPE = "G07_3_SYNTHETIC_MEMORY_ONLY"
PROTECTED = (
    "decades", "kanto", "johto", "hoenn", "sinnoh", "unova_uninstalled",
    "global_files", "saves", "checkpoints", "key_items", "boxes", "progress",
    "mechanics",
)
FAULTS = (
    "after_preflight", "after_staging", "after_backup", "after_cas",
    "after_first_candidate_write", "after_candidate_commit", "before_publish",
)
STATE_KEYS = {
    "scope", "region", "channel", "revision", "package_version", "generation",
    "source_manifest_sha256", "files", "protected",
}
CONTRACT_KEYS = {
    "schema_version", "phase", "region", "status", "depends_on", "simulator",
    "fixture_scope", "supported_channel", "allowed_file_prefix",
    "protected_namespaces", "fault_points", "guardrails",
    "native_technical_completed", "native_playable_completed", "can_install",
    "release_allowed", "limitations",
}
DEPS = {
    "schema": g72.SCHEMA_PATH,
    "contract": g72.CONTRACT_PATH,
    "validator": "scripts/regions/audit_unova_g07_incremental_manifest.py",
    "native_readiness": "scripts/regions/audit_unova_a12_ownership.py",
    "tracker": g72.TRACKER,
    "registry": g72.REGISTRY,
}
GUARDS = {
    "source_manifest_verified_first": True,
    "source_bytes_checked_before_stage": True,
    "package_hash_and_rights_checked": True,
    "exact_expected_revision": True,
    "expected_generation_required": True,
    "expected_full_snapshot_sha256_required": True,
    "double_cas_check_before_candidate_publish": True,
    "staged_payload_hash_rechecked": True,
    "backup_original_bytes_in_memory": True,
    "no_partial_state_exposed": True,
    "rollback_restores_complete_fixture": True,
    "conflicting_external_edit_abort": True,
    "unlisted_files_unchanged": True,
    "protected_namespaces_unchanged": True,
    "all_or_nothing_commit_in_memory": True,
    "never_install_native": True,
    "never_write_game_or_saves": True,
    "never_download_or_extract": True,
    "unova_installed": False,
    "windows_installer_ready": False,
    "android_supported": False,
    "joiplay_supported": False,
    "release_authorized": False,
}
def deny(msg: str) -> None:
    raise ValueError("UNOVA_G07_3_BLOCKED: " + msg)

def audit_contract(root: Path = ROOT) -> dict:
    """Verify rooted source-of-truth files, gate flags and G07.2's own audit."""
    g72.validate_catalog(root)
    data = g72.j(root, CONTRACT_PATH)
    g72.strict(data, CONTRACT_KEYS, "G07.3 transaction contract")
    expected = {
        "schema_version": 1, "phase": "G07.3", "region": "UNOVA",
        "status": "PLANNED_OFFLINE_CAS_TRANSACTION_ONLY",
        "depends_on": DEPS,
        "simulator": "scripts/regions/audit_unova_g07_transaction.py",
        "fixture_scope": SCOPE, "supported_channel": g72.CHANNEL,
        "allowed_file_prefix": g72.PREFIX,
        "protected_namespaces": list(PROTECTED), "fault_points": list(FAULTS),
        "guardrails": GUARDS, "native_technical_completed": 0,
        "native_playable_completed": 0, "can_install": False,
        "release_allowed": False,
    }
    for key, expected_value in expected.items():
        if data.get(key) != expected_value or type(data.get(key)) is not type(expected_value):
            deny("source schema, native safety policy or CAS gate changed: " + key)
    if not isinstance(data["limitations"], list) or len(data["limitations"]) < 5 or any(
        not isinstance(text, str) or not text.strip() for text in data["limitations"]
    ):
        deny("missing explicit limitations of in-memory simulation")
    board = g72.j(root, g72.TRACKER)
    g07 = next((x for x in board["groups"] if x["id"] == "G07"), {})
    tasks = g07.get("tasks", [])
    if (not any(t.get("id") == "G07.2" and t.get("status") == "done" for t in tasks)
        or not any(t.get("id") == "G07.3" and t.get("status") in ("pending", "done") for t in tasks)):
        deny("G07.2 not certified as completed or G07.3 missing")
    return {
        "phase": "G07.3", "scope": SCOPE,
        "native_files_written": 0, "native_saves_modified": False,
        "can_install": False, "blue_story_invoked": False,
        "game_exe_invoked": False, "joiplay_invoked": False,
        "rollback_points": len(FAULTS), "source_contract": "G07.2",
        "can_release": False, "simulated_only": True,
    }

def validate_state(state: Any) -> dict:
    """Strict synthetic fixture, including all other regions and user state."""
    g72.strict(state, STATE_KEYS, "synthetic store")
    if state["scope"] != SCOPE or state["region"] != "UNOVA" or state["channel"] != g72.CHANNEL:
        deny("state is not a G07.3 synthetic Unova documentation snapshot")
    if type(state["revision"]) is not str or not g72.HEX40.fullmatch(state["revision"]):
        deny("unknown local revision")
    if state["package_version"] != "0.0.0" and (
        type(state["package_version"]) is not str
        or not g72.VERSION.fullmatch(state["package_version"])
    ):
        deny("unsupported local version")
    if type(state["generation"]) is not int or not 0 <= state["generation"] <= 1_000_000:
        deny("invalid generation/CAS counter")
    g72.sha(state["source_manifest_sha256"], "recorded origin manifest")
    files = state["files"]
    if not isinstance(files, dict) or not 0 < len(files) <= g72.MAX_FILES:
        deny("fixture inventory missing or unbounded")
    total = 0
    for name, raw in files.items():
        if (not g72.path_ok(name) or name == g72.SOURCE_MANIFEST
            or type(raw) is not bytes or not 0 < len(raw) <= g72.MAX_BYTES):
            deny("unsafe or native byte path in synthetic store")
        total += len(raw)
    if total > g72.MAX_PACKAGE_BYTES:
        deny("fixture exceeds memory cap")
    protected = g72.strict(state["protected"], set(PROTECTED), "protected namespaces")
    for region, labels in protected.items():
        if not isinstance(labels, dict) or not 0 < len(labels) <= 24:
            deny("protected namespace missing: " + region)
        if any(
            type(k) is not str or re.fullmatch(r"FIXTURE_[A-Z0-9_]{1,60}", k) is None
            or type(v) is not str or re.fullmatch(r"FIXTURE_[A-Z0-9_]{1,90}", v) is None
            for k, v in labels.items()
        ):
            deny("only explicit synthetic protected metadata accepted: " + region)
    return state

def state_etag(state: dict) -> str:
    """CAS digest covers revision, generation, docs bytes and ALL protected data."""
    validate_state(state)
    serial = {
        k: v for k, v in state.items() if k != "files"
    }
    serial["files"] = {
        key: {"sha256": g72.digest(raw), "size": len(raw)}
        for key, raw in sorted(state["files"].items())
    }
    return g72.digest(g72.canonical(serial))

def base_fixture(package: dict | None = None, manifest: bytes | None = None,
                 source: Mapping[str, bytes] | None = None) -> dict:
    if package is None or manifest is None or source is None:
        package, manifest, source, _ = g72.demo_package()
    protected = {
        key: {"FIXTURE_" + key.upper() + "_LEDGER": "FIXTURE_INTACT_" + key.upper()}
        for key in PROTECTED
    }
    state = {
        "scope": SCOPE, "region": "UNOVA", "channel": g72.CHANNEL,
        "revision": package["source"]["origin_revision"],
        "package_version": "0.0.0", "generation": 0,
        "source_manifest_sha256": g72.digest(manifest),
        "files": dict(source), "protected": protected,
    }
    validate_state(state)
    return state

def _manifest_after(state: dict, package: dict) -> str:
    """Synthetic next-origin digest: no real origin manifest is emitted."""
    rows = [
        {"path": name, "size": len(content), "sha256": g72.digest(content)}
        for name, content in sorted(state["files"].items())
    ]
    return g72.digest(g72.canonical({
        "region": "UNOVA", "channel": g72.CHANNEL,
        "revision": package["source"]["target_revision"],
        "package_version": package["package_version"],
        "fixture_only": True, "files": rows,
    }))

def _safe_result(status: str, state: dict, *, reason: str | None = None,
                 trace: tuple[str, ...] = (), backups: dict | None = None) -> dict:
    # All data in the return value is cloned; no "partial candidate" escapes.
    out = {
        "phase": "G07.3", "status": status, "state": copy.deepcopy(state),
        "snapshot_sha256": state_etag(state), "trace": list(trace),
        "backup_manifest": copy.deepcopy(backups) if backups is not None else {},
        "native_files_written": 0, "bytes_written": 0,
        "native_saves_modified": False, "game_exe_invoked": False,
        "blue_story_invoked": False, "joiplay_invoked": False,
        "can_install": False, "release_allowed": False,
        "in_memory_only": True,
    }
    if reason is not None:
        out["reason"] = reason
    return out

class SyntheticFailure(Exception):
    """Used only for injecting a deterministic rollback point."""

def transact(
    state: dict, package: dict, origin_manifest: bytes,
    origin_bytes: Mapping[str, bytes], target_bytes: Mapping[str, bytes],
    *, expected_generation: int, expected_snapshot_sha256: str,
    observed_after_staging: dict | None = None, observed_before_publish: dict | None = None,
    fail_at: str | None = None,
) -> dict:
    """Prepare, stage, backup, CAS recheck and commit a NEW immutable snapshot.

    The only possible commit is the in-memory returned fixture. An injected
    failure, stale snapshot, competing edit, or unsupported revision preserves
    the entire starting snapshot, including ALL protected namespaces.
    """
    validate_state(state)
    start = copy.deepcopy(state)
    if fail_at is not None and fail_at not in FAULTS:
        deny("unknown injected fault")
    if type(expected_generation) is not int or expected_generation < 0:
        deny("explicit integer CAS generation required")
    g72.sha(expected_snapshot_sha256, "full CAS snapshot")
    trace = []
    # Stage zero: validation before any candidate or backup exists.
    g72.validate_package(package, origin_manifest, origin_bytes, target_bytes)
    trace.append("G07_2_PREVALIDATED")
    if state["package_version"] != "0.0.0":
        return _safe_result("CONFLICT_UNSUPPORTED_VERSION_CHAIN", start,
                            reason="G07.2 currently models only fixture origin 0.0.0",
                            trace=tuple(trace))
    if state["revision"] != package["source"]["origin_revision"]:
        return _safe_result("CONFLICT_SOURCE_REVISION", start,
                            reason="expected origin revision does not match current fixture",
                            trace=tuple(trace))
    if state["source_manifest_sha256"] != package["source"]["manifest_sha256"]:
        return _safe_result("CONFLICT_SOURCE_MANIFEST", start,
                            reason="synthetic source manifest was changed", trace=tuple(trace))
    if state["generation"] != expected_generation:
        return _safe_result("CONFLICT_CAS_GENERATION", start,
                            reason="caller observed stale generation", trace=tuple(trace))
    if state_etag(state) != expected_snapshot_sha256:
        return _safe_result("CONFLICT_CAS_SNAPSHOT", start,
                            reason="caller observed stale snapshot", trace=tuple(trace))
    changed_names = set(origin_bytes)
    if not changed_names.issubset(state["files"]) or any(
        state["files"][name] != raw for name, raw in origin_bytes.items()
    ):
        return _safe_result("CONFLICT_SOURCE_BYTES", start,
                            reason="current synthetic docs differ from package origin",
                            trace=tuple(trace))
    trace.append("BASELINE_MATCHED")
    backups: dict[str, dict] = {}
    try:
        if fail_at == "after_preflight":
            raise SyntheticFailure("after_preflight")
        stage = {name: bytes(raw) for name, raw in target_bytes.items()}
        for row in package["files"]:
            actual = stage[row["path"]]
            if g72.digest(actual) != row["sha256"] or len(actual) != row["size"]:
                deny("staged synthetic bytes changed before CAS")
        trace.append("PAYLOAD_STAGED_IN_MEMORY")
        if fail_at == "after_staging":
            raise SyntheticFailure("after_staging")
        originals = {name: bytes(state["files"][name]) for name in changed_names}
        backups = {
            name: {"sha256": g72.digest(raw), "size": len(raw), "memory_only": True}
            for name, raw in sorted(originals.items())
        }
        trace.append("ORIGINAL_BYTES_BACKED_UP_IN_MEMORY")
        if fail_at == "after_backup":
            raise SyntheticFailure("after_backup")
        # An alternate snapshot stands for a concurrent edit in the fixture
        # store. It is never used as a replacement or silently overwritten.
        observed = observed_after_staging if observed_after_staging is not None else state
        validate_state(observed)
        if (
            observed["generation"] != expected_generation
            or state_etag(observed) != expected_snapshot_sha256
            or state_etag(state) != expected_snapshot_sha256
        ):
            return _safe_result("CONFLICT_CAS_CONCURRENT_EDIT", start,
                                reason="fixture changed between staging and final compare",
                                trace=tuple(trace), backups=backups)
        trace.append("FINAL_FULL_STATE_CAS_MATCHED")
        if fail_at == "after_cas":
            raise SyntheticFailure("after_cas")
        candidate = copy.deepcopy(state)
        for i, name in enumerate(sorted(changed_names)):
            candidate["files"][name] = stage[name]
            if i == 0 and fail_at == "after_first_candidate_write":
                raise SyntheticFailure("after_first_candidate_write")
        candidate["revision"] = package["source"]["target_revision"]
        candidate["package_version"] = package["package_version"]
        candidate["generation"] += 1
        candidate["source_manifest_sha256"] = _manifest_after(candidate, package)
        trace.append("FULL_CANDIDATE_BUILT_NOT_PUBLISHED")
        if fail_at == "after_candidate_commit":
            raise SyntheticFailure("after_candidate_commit")
        validate_state(candidate)
        if candidate["protected"] != start["protected"]:
            deny("protected regional/global state modified")
        if any(candidate["files"][k] != v for k, v in start["files"].items()
               if k not in changed_names):
            deny("unlisted fixture docs changed")
        before_publish = observed_before_publish if observed_before_publish is not None else observed
        validate_state(before_publish)
        if (before_publish["generation"] != expected_generation
            or state_etag(before_publish) != expected_snapshot_sha256
            or state_etag(state) != expected_snapshot_sha256):
            return _safe_result("CONFLICT_CAS_CONCURRENT_EDIT", start,
                                reason="prepublish CAS no longer matches",
                                trace=tuple(trace), backups=backups)
        trace.append("PREPUBLISH_CAS_RECHECKED")
        if fail_at == "before_publish":
            raise SyntheticFailure("before_publish")
    except SyntheticFailure as exc:
        if state != start:
            deny("input state mutated during simulated rollback")
        return _safe_result("SIMULATED_ROLLBACK_COMPLETE", start,
                            reason=str(exc), trace=tuple(trace), backups=backups)
    if state != start:
        deny("input state unexpectedly mutated")
    result = _safe_result("SIMULATED_ATOMIC_COMMIT_NOT_INSTALLED", candidate,
                          trace=tuple((*trace, "PUBLISHED_AS_NEW_PYTHON_DICT")),
                          backups=backups)
    result["changed_files"] = len(changed_names)
    result["expected_source_revision"] = start["revision"]
    result["new_fixture_revision"] = candidate["revision"]
    result["protected_unchanged"] = candidate["protected"] == start["protected"]
    return result

def multi_file_fixture() -> tuple[dict, bytes, dict[str, bytes], dict[str, bytes]]:
    """Two edited docs are needed to catch partial candidate commits."""
    pkg, manifest, old, new = g72.demo_package()
    name = g72.PREFIX + "g07-3-second.md"
    old[name] = b"earlier"
    new[name] = b"next-version"
    origin = json.loads(manifest)
    origin["files"].append({
        "path": name, "sha256": g72.digest(old[name]), "size": len(old[name])
    })
    manifest = g72.canonical(origin)
    pkg["source"]["manifest_sha256"] = g72.digest(manifest)
    pkg["source"]["manifest_size"] = len(manifest)
    pkg["files"].append({
        "path": name, "kind": "documentation_fixture",
        "sha256": g72.digest(new[name]),
        "source_sha256": g72.digest(old[name]),
        "size": len(new[name]), "source_size": len(old[name]),
        "rights": copy.deepcopy(g72.RIGHTS),
    })
    pkg["package_sha256"] = g72.package_digest(pkg)
    g72.validate_package(pkg, manifest, old, new)
    return pkg, manifest, old, new

def demo(root: Path = ROOT) -> dict:
    audit_contract(root)
    pkg, manifest, old, new = multi_file_fixture()
    state = base_fixture(pkg, manifest, old)
    baseline = state_etag(state)
    kwargs = dict(expected_generation=state["generation"],
                  expected_snapshot_sha256=baseline)
    success = transact(state, pkg, manifest, old, new, **kwargs)
    rollbacks = [transact(state, pkg, manifest, old, new, fail_at=f, **kwargs)
                 for f in FAULTS]
    concurrent = copy.deepcopy(state)
    concurrent["protected"]["saves"]["FIXTURE_SAVES_LEDGER"] = "FIXTURE_DIFFERENT_SAVE"
    conflict = transact(state, pkg, manifest, old, new,
                        observed_after_staging=concurrent, **kwargs)
    if (not all(x["state"] == state for x in rollbacks)
        or any(x["status"] != "SIMULATED_ROLLBACK_COMPLETE" for x in rollbacks)
        or success["state"]["protected"] != state["protected"]
        or success["state"]["files"] != new
        or conflict["status"] != "CONFLICT_CAS_CONCURRENT_EDIT"):
        deny("offline dry-run invariant failed")
    return {
        "phase": "G07.3", "status": success["status"],
        "fixture_files": success["changed_files"], "rollback_points": len(rollbacks),
        "all_rollbacks_restored": True, "concurrent_protected_save_blocked": True,
        "backup_entries": len(success["backup_manifest"]),
        "protected_regions_preserved": True, "native_files_written": 0,
        "bytes_written": 0, "can_install": False, "release_allowed": False,
        "native_saves_modified": False, "simulated_only": True,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    flags = parser.add_mutually_exclusive_group(required=True)
    flags.add_argument("--check", action="store_true")
    flags.add_argument("--simulate-demo", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = audit_contract() if args.check else demo()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as exc:
        print("UNOVA_G07_3_BLOCKED: " + str(exc)[:280])
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
