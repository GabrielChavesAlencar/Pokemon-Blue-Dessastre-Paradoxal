"""CH11: reject cross-region badge/HM contracts, false gameplay and drift."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from audit_sinnoh_badges_hms import (
    CONTRACT, REGISTRY, REGIONS_RUNTIME, POLICY_RUNTIME,
    audit, read_json, read_runtime,
)


class SinnohBadgeHMContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = read_json(CONTRACT)
        cls.registry = read_json(REGISTRY)
        cls.runtime = read_runtime(REGIONS_RUNTIME)
        cls.policy = read_runtime(POLICY_RUNTIME)

    def check(self, spec=None, registry=None, runtime=None, policy=None):
        return audit(
            copy.deepcopy(self.contract if spec is None else spec),
            copy.deepcopy(self.registry if registry is None else registry),
            self.runtime if runtime is None else runtime,
            self.policy if policy is None else policy,
        )

    def rejects(self, reason, **kwargs):
        with self.assertRaisesRegex(ValueError, reason):
            self.check(**kwargs)

    def test_real_8_badges_8_hms_contract_is_planned_not_playable(self):
        result = self.check()
        self.assertEqual((result["badges"], result["hm_moves"]), (8, 8))
        self.assertFalse(result["can_install"])
        self.assertFalse(result["gameplay_verified"])

    def test_cli_is_safe_read_only(self):
        cp = subprocess.run(
            [sys.executable, str(ROOT / "scripts/regions/audit_sinnoh_badges_hms.py")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertFalse(json.loads(cp.stdout)["can_install"])

    def test_missing_or_extra_badge_is_rejected(self):
        spec = copy.deepcopy(self.contract)
        spec["rules"].pop()
        self.rejects("oito", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["rules"].append(copy.deepcopy(spec["rules"][0]))
        self.rejects("oito", spec=spec)

    def test_wrong_platinum_badge_order_and_duplicates_rejected(self):
        spec = copy.deepcopy(self.contract)
        spec["rules"][1]["badge"] = spec["rules"][0]["badge"]
        self.rejects("incompatíveis", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["rules"][2], spec["rules"][3] = spec["rules"][3], spec["rules"][2]
        self.rejects("incompatíveis", spec=spec)

    def test_hm_belongs_to_correct_badge_and_item(self):
        for index, changes in (
            (0, {"field_move": "SURF"}),
            (4, {"hm_item": "HM06"}),
            (7, {"hm_item": "HM01"}),
        ):
            with self.subTest(index=index):
                spec = copy.deepcopy(self.contract)
                spec["rules"][index].update(changes)
                self.rejects("incompatíveis", spec=spec)

    def test_foreign_region_badges_do_not_grant_sinnoh(self):
        for foreign in ("KANTO", "JOHTO", "HOENN", "DECADES"):
            with self.subTest(region=foreign):
                catalog = copy.deepcopy(self.registry)
                catalog["regions"]["SINNOH"]["field"]["SURF"]["badge"] = (
                    foreign + ":FEN")
                self.rejects("outra região|irregular", registry=catalog)

    def test_catalog_status_or_milestones_drift_blocks(self):
        catalog = copy.deepcopy(self.registry)
        catalog["regions"]["SINNOH"]["status"] = "playable"
        self.rejects("divergentes", registry=catalog)
        catalog = copy.deepcopy(self.registry)
        catalog["regions"]["SINNOH"]["milestones"][0] = "SOUL"
        self.rejects("divergentes", registry=catalog)

    def test_unknown_field_move_or_cross_region_rule_blocks(self):
        catalog = copy.deepcopy(self.registry)
        catalog["regions"]["SINNOH"]["field"]["FLASH"] = {
            "badge": "KANTO:BOULDER", "tool": True}
        self.rejects("diverge", registry=catalog)
        catalog = copy.deepcopy(self.registry)
        catalog["regions"]["SINNOH"]["field"]["DEFOG"] = {
            "badge": "SINNOH:RELIC", "tool": False}
        self.rejects("irregular", registry=catalog)

    def test_unsupported_or_falsely_playable_flags_block(self):
        for key in ("approved_for_install", "gameplay_verified",
                    "native_gym_events_verified",
                    "hm_pickup_events_installed", "native_map_ids_assigned"):
            with self.subTest(flag=key):
                spec = copy.deepcopy(self.contract)
                spec[key] = True
                self.rejects("jogável|isolamento", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["requires_confirmed_local_pickup"] = False
        self.rejects("jogável|isolamento", spec=spec)

    def test_missing_audit_fields_or_injected_map_id_rejected(self):
        spec = copy.deepcopy(self.contract)
        spec.pop("hm_item_is_not_equivalent_to_local_pickup")
        self.rejects("Campos", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["map_id"] = 500
        self.rejects("Campos", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["rules"][0]["event_id"] = 900
        self.rejects("Campos", spec=spec)

    def test_missing_runtime_guard_or_mapping_blocks(self):
        source = self.runtime.replace(
            '"DEFOG" => :HM05', '"DEFOG" => :HM03')
        self.rejects("Runtime Ruby", runtime=source)
        source = self.runtime.replace(
            "pickup_confirmed == true", "pickup_confirmed != false")
        self.rejects("Guarda Ruby", runtime=source)
        source = self.policy.replace(
            'local_proof = current["current"] == "SINNOH"',
            "local_proof = false")
        self.rejects("Política de campo", policy=source)

    def test_picked_up_items_stay_unverified_on_paper(self):
        spec = copy.deepcopy(self.contract)
        spec["rules"][2]["verified_hm_pickup_event"] = True
        self.rejects("jogáveis", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["rules"][5]["verified_gym_event"] = True
        self.rejects("jogáveis", spec=spec)


if __name__ == "__main__":
    unittest.main()
