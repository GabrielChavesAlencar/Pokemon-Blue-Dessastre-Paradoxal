"""Move-learning editor for Pokémon Essentials PBS species and alternate forms.

Edits ONLY Moves, TutorMoves and EggMoves within one selected section.
Never writes move definitions or touches another species. No GBA slot limits.
"""
from __future__ import annotations
import re
from pathlib import Path

MOVE_ID = re.compile(r"^[A-Z][A-Z0-9_]{0,79}$")
PBS_SPECIES_FILE = re.compile(r"^pokemon(?:_[A-Za-z0-9_]+)?\.txt$", re.I)
FORM_HEADER = re.compile(r"^([A-Za-z][A-Za-z0-9_]+),(\d+)$")
KEYS = {"level": "Moves", "tutor": "TutorMoves", "egg": "EggMoves"}
FIELD_LINE = re.compile(r"^([ \t]*)(Moves|TutorMoves|EggMoves)[ \t]*=[ \t]*(.*)$", re.I)


class MoveEditorError(ValueError):
    def __init__(self, text: str, status: int = 400):
        super().__init__(text)
        self.status = status


def ensure_species_file(name: str) -> None:
    if (not isinstance(name, str) or not PBS_SPECIES_FILE.fullmatch(name)
            or name.lower().startswith(("pokemon_metrics", "pokemon_forms_metrics"))
            or "/" in name or "\\" in name):
        raise MoveEditorError("Selecione um arquivo de espécies pokemon*.txt válido.")


def species_files(game_root: Path) -> list[Path]:
    folder = game_root / "PBS"
    if not folder.is_dir():
        return []
    return sorted((file for file in folder.glob("pokemon*.txt")
                  if file.is_file() and not file.is_symlink()
                  and PBS_SPECIES_FILE.fullmatch(file.name)
                  and not file.name.lower().startswith("pokemon_metrics")
                  and file.stat().st_size <= 10_000_000),
                  key=lambda f: (f.name != "pokemon.txt", f.name.lower()))


def _header_forms(header: str, file: str) -> bool:
    return file.lower().startswith("pokemon_forms") or bool(FORM_HEADER.fullmatch(header))


def _csv(values: list[str]) -> list[str]:
    parts = []
    for value in values:
        parts.extend(item.strip() for item in value.split(",") if item.strip())
    return parts


def collect_fields(section: str) -> dict[str, list[str]]:
    result = {key: [] for key in KEYS}
    for line in section.splitlines():
        match = FIELD_LINE.match(line)
        if match:
            which = next(key for key, pbs in KEYS.items() if pbs.lower() == match.group(2).lower())
            result[which].append(match.group(3))
    return {key: _csv(value) for key, value in result.items()}


def structured(fields: dict[str, list[str]]) -> dict:
    pairs = fields["level"]
    if len(pairs) % 2:
        raise MoveEditorError("Moves existente possui pares de nível/golpe incompletos.")
    level = []
    for index in range(0, len(pairs), 2):
        try:
            value = int(pairs[index])
        except ValueError as exc:
            raise MoveEditorError("Nível inválido no PBS: " + pairs[index]) from exc
        level.append({"level": value, "move": pairs[index+1].upper()})
    return {"level": level, "tutor": [v.upper() for v in fields["tutor"]],
            "egg": [v.upper() for v in fields["egg"]]}


def find_base(game_root, species_id, *, read_text, sections_in, section_lines):
    """Return moves of the base species, without recursively inheriting or editing."""
    base = FORM_HEADER.fullmatch(species_id)
    if not base:
        return None
    key = base.group(1).upper()
    for file in species_files(game_root):
        if "forms" in file.name.lower():
            continue
        _, source = read_text(file)
        sections = sections_in(source)
        selected = next((s for s in sections if s["id"].upper() == key), None)
        if selected:
            return structured(collect_fields(section_lines(source, selected)))
    return None


def catalog(game_root, *, read_text, sections_in, section_lines):
    species = []
    for file in species_files(game_root):
        _, source = read_text(file)
        for sec in sections_in(source):
            header = sec["id"]
            species.append({"file": file.name, "index": sec["index"], "id": header,
                            "name": sec["label"] or header,
                            "form": _header_forms(header, file.name)})
    moves = {}
    for file in sorted((game_root / "PBS").glob("moves*.txt")) if (game_root / "PBS").is_dir() else ():
        if not file.is_file() or file.is_symlink() or file.stat().st_size > 10_000_000:
            continue
        _, source = read_text(file)
        for sec in sections_in(source):
            move_id = sec["id"].upper()
            if MOVE_ID.fullmatch(move_id):
                moves.setdefault(move_id, sec["label"] or move_id)
    return {"species": species, "moves": [{"id": key, "name": name}
                                          for key, name in sorted(moves.items())]}


