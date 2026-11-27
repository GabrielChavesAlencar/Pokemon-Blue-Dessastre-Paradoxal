"""Pure K03-E release inputs; does not install, publish, or touch saves."""
from __future__ import annotations

import copy

from k03e_contract import MAPS, MUSIC, candidate_manifest
from export_kanto import k03e_portal_delta


def promote_inputs(source: dict, site: dict, music: dict, evidence: dict):
    """Return an additive, synchronized source, portal and music triplet."""
    manifest = candidate_manifest(source)
    if (evidence.get("version") != 1 or evidence.get("status") != "CANDIDATE_NOT_PUBLISHED"
            or not evidence.get("evidence", {}).get("sha256")):
        raise ValueError("K03-E portal evidence must be an audited candidate")
    promoted_site = {**copy.deepcopy(site),
                     "locations": copy.deepcopy(site["locations"] + evidence["locations"]),
                     "trainers": copy.deepcopy(site["trainers"] + evidence["trainers"])}
    k03e_portal_delta(site, promoted_site)
    existing = {row["map"] for row in music["maps"]}
    if existing & set(MAPS.values()):
        raise ValueError("K03-E music was already bound in the baseline")
    if set(manifest["preview_only"]) & MAPS.keys():
        raise ValueError("K03-E promotion would activate a preview")
    promoted_music = {**copy.deepcopy(music), "maps": copy.deepcopy(music["maps"] + MUSIC)}
    return manifest, promoted_site, promoted_music
