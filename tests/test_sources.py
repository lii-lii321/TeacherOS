import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGETS = (
    [ROOT / "main.py", ROOT / "dashboard.py"]
    + sorted((ROOT / "app").rglob("*.py"))
    + sorted((ROOT / "scripts").rglob("*.py"))
    + sorted((ROOT / "tests").rglob("*.py"))
)


def test_all_python_sources_parse():
    assert len(TARGETS) >= 20, f"unexpectedly few sources found: {TARGETS}"
    for path in TARGETS:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            raise AssertionError(f"source file fails to parse: {path}") from exc
