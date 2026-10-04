from tests.test_students import create_student


async def test_create_and_list_sessions(client):
    student = await create_student(client)
    resp = await client.post(
        "/classes",
        json={"student_id": student["id"], "topic": "二次函数", "understanding": 4},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["ai_generated"] is False
    assert body["structured"] == {}

    listed = await client.get("/classes", params={"student_id": student["id"]})
    assert len(listed.json()) == 1


async def test_create_for_missing_student(client):
    resp = await client.post("/classes", json={"student_id": 999})
    assert resp.status_code == 404


async def test_get_missing_session(client):
    resp = await client.get("/classes/999")
    assert resp.status_code == 404
