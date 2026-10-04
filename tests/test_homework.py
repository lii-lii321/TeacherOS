from tests.test_students import create_student


async def create_homework(client, student_id):
    resp = await client.post(
        "/homework",
        json={
            "student_id": student_id,
            "title": "巩固作业",
            "items": [
                {"knowledge_point": "一次函数", "difficulty": "basic"},
                {"knowledge_point": "一次函数", "difficulty": "basic"},
                {"knowledge_point": "几何证明", "difficulty": "consolidation"},
            ],
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def test_create_get_homework(client):
    student = await create_student(client)
    homework = await create_homework(client, student["id"])
    assert [i["id"] for i in homework["items"]] == [1, 2, 3]
    assert homework["status"] == "assigned"

    got = await client.get(f"/homework/{homework['id']}")
    assert got.json()["title"] == "巩固作业"


async def test_submit_updates_mastery_and_profile(client):
    student = await create_student(client)
    homework = await create_homework(client, student["id"])

    resp = await client.post(
        f"/homework/{homework['id']}/submit",
        json={"results": [
            {"item_id": 1, "correct": True},
            {"item_id": 2, "correct": True},
            {"item_id": 3, "correct": False},
        ]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["accuracy"] == round(2 / 3, 4)

    updates = {u["name"]: u["mastery"] for u in data["knowledge_updates"]}
    assert updates["一次函数"] == 65
    assert updates["几何证明"] == 35

    profile = (await client.get(f"/students/{student['id']}/profile")).json()
    assert profile["recent_accuracy"] == round(2 / 3, 4)
    assert "几何证明" in profile["weak_points"]
    assert profile["homework_count"] == 1


async def test_submit_ignores_unknown_item_ids(client):
    student = await create_student(client)
    homework = await create_homework(client, student["id"])
    resp = await client.post(
        f"/homework/{homework['id']}/submit",
        json={"results": [{"item_id": 1, "correct": True}, {"item_id": 99, "correct": True}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["accuracy"] == 1.0
    updates = {u["name"]: u["mastery"] for u in data["knowledge_updates"]}
    assert updates == {"一次函数": 65}


async def test_submit_missing_homework_404(client):
    resp = await client.post("/homework/999/submit", json={"results": [{"item_id": 1, "correct": True}]})
    assert resp.status_code == 404