def detail(game_root, name: str, index: int, *,
           pbs_path, read_text, sections_in, section_lines, file_hash):
    ensure_species_file(name)
    if type(index) is not int or index < 0:
        raise MoveEditorError("Índice de espécie inválido.")
    file = pbs_path(game_root, name)
    raw, source = read_text(file)
    sections = sections_in(source)
    if index >= len(sections):
        raise MoveEditorError("Espécie não encontrada.", 404)
    section = sections[index]
    own_fields = collect_fields(section_lines(source, section))
    own = structured(own_fields)
    form = _header_forms(section["id"], name)
    base = find_base(game_root, section["id"], read_text=read_text,
                     sections_in=sections_in, section_lines=section_lines) if form else None
    inherited = [field for field in KEYS if form and not own_fields[field]]
    effective = {field: base[field] if field in inherited and base else own[field]
                 for field in KEYS}
    return {"file": name, "index": index, "id": section["id"],
            "name": section["label"] or section["id"], "hash": file_hash(raw),
            "form": form, "inherited": inherited, "own": own, "effective": effective,
            "base": base, "baseAvailable": bool(base)}


def validate_values(body, allowed: set[str], form: bool) -> tuple[dict, set]:
    if not isinstance(body, dict) or not allowed:
        raise MoveEditorError("Catálogo de golpes PBS indisponível.")
    inherit = body.get("inherit", [])
    if not isinstance(inherit, list) or any(v not in KEYS for v in inherit):
        raise MoveEditorError("Campos de herança inválidos.")
    if inherit and not form:
        raise MoveEditorError("Somente formas podem herdar os golpes da espécie base.")
    inherited = set(inherit)
    result = {}
    for field in KEYS:
        values = body.get(field)
        if not isinstance(values, list) or len(values) > 1500:
            raise MoveEditorError("Lista de golpes inválida: " + field)
        normalized = []
        if field == "level":
            for pair in values:
                if not isinstance(pair, dict) or type(pair.get("level")) is not int:
                    raise MoveEditorError("Informe níveis inteiros nos golpes por nível.")
                level = pair["level"]
                if not 1 <= level <= 100:
                    raise MoveEditorError("Níveis dos golpes devem estar entre 1 e 100.")
                move = pair.get("move")
                if not isinstance(move, str) or not MOVE_ID.fullmatch(move.upper()):
                    raise MoveEditorError("ID de golpe inválido.")
                normalized.append({"level": level, "move": move.upper()})
        else:
            for move in values:
                if not isinstance(move, str) or not MOVE_ID.fullmatch(move.upper()):
                    raise MoveEditorError("ID de golpe inválido.")
                normalized.append(move.upper())
        for move in (item["move"] for item in normalized) if field == "level" else normalized:
            if move not in allowed:
                raise MoveEditorError("Golpe não encontrado no PBS do Decades: " + move)
        if field in inherited and normalized:
            raise MoveEditorError("Remova os golpes próprios antes de marcar herança: " + field)
        result[field] = normalized
    return result, inherited


def replace_fields(section: str, values: dict, inherited: set) -> str:
    """Preserve unknown keys, comments, form data, section header and existing line endings."""
    lines = section.splitlines(keepends=True)
    if not lines:
        raise MoveEditorError("Registro PBS vazio.")
    newline = "\r\n" if "\r\n" in section else "\n"
    out, inserted = [], set()
    for line in lines:
        match = FIELD_LINE.match(line.rstrip("\r\n"))
        if not match:
            out.append(line)
            continue
        field = next(key for key, pbs in KEYS.items() if pbs.lower() == match.group(2).lower())
        if field in inserted:
            continue
        inserted.add(field)
        if field in inherited or not values[field]:
            continue
        value = serialize(field, values[field])
        out.append(match.group(1) + KEYS[field] + " = " + value + newline)
    for field in KEYS:
        if field not in inserted and field not in inherited and values[field]:
            if out and not out[-1].endswith(("\n", "\r")):
                out[-1] += newline
            out.append(KEYS[field] + " = " + serialize(field, values[field]) + newline)
    return "".join(out)


def serialize(field: str, values: list) -> str:
    if field == "level":
        return ",".join(f"{pair['level']},{pair['move']}" for pair in values)
    return ",".join(values)


def save(game_root, backups, body, *, pbs_path, read_text, sections_in,
         section_lines, file_hash, save_section):
    if not isinstance(body, dict):
        raise MoveEditorError("Dados inválidos.")
    name = body.get("file", "")
    ensure_species_file(name)
    index = body.get("index")
    selected = detail(game_root, name, index, pbs_path=pbs_path,
                      read_text=read_text, sections_in=sections_in,
                      section_lines=section_lines, file_hash=file_hash)
    if selected["id"] != body.get("id"):
        raise MoveEditorError("Registro alterado desde a leitura. Recarregue.", 409)
    if selected["hash"] != body.get("hash"):
        raise MoveEditorError("Arquivo modificado desde a leitura. Recarregue.", 409)
    move_ids = set()
    for file in sorted((game_root / "PBS").glob("moves*.txt")):
        if file.is_file() and not file.is_symlink():
            _, source = read_text(file)
            move_ids.update(s["id"].upper() for s in sections_in(source))
    values, inherited = validate_values(body, move_ids, selected["form"])
    _, source = read_text(pbs_path(game_root, name))
    original = section_lines(source, sections_in(source)[index])
    updated = replace_fields(original, values, inherited)
    if original == updated:
        return {**selected, "ok": True, "unchanged": True}
    result = save_section(game_root, name, index, selected["hash"], updated, backups)
    return {"ok": True, "unchanged": False, "file": name, "index": result["index"],
            "hash": result["hash"], "id": selected["id"]}
