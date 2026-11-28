"""Create the Android bootstrap ZIP from an explicit code/documentation allowlist."""
import argparse
import hashlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[2]
MEMBERS = {
    "ATUALIZAR-ANDROID.py": ROOT / "scripts/android/source_bootstrap.py",
    "LEIA-ME.md": ROOT / "docs/ANDROID_INSTALACAO_PELAS_FONTES.md",
}


def build(output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name, path in MEMBERS.items():
            archive.write(path, name)
    with ZipFile(output) as archive:
        if set(archive.namelist()) != MEMBERS.keys() or archive.testzip():
            raise ValueError("O ZIP deve conter só o código inicial e o guia.")
    output.with_suffix(".zip.sha256").write_text(
        hashlib.sha256(output.read_bytes()).hexdigest() + "  " + output.name + "\n", encoding="ascii")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    build(parser.parse_args().output)
