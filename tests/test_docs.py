import re
from pathlib import Path

from app.services.copilot_service import KP_TOPICS
from app.services.question_bank import _load
from main import app

README = Path(__file__).resolve().parents[1] / "README.md"
BUILTIN_ROUTES = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


def _route_paths(routes) -> list[str]:
    paths: list[str] = []
    for route in routes:
        if hasattr(route, "path"):
            paths.append(route.path)
        inner = getattr(route, "original_router", None)
        if inner is not None:
            paths.extend(_route_paths(getattr(inner, "routes", [])))
    return paths


def _normalize(text: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", text)


def test_readme_documents_all_routes():
    readme = _normalize(README.read_text(encoding="utf-8"))
    missing = [
        path
        for path in _route_paths(app.routes)
        if path not in BUILTIN_ROUTES and _normalize(path) not in readme
    ]
    assert not missing, f"routes missing from README: {missing}"


def test_readme_numbers_match_question_bank():
    bank = _load()
    question_count = sum(
        len(items.get(difficulty, []))
        for items in bank.values()
        for difficulty in ("basic", "consolidation", "advanced")
    )
    kp_count = len(KP_TOPICS)

    readme = " ".join(README.read_text(encoding="utf-8").split())
    stated_questions = {int(n) for n in re.findall(r"(\d+) questions", readme)}
    stated_kps = {int(n) for n in re.findall(r"(\d+) knowledge points", readme)} | {
        int(n) for n in re.findall(r"(\d+) KPs", readme)
    }
    assert stated_questions, "README should state the question-bank size"
    assert stated_questions == {question_count}, stated_questions
    assert stated_kps == {kp_count}, stated_kps
