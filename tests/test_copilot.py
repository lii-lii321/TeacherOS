from tests.test_students import create_student

import app.services.copilot_service as copilot_service

NOTE = "今天讲了二次函数，学生对顶点式理解一般，做了10道题错了3道"


async def test_lesson_note_creates_records(client):
    student = await create_student(client)
    resp = await client.post(
        "/copilot/lesson-note",
        json={"student_id": student["id"], "note": NOTE},
    )
    assert resp.status_code == 200
    data = resp.json()

    structured = data["structured"]
    assert structured["topic"] == "二次函数"
    assert "二次函数" in structured["knowledge_points"]
    assert "讲了二次函数" not in structured["knowledge_points"]
    assert structured["error_stats"]["total"] == 10
    assert structured["error_stats"]["wrong"] == 3
    assert structured["error_stats"]["accuracy"] == 70

    assert "二次函数" in data["parent_message"]
    assert "张同学家长您好" in data["parent_message"]

    assert data["session"]["ai_generated"] is True
    assert data["session"]["structured"]["topic"] == "二次函数"
    assert len(data["homework"]["items"]) >= 5
    assert data["homework_estimated_minutes"] > 0

    plan = data["next_lesson_plan"]
    assert plan["review"] == ["二次函数"]
    assert "二次函数" in plan["message"]
    assert plan["estimated_minutes"] > 0


async def test_lesson_note_updates_mastery(client):
    student = await create_student(client)
    resp = await client.post(
        "/copilot/lesson-note", json={"student_id": student["id"], "note": NOTE}
    )
    assert resp.status_code == 200

    profile = (await client.get(f"/students/{student['id']}/profile")).json()
    kps = {kp["name"]: kp["mastery"] for kp in profile["knowledge_points"]}
    assert kps.get("二次函数") == 60


async def test_lesson_note_dry_run(client):
    student = await create_student(client)
    resp = await client.post(
        "/copilot/lesson-note",
        json={"student_id": student["id"], "note": NOTE, "create_records": False},
    )
    data = resp.json()
    assert data["session"] is None
    assert data["homework"] is None
    assert (await client.get("/classes")).json() == []


async def test_multiple_knowledge_points_detected(client):
    student = await create_student(client)
    note = "复习了一次函数和几何证明，函数图像画得不错，证明过程薄弱"
    resp = await client.post(
        "/copilot/lesson-note",
        json={"student_id": student["id"], "note": note, "create_records": False},
    )
    kps = resp.json()["structured"]["knowledge_points"]
    assert "一次函数" in kps
    assert "几何证明" in kps
    assert resp.json()["structured"]["performance_score"] == 2


async def test_lesson_note_homework_questions_vary(client):
    student = await create_student(client)
    first = (
        await client.post("/copilot/lesson-note", json={"student_id": student["id"], "note": NOTE})
    ).json()
    second = (
        await client.post("/copilot/lesson-note", json={"student_id": student["id"], "note": NOTE})
    ).json()

    first_questions = [item["question"] for item in first["homework"]["items"]]
    second_questions = [item["question"] for item in second["homework"]["items"]]
    assert first_questions and second_questions
    assert first_questions != second_questions


class FakeLLM:
    name = "openai"

    def __init__(self, content: str):
        self.content = content

    async def complete(self, system: str, user: str) -> str:
        return self.content


def _with_provider(monkeypatch, content: str) -> None:
    monkeypatch.setattr(copilot_service, "get_provider", lambda: FakeLLM(content))


DUPLICATE_REPLY = (
    '{"topic": "二次函数", "knowledge_points": ["二次函数", "二次函数", " 一元二次方程 ", ""],'
    '"performance_score": 2, "problems": ["计算粗心"], "suggestions": ["多做真题"]}'
)


async def test_enrich_dedups_and_cleans_knowledge_points(monkeypatch):
    _with_provider(monkeypatch, DUPLICATE_REPLY)
    base = copilot_service.build_structured("今天讲了二次函数，做10题错3题")
    merged = await copilot_service.enrich_with_llm("今天讲了二次函数", base)

    assert merged["ai_enriched"] is True
    assert merged["knowledge_points"] == ["二次函数", "一元二次方程"]
    assert merged["performance_score"] == 2


HIGH_PERF_REPLY = (
    '{"topic": "一次函数", "knowledge_points": ["一次函数", "二次函数"],'
    '"performance_score": 4, "problems": [], "suggestions": []}'
)


async def test_enrich_recomputes_weak_from_merged_kps(monkeypatch):
    _with_provider(monkeypatch, HIGH_PERF_REPLY)
    base = copilot_service.build_structured("复习了全等三角形，孩子表现很好")
    merged = await copilot_service.enrich_with_llm("复习了全等三角形", base)

    assert merged["knowledge_points"] == ["一次函数", "二次函数"]
    assert merged["performance_score"] == 4
    assert merged["weak_knowledge_points"] == ["一次函数"]


async def test_enrich_invalid_json_falls_back_to_rules(monkeypatch):
    _with_provider(monkeypatch, "抱歉，我无法解析这段笔记。")
    base = copilot_service.build_structured(NOTE)
    merged = await copilot_service.enrich_with_llm(NOTE, base)

    assert merged == base
    assert merged["ai_enriched"] is False
