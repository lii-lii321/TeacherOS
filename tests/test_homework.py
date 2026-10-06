from app.services.homework_service import check_answer
from app.services.mastery_service import MASTERY_MAX, MASTERY_MIN
from tests.test_students import create_student


def test_check_answer_keeps_decimal_point():
    assert check_answer("8.5", "8.5") is True
    assert check_answer("85", "8.5") is False
    assert check_answer("5", "0.5") is False
    assert check_answer("答案是85", "答案是8.5") is False
    assert check_answer("x=1.25", "1.25") is True
    assert check_answer("π≈3.14", "3.14") is True
    assert check_answer("8.50", "8.5") is True
    assert check_answer("8．5", "8.5") is True


def test_check_answer_basic_equivalence():
    assert check_answer("x=3", "3") is True
    assert check_answer("答案 3。", "3") is True
    assert check_answer("不知道", "3") is False
    assert check_answer(None, "3") is False


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


async def test_submit_rejects_unknown_item_ids(client):
    student = await create_student(client)
    homework = await create_homework(client, student["id"])
    resp = await client.post(
        f"/homework/{homework['id']}/submit",
        json={"results": [{"item_id": 1, "correct": True}, {"item_id": 99, "correct": True}]},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "results contain unknown or duplicate item_id"


async def test_submit_rejects_duplicate_item_id(client):
    student = await create_student(client)
    homework = await create_homework(client, student["id"])
    resp = await client.post(
        f"/homework/{homework['id']}/submit",
        json={"results": [{"item_id": 1, "correct": True}, {"item_id": 1, "correct": False}]},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "results contain unknown or duplicate item_id"


async def test_submit_missing_homework_404(client):
    resp = await client.post("/homework/999/submit", json={"results": [{"item_id": 1, "correct": True}]})
    assert resp.status_code == 404


async def test_submit_caps_mastery_at_max(client):
    student = await create_student(client)
    homework = await create_homework(client, student["id"])
    results = [
        {"item_id": 1, "correct": True},
        {"item_id": 2, "correct": True},
        {"item_id": 3, "correct": True},
    ]
    for _ in range(15):
        resp = await client.post(f"/homework/{homework['id']}/submit", json={"results": results})
        assert resp.status_code == 200
    profile = (await client.get(f"/students/{student['id']}/profile")).json()
    kps = {kp["name"]: kp["mastery"] for kp in profile["knowledge_points"]}
    assert kps["一次函数"] == MASTERY_MAX
    assert kps["几何证明"] == MASTERY_MAX


async def test_submit_floors_mastery_at_min(client):
    student = await create_student(client)
    homework = await create_homework(client, student["id"])
    results = [
        {"item_id": 1, "correct": False},
        {"item_id": 2, "correct": False},
        {"item_id": 3, "correct": False},
    ]
    for _ in range(15):
        resp = await client.post(f"/homework/{homework['id']}/submit", json={"results": results})
        assert resp.status_code == 200
    profile = (await client.get(f"/students/{student['id']}/profile")).json()
    kps = {kp["name"]: kp["mastery"] for kp in profile["knowledge_points"]}
    assert kps["一次函数"] == MASTERY_MIN
    assert kps["几何证明"] == MASTERY_MIN


async def test_list_homework_filters_by_student(client):
    first = await create_student(client, name="甲同学")
    second = await create_student(client, name="乙同学")
    await create_homework(client, first["id"])
    await create_homework(client, second["id"])

    listed = await client.get("/homework")
    assert {hw["student_id"] for hw in listed.json()} == {first["id"], second["id"]}

    only_first = await client.get("/homework", params={"student_id": first["id"]})
    assert [hw["student_id"] for hw in only_first.json()] == [first["id"]]
