import json
from functools import lru_cache
from pathlib import Path

BANK_PATH = Path(__file__).resolve().parents[1] / "data" / "question_bank.json"
DIFFICULTIES = ("basic", "consolidation", "advanced")
FALLBACK_KEY = "_通用"


@lru_cache(maxsize=1)
def _load() -> dict:
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def list_questions(knowledge_point: str | None = None, difficulty: str | None = None) -> list[dict]:
    bank = _load()
    keys = [knowledge_point] if knowledge_point else [k for k in bank if k != FALLBACK_KEY]
    diffs = [difficulty] if difficulty else list(DIFFICULTIES)
    result: list[dict] = []
    for key in keys:
        for diff in diffs:
            for index, item in enumerate(bank.get(key, {}).get(diff, [])):
                result.append({
                    "id": f"{key}-{diff}-{index + 1}",
                    "knowledge_point": key,
                    "difficulty": diff,
                    "question": item["question"],
                    "answer": item["answer"],
                })
    return result


def pick_questions(kp: str, difficulty: str, count: int, offset: int = 0) -> list[dict]:
    bank = _load()
    pool = bank.get(kp, {}).get(difficulty) or bank.get(FALLBACK_KEY, {}).get(difficulty) or []
    return [dict(pool[(offset + index) % len(pool)]) for index in range(count)] if pool else []
