"""Validate inline JavaScript from the self-contained local Johto editor."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
page=(ROOT/"web/johto-map-editor.html").read_text("utf-8")
scripts=re.findall(r"<script>(.*?)</script>",page,re.S)
assert len(scripts)==1,"Expected exactly one inline local editor script"
assert page.count("__JOHTO_CSRF__")==1
assert 'id="mapCanvas"' in page and 'id="paletteCanvas"' in page
assert 'id="publish"' in page and 'id="save"' in page
assert "'/api/publish'" in scripts[0] and "'/api/save'" in scripts[0]
node=shutil.which("node")
assert node,"Node.js must be available for JS syntax test"
with tempfile.TemporaryDirectory() as temp:
    target=Path(temp)/"johto-map-editor.js"
    target.write_text(scripts[0],encoding="utf-8")
    subprocess.run([node,"--check",str(target)],check=True)
print("Johto Map Studio inline JavaScript: syntax PASS")
