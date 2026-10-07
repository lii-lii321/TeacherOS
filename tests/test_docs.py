import re
from pathlib import Path

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
