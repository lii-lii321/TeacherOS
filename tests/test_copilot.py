from tests.test_students import create_student

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
