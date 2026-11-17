#!/usr/bin/env python3
"""Unova E08: an honest, read-only readiness report; never approves gameplay.

No Game.exe is launched, no installed maps/saves are modified, and no
license or QA may be inferred from the presence of a JSON/Markdown file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from audit_unova_u03_catalog import validate as validate_areas
from audit_unova_e06_e07 import validate as validate_resources

ROOT = Path(__file__).resolve().parents[2]


def inspect(root: Path = ROOT) -> dict:
    root = Path(root).absolute()
    paths = {
        "areas": root/"data/regions/unova-u03-areas.json",
        "resources": root/"data/regions/unova-e06-e07-preparation.json",
        "registry": root/"site/public/data/regions.json",
        "research": root/"docs/UNOVA_PESQUISA_FONTES_RMXP.md",
        "plan": root/"docs/UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md",
        "rxdata_tool": root/"scripts/regions/audit_unova_source_detail.py",
    }
    for name,path in paths.items():
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 3_000_000:
            raise ValueError("E08: arquivo obrigatorio ausente/inseguro: " + name)
    areas = json.loads(paths["areas"].read_text("utf-8-sig"))
    resources = json.loads(paths["resources"].read_text("utf-8-sig"))
    registry = json.loads(paths["registry"].read_text("utf-8-sig"))
    region = registry["regions"]["UNOVA"]
    area_report = validate_areas(areas, region)
    res_report = validate_resources(resources, areas, region)
    if len(paths["research"].read_text("utf-8")) < 1000 or len(paths["plan"].read_text("utf-8")) < 1000:
        raise ValueError("E08: documentacao de pesquisa/plano incompleta")
    # A local file's existence does not constitute a source license or QA signoff.
    has_source = (root/".blue-work/unova/sources/Pokemon_World_V18.zip").is_file()
    stages = [
        {"id":"E01","name":"Pesquisa de fontes publicada","completed":True,"proof":"docs/UNOVA_PESQUISA_FONTES_RMXP.md"},
        {"id":"E02","name":"Plano U01-U32 documentado","completed":True,"proof":"docs/UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md"},
        {"id":"E03","name":"Catalogo simbolico, validador e testes","completed":True,"proof":"data/regions/unova-u03-areas.json"},
        {"id":"E04","name":"ZIP real auditado e proveniencia comprovada","completed":False,"proof":None},
        {"id":"E05","name":"Nomes e eventos reais RXDATA confrontados com Unova","completed":False,"proof":None},
        {"id":"E06","name":"Direitos de assets confirmados por recurso","completed":False,"proof":None},
        {"id":"E07","name":"Catalogo simbolico musical/treinadores e fallbacks documentados","completed":True,"proof":"data/regions/unova-e06-e07-preparation.json"},
        {"id":"E08","name":"Evidencia QA de integracao Game.exe e JoiPlay","completed":False,"proof":None},
    ]
    verified = sum(1 for stage in stages if stage["completed"])
    return {
        "schema":1,"region":"UNOVA","phase":"E08",
        "mode":"READ_ONLY_PROGRESS_WITHOUT_NATIVE_SIGNOFF",
        "status":"PREPARATION_ONLY_EVIDENCE_MISSING",
        "bar_e":{"completed":verified,"total":8,"percent":100*verified/8,"stages":stages},
        "prepared_tooling":{
            "zip_metadata_auditor":(root/"scripts/regions/audit_unova_u02.py").is_file(),
            "inert_rxdata_auditor":True,
            "rights_catalog_checked":res_report["rights_groups_unverified"],
            "symbolic_music_cues":res_report["music_cues"],
            "symbolic_trainer_references":res_report["trainer_references"],
            "symbolic_areas":area_report["catalog_areas"],
        },
        "donor_zip_present_not_audited":has_source,
        "source_map_ids_verified":False,
        "rights_verified":False,
        "game_exe_tested":False,"android_tested":False,
        "playable_phases_completed":0,
        "game_or_saves_modified":False,
        "can_install":False,
        "blockers":[
            "E04 requer ZIP real e documentos de origem, com hashes e inspeção",
            "E05 requer ler MapInfos/MapNNN reais e revisão manual da região",
            "E06 requer direitos por arquivo, não só ficha preparatória",
            "E07 catalogos simbolicos prontos; ainda falta confirmar times, tracks e licencas em fonte real",
            "E08 requer evidências de QA Windows/JoiPlay, não apenas CI",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    args=parser.parse_args(argv)
    try:
        report=inspect(args.project)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 0  # valid blocked/partial reports are successful diagnostics
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print("UNOVA_E08_BLOQUEADO: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
