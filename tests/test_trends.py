from tests.test_students import create_student

NOTE = "今天讲了二次函数，学生对顶点式理解一般，做了10道题错了3道"


async def add_graded_homework(client, student_id, correct_flags):
    items = [{"knowledge_point": "一次函数"} for _ in correct_flags]
    resp = await client.post("/homework", json={"student_id": student_id, "title": "t", "items": items})
    homework_id = resp.json()["id"]
    resp = await client.post(
        f"/homework/{homework_id}/submit",
        json={"results": [{"item_id": i + 1, "correct": c} for i, c in enumerate(correct_flags)]},
    )
    assert resp.status_code == 200


async def test_trends_full_flow(client):
    student = await create_student(client)
    await add_graded_homework(client, student["id"], [True, True, False])
    await add_graded_homework(client, student["id"], [True, True, True])
    note_resp = await client.post(
        "/copilot/lesson-note", json={"student_id": student["id"], "note": NOTE}
    )
    assert note_resp.status_code == 200

    resp = await client.get(f"/students/{student['id']}/trends")
    assert resp.status_code == 200
    trends = resp.json()

    assert len(trends["accuracy_series"]) == 2
    assert trends["accuracy_series"][0]["accuracy"] == round(2 / 3, 4)
    assert trends["accuracy_series"][1]["accuracy"] == 1.0
    assert trends["accuracy_direction"] == "improving"
    assert len(trends["mastery_logs"]) >= 3
    assert len(trends["recent_sessions"]) == 1
    assert trends["recent_sessions"][0]["topic"] == "二次函数"
    assert "二次函数" in trends["suggestion"]


async def test_trends_insufficient_data(client):
    student = await create_student(client)
    trends = (await client.get(f"/students/{student['id']}/trends")).json()
    assert trends["accuracy_direction"] == "insufficient_data"
    assert trends["accuracy_series"] == []
    assert trends["recent_sessions"] == []


async def test_trends_missing_student_404(client):
    resp = await client.get("/students/999/trends")
    assert resp.status_code == 404


async def test_trends_mastery_logs_window_latest(client):
    student = await create_student(client)
    for _ in range(50):
        await add_graded_homework(client, student["id"], [True])
    await add_graded_homework(client, student["id"], [False])

    trends = (await client.get(f"/students/{student['id']}/trends")).json()
    profile = (await client.get(f"/students/{student['id']}/profile")).json()

    assert len(trends["mastery_logs"]) == 50
    current = {kp["name"]: kp["mastery"] for kp in profile["knowledge_points"]}
    assert trends["mastery_logs"][-1]["mastery"] == current["一次函数"]
