"""Verify that the actual Pages staging allowlist excludes JCR inputs and fixtures."""
from pathlib import Path
import shlex
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_journal_metrics import validate_public_projection
import json

workflow = (ROOT / ".github/workflows/deploy.yml").read_text()
copy_lines = [line.strip() for line in workflow.splitlines() if line.strip().startswith("cp ") and "_site/" in line]
assert len(copy_lines) == 1, "Review the Pages staging command"
command = shlex.split(copy_lines[0])
assert command[:3] == ["cp", "-r", "--"] and command[-1] == "_site/", "Review the Pages staging command"
sources = command[3:-1]
assert set(sources) == {"*.html", "assets", "data", "robots.txt", ".nojekyll"}, "Review the Pages input allowlist"
assert '--for-deploy --site-dir _site' in workflow, "Pages must run the staged public projection check"
registry = ROOT / "data/journals.json"
validate_public_projection(json.loads(registry.read_text()))
for source in ("data", "assets"):
    for path in (ROOT / source).rglob("*"):
        if path.is_file() and path.suffix in (".json", ".js", ".csv", ".xlsx"):
            assert path.suffix not in (".csv", ".xlsx"), f"Unexpected input file in Pages tree: {path.relative_to(ROOT)}"
            content = path.read_text()
            assert not any(marker in content for marker in ("example.invalid/synthetic-fixture", "Synthetic Vision Category")), (
                f"Synthetic fixture in Pages tree: {path.relative_to(ROOT)}")
print("Pages staging allowlist excludes test fixtures and review inputs; public registry validated.")
