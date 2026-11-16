#!/usr/bin/env python3
"""CH15: audit 13 Platinum teams; never confuse history, strongest or native PBS.

Read-only. An optional PBS input reports *candidates* (not Game.exe-compilation
proof). Does not write PBS, game/, site data, MapIDs, trainer levels or saves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/regions/sinnoh-trainer-teams-ch15.json"
WALKTHROUGH = ROOT / "docs/SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md"
REVIEW = ROOT / "data/regions/detonados-content-review.json"
REGIONS = ROOT / "site/public/data/regions.json"
STRONGEST = ROOT / "site/public/data/strongest-teams.json"
STORY_TRAINERS = ROOT / "site/public/data/story-trainers.json"
CAMPAIGN = ROOT / "scripts/battle_polish/Campaign.rb"
STORY = ROOT / "scripts/battle_polish/Story.rb"

GYM_NAMES = (
    "Roark", "Gardenia", "Fantina", "Maylene", "Crasher Wake",
    "Byron", "Candice", "Volkner",
)
ELITE_NAMES = ("Aaron", "Bertha", "Flint", "Lucian")
CHAMPION = "Cynthia"
GYM_BADGES = (
    "COAL", "FOREST", "RELIC", "COBBLE", "FEN", "MINE", "ICICLE", "BEACON",
)
TOP_KEYS = {
    "schema", "region", "status", "reference_game", "sources",
    "native_source_available_in_repository", "native_pbs_compilation_verified",
    "native_event_battle_bindings_verified", "gameplay_verified",
    "can_install", "may_write_pbs", "ui_policy", "dynamic_balance",
    "trainers", "notes",
}
SOURCES = {
    "historical": "docs/SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md",
    "identities": "data/regions/detonados-content-review.json",
    "regional_badges": "site/public/data/regions.json",
    "kanto_strongest_not_sinnoh": "site/public/data/strongest-teams.json",
    "other_regions_pbs_not_sinnoh": "site/public/data/story-trainers.json",
    "balance": "scripts/battle_polish/Campaign.rb",
    "boss_preservation": "scripts/battle_polish/Story.rb",
}
UI_POLICY = {
    "publish_historical_fixed_levels": False,
    "publish_rematch_as_blue_strongest": False,
    "publish_unverified_blue_native_as_installed": False,
    "render_actual_levels_from": "BLUE_CAMPAIGN_DYNAMIC_SCALING_ONLY",
}
BALANCE = {
    "normal_percent": 70, "master_percent": 90,
    "reference_level": "highest_non_egg_party_level",
    "boss_species_preserved": True,
    "blue_regional_first_boss_bst_exemption": True,
    "elite_champion_first_roster_not_automatically_evolved": True,
}
TRAINER_KEYS = {
    "id", "name", "role", "order", "badge", "reference_city",
    "first_battle", "historical_rematch", "blue_strongest", "native_pbs",
}
BLUE_STRONGEST = {
    "status": "BLUE_FULL_POWER_VARIANT_NOT_VERIFIED",
    "species": None, "trainer_type": None, "trainer_name": None,
    "trainer_version": None, "source_sha256": None,
    "game_exe_verified": False,
}
NATIVE_PBS = {
    "status": "NATIVE_PBS_NOT_AVAILABLE_OR_VERIFIED",
    "trainer_type": None, "trainer_name": None, "trainer_version": None,
    "source_file": None, "source_sha256": None, "team": None,
    "compiled": False, "event_bound": False, "game_exe_verified": False,
}
HEADER = re.compile(r"^\[\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*([^,\]\r\n]+?)(?:\s*,\s*(\d{1,3}))?\s*\]$")
POKEMON = re.compile(r"^\s*Pokemon\s*=\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(\d{1,3})(?:\s*(?:#.*)?)?$", re.I)


def fail(message: str) -> None:
    raise ValueError("SINNOH_CH15_BLOQUEADO: " + message)


def read_text(path: Path, *, maximum: int = 8_000_000) -> str:
    if path.is_symlink() or not path.is_file():
        fail("Arquivo de fonte ausente ou symlink: " + str(path))
    if path.stat().st_size > maximum:
        fail("Arquivo excede limite read-only")
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict:
    value = json.loads(read_text(path))
    if not isinstance(value, dict):
        fail("Documento JSON deve ser objeto")
    return value


def cells(line: str) -> list[str]:
    return [v.strip() for v in line.strip().strip("|").split("|")]


def species_symbol(label: str) -> str:
    if label == "Mr. Mime":
        return "MRMIME"
    token = re.sub(r"[^A-Z0-9]", "", label.upper())
    if not token or token[0].isdigit():
        fail("Espécie não reconhecida no documento: " + label)
    return token


def parse_team(cell: str) -> tuple[list[str], list[int]]:
    if not isinstance(cell, str) or not cell:
        fail("Equipe histórica vazia")
    species, levels = [], []
    for item in re.split(r"[,;]", cell):
        match = re.fullmatch(r"\s*(.+?)\s+([0-9]{1,3})\s*", item)
        if not match:
            fail("Formato da equipe histórica inválido: " + item)
        name = species_symbol(match.group(1))
        level = int(match.group(2))
        if not 1 <= level <= 100:
            fail("Nível histórico fora da faixa de referência")
        if name in species:
            fail("Espécie duplicada na equipe histórica: " + name)
        species.append(name)
        levels.append(level)
    if not 1 <= len(species) <= 6:
        fail("Equipe histórica tem cardinalidade inválida")
    return species, levels


def section(text: str, start: str, end: str) -> str:
    a, b = text.find(start), text.find(end, text.find(start) + len(start))
    if a < 0 or b <= a:
        fail("Seção de Platinum ausente: " + start)
    return text[a:b]


def parse_document(text: str) -> list[dict]:
    gym_body = section(text, "## 2. Ginásios", "### 2.1")
    gym_lines = [line for line in gym_body.splitlines()
                 if re.match(r"^\|\s*[1-8]\s+—", line)]
    if len(gym_lines) != 8:
        fail("Detonado deve conter exatamente oito equipes de ginásio")
    result = []
    for i, line in enumerate(gym_lines):
        row = cells(line)
        if len(row) != 6:
            fail("Tabela de ginásios foi modificada")
        marker = re.fullmatch(r"([1-8])\s+—\s+([A-Za-z]+) Badge", row[0])
        name = row[2].split(" — ", 1)[0]
        if not marker or int(marker.group(1)) != i + 1 or name != GYM_NAMES[i]:
            fail("Líder, insígnia ou ordem Platinum divergente")
        badge = marker.group(2).upper()
        if badge != GYM_BADGES[i]:
            fail("Insígnia histórica não corresponde ao líder")
        result.append({
            "id": "SINNOH_" + re.sub(r"[^A-Z0-9]", "_", name.upper()).strip("_"),
            "name": name, "role": "GYM_LEADER", "order": i + 1,
            "badge": badge, "reference_city": row[1],
            "base": parse_team(row[3]), "rematch": None,
        })
    league_body = section(text, "## 8. Elite Four", "**Pontos de QA:**")
    lines = [line for line in league_body.splitlines()
             if re.match(r"^\|\s*(?:[1-4]|Campeã)\s*\|", line)]
    if len(lines) != 5:
        fail("Elite Four/Cynthia incompletos no detonado")
    rematch_body = section(text, "### 8.1 Rematch histórico", "**BLUE:**")
    rematch_rows = [cells(line) for line in rematch_body.splitlines()
                    if re.match(r"^\|\s*(?:Aaron|Bertha|Flint|Lucian|Cynthia)\s*\|", line)]
    if len(rematch_rows) != 5:
        fail("Revanche histórica Elite/Cynthia incompleta")
    for i, (line, rem) in enumerate(zip(lines, rematch_rows)):
        row = cells(line)
        if len(row) != 4 or len(rem) != 2:
            fail("Equipe Elite/Cynthia incompleta")
        expected = ELITE_NAMES[i] if i < 4 else CHAMPION
        if (row[1] != expected or rem[0] != expected or
                row[0] != (str(i + 1) if i < 4 else "Campeã")):
            fail("Ordem ou identidade da Liga Platinum alterada")
        result.append({
            "id": "SINNOH_" + expected.upper(), "name": expected,
            "role": "ELITE_FOUR" if i < 4 else "CHAMPION",
            "order": i + 1 if i < 4 else 1,
            "badge": None, "reference_city": None,
            "base": parse_team(row[3]), "rematch": parse_team(rem[1]),
        })
    return result


def historic_team(team: tuple[list[str], list[int]] | None,
                  source: str) -> dict | None:
    if team is None:
        return None
    return {
        "source": source, "source_game": "POKEMON_PLATINUM",
        "status": "HISTORICAL_REFERENCE_ONLY",
        "species": team[0], "historical_levels": team[1],
        "levels_are_not_runtime_levels": True, "verified_in_blue_pbs": False,
    }


def check_runtime(campaign: str, story: str) -> None:
    for snippet in (
        "master? ? 90 : 70",
        "highest=party.reject(&:egg?).map(&:level).max || 1",
        "GameData::GrowthRate.max_level",
        "pkmn=Marshal.load(Marshal.dump(original));pkmn.level=level",
        "BlueEvolutionScaling.upgrade_trainer!(pkmn)",
        "!BlueCampaign.boss?(trainer)",
        "def self.boss?(trainer)",
        "def self.trainer_level(trainer,party=$player.party)",
    ):
        if snippet not in campaign:
            fail("Regra dinâmica Campaign.rb alterada: " + snippet)
    for snippet in (
        "REGIONAL_BOSS_TYPE =",
        "LEADER|ELITE|ELITEFOUR|CHAMPION",
        "def self.regional_first_boss?(trainers)",
        "def self.with_regional_full_power",
        "BlueStory.regional_first_boss?(args[4])",
        "def self.cap;[350,450,540,nil][stage];end",
    ):
        if snippet not in story:
            fail("Preservação da equipe autoral em Story.rb alterada: " + snippet)


def audit(catalog: dict, walkthrough: str, review: dict,
          regions: dict, strongest: dict, story_trainers: dict,
          campaign: str, story: str) -> dict:
    if not isinstance(catalog, dict) or set(catalog) != TOP_KEYS:
        fail("Campos de catálogo ausentes ou desconhecidos")
    exact_top = {
        "schema": 1, "region": "SINNOH",
        "status": "HISTORICAL_REFERENCE_ONLY_NOT_INSTALLED",
        "reference_game": "PLATINUM", "sources": SOURCES,
        "native_source_available_in_repository": False,
        "native_pbs_compilation_verified": False,
        "native_event_battle_bindings_verified": False,
        "gameplay_verified": False, "can_install": False,
        "may_write_pbs": False, "ui_policy": UI_POLICY,
        "dynamic_balance": BALANCE,
    }
    if any(type(catalog[k]) is not type(expected) or catalog[k] != expected
           for k, expected in exact_top.items()):
        fail("Fonte, política de nível ou verificação nativa adulterada")
    if not isinstance(catalog.get("notes"), str) or len(catalog["notes"]) < 200:
        fail("Nota de limitações insuficiente")
    source = review.get("regions", {}).get("SINNOH", {})
    if (review.get("status") != "REFERENCE_ONLY_NEVER_AUTO_INSTALL" or
            source.get("game") != "Platinum" or
            source.get("leaders") != list(GYM_NAMES) or
            source.get("elite_four") != list(ELITE_NAMES) or
            source.get("champion") != CHAMPION):
        fail("Identidades Platinum divergentes da referência existente")
    if (not isinstance(regions.get("regions"), dict) or
            regions["regions"].get("SINNOH", {}).get("status") != "planned" or
            set(regions["regions"]["SINNOH"].get("milestones", [])) !=
            set(GYM_BADGES)):
        fail("Insígnias da Sinnoh não coincidem com o registro regional")
    # Never silently inherit published strongest teams from OTHER regions.
    if (strongest.get("source", {}).get("path") !=
            "docs/ESTUDO_TIMES_MAIS_FORTES_KANTO_LIDERES_ELITE4_CAMPEOES.md" or
            not isinstance(strongest.get("teams"), list) or
            any(team.get("region") == "SINNOH" for team in strongest["teams"])):
        fail("Catálogo forte Kanto/Johto não prova equipes Sinnoh")
    if (story_trainers.get("source") !=
            "https://github.com/HazyCrazy/Pokemon-Decades/blob/main/PBS/trainers_story_mode.txt" or
            not isinstance(story_trainers.get("masters"), list) or
            any(t.get("name") in GYM_NAMES + ELITE_NAMES + (CHAMPION,)
                for t in story_trainers["masters"] + story_trainers.get("bosses", []))):
        fail("PBS de Decades não pode ser usado como prova Sinnoh")
    expected_trainers = parse_document(walkthrough)
    roster = catalog.get("trainers")
    if not isinstance(roster, list) or len(roster) != 13:
        fail("São exigidos oito líderes, Elite Four e Cynthia")
    for i, (trainer, documented) in enumerate(zip(roster, expected_trainers)):
        if not isinstance(trainer, dict) or set(trainer) != TRAINER_KEYS:
            fail("Campos de treinador ausentes ou desconhecidos")
        for key in ("id", "name", "role", "order", "badge", "reference_city"):
            if type(trainer[key]) is not type(documented[key]) or (
                    trainer[key] != documented[key]):
                fail("Identidade, ordem ou badge histórica divergente: " + key)
        if (trainer["first_battle"] !=
                historic_team(documented["base"], "PLATINUM_FIRST_BATTLE")):
            fail("Primeiro time Platinum divergente de referência: " + trainer["name"])
        if (trainer["historical_rematch"] !=
                historic_team(documented["rematch"], "PLATINUM_LEAGUE_REMATCH")):
            fail("Revanche histórica inexistente/alterada: " + trainer["name"])
        if trainer["blue_strongest"] != BLUE_STRONGEST:
            fail("Time Blue Full Power não pode ser afirmado instalado: " +
                 trainer["name"])
        if trainer["native_pbs"] != NATIVE_PBS:
            fail("Equipe PBS nativa não verificada ou identidade inventada: " +
                 trainer["name"])
    check_runtime(campaign, story)
    return {
        "schema": 1, "region": "SINNOH",
        "historical_gym_leaders": 8, "historical_elite": 4,
        "historical_champions": 1,
        "platinum_historical_rematches": 5,
        "blue_full_power_variants_native_verified": 0,
        "native_pbs_teams_compiled_and_event_bound": 0,
        "native_pbs_compilation_verified": False,
        "native_event_battle_bindings_verified": False,
        "source_document_matches": True,
        "normal_percent": 70, "master_percent": 90,
        "publish_fixed_historical_levels": False,
        "can_install": False, "gameplay_verified": False,
    }


def inspect_pbs_candidates(raw: str, catalog: dict) -> dict:
    """An untrusted optional source *lookup*, never an installed-team proof.

    Accepts Essentials-style 2/3-item section headers and Pokemon lines.
    Rejects duplicate identities and malformed target teams. Never writes to
    the catalog or changes an installed/compiled/verified flag.
    """
    valid_names = {t["name"] for t in catalog["trainers"]}
    sections: dict[tuple[str, str, int], list[str]] = {}
    current = None
    for lineno, line in enumerate(raw.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            m = HEADER.fullmatch(stripped)
            if not m:
                if re.search(r"SINNOH|ROARK|CYNTHIA", stripped, re.I):
                    fail(f"Cabeçalho PBS candidato ilegível na linha {lineno}")
                current = None
                continue
            name = m.group(2).strip()
            current = None
            if name in valid_names:
                identity = (m.group(1), name, int(m.group(3) or 0))
                if identity in sections:
                    fail(f"Identidade PBS repetida: {identity}")
                sections[identity] = []
                current = identity
            continue
        if current and re.match(r"^\s*Pokemon\s*=", line, re.I):
            pkmn = POKEMON.fullmatch(line)
            if pkmn is None:
                fail(f"Linha Pokémon PBS inválida para {current[1]}")
            sections[current].append(pkmn.group(1).upper())
    candidates = []
    for (typ, name, version), species in sorted(sections.items()):
        if not 1 <= len(species) <= 6:
            fail("Equipe candidata PBS vazia ou acima de seis: " + name)
        candidates.append({
            "trainer_type": typ, "trainer_name": name,
            "trainer_version": version, "species": species,
            "status": "UNTRUSTED_PBS_CANDIDATE_NOT_COMPILED",
        })
    return {
        "pbs_candidate_count": len(candidates), "candidates": candidates,
        "native_pbs_teams_compiled_and_event_bound": 0,
        "native_source_verified": False, "gameplay_verified": False,
        "warning": "PBS input is read-only untrusted text. Native compilation and map binding NOT verified.",
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--catalog", type=Path, default=CATALOG)
    cli.add_argument("--walkthrough", type=Path, default=WALKTHROUGH)
    cli.add_argument("--review", type=Path, default=REVIEW)
    cli.add_argument("--regions", type=Path, default=REGIONS)
    cli.add_argument("--strongest", type=Path, default=STRONGEST)
    cli.add_argument("--story-trainers", type=Path, default=STORY_TRAINERS)
    cli.add_argument("--campaign", type=Path, default=CAMPAIGN)
    cli.add_argument("--story", type=Path, default=STORY)
    cli.add_argument("--pbs", type=Path, default=None,
                     help="Optional local PBS source; inspect as untrusted candidates only.")
    args = cli.parse_args()
    try:
        catalog = read_json(args.catalog)
        result = audit(catalog, read_text(args.walkthrough),
                       read_json(args.review), read_json(args.regions),
                       read_json(args.strongest), read_json(args.story_trainers),
                       read_text(args.campaign), read_text(args.story))
        if args.pbs is not None:
            raw = read_text(args.pbs)
            result["pbs_candidate_source_sha256"] = hashlib.sha256(
                raw.encode("utf-8")).hexdigest()
            result["pbs_candidates"] = inspect_pbs_candidates(raw, catalog)
    except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
