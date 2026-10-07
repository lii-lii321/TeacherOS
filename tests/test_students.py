async def create_student(client, **overrides):
    payload = {
        "name": "张同学",
        "grade": "初二",
        "subject": "数学",
        "current_score": 80,
        "target_score": 110,
    }
    payload.update(overrides)
    resp = await client.post("/students", json=payload)
    assert resp.status_code == 201
    return resp.json()


async def test_create_get_list(client):
    student = await create_student(client)
    assert student["id"] > 0
    assert student["status"] == "active"

    got = await client.get(f"/students/{student['id']}")
    assert got.status_code == 200
    assert got.json()["name"] == "张同学"

    listed = await client.get("/students")
    assert len(listed.json()) == 1


async def test_update_and_archive(client):
    student = await create_student(client)
    resp = await client.patch(f"/students/{student['id']}", json={"current_score": 85})
    assert resp.json()["current_score"] == 85

    resp = await client.delete(f"/students/{student['id']}")
    assert resp.status_code == 204
    assert (await client.get("/students")).json() == []
    assert len((await client.get("/students", params={"status": "all"})).json()) == 1


async def test_missing_student_404(client):
    resp = await client.get("/students/999")
    assert resp.status_code == 404


async def test_students_invalid_status_422(client):
    resp = await client.get("/students", params={"status": "archiveds"})
    assert resp.status_code == 422


async def test_profile_empty(client):
    student = await create_student(client)
    resp = await client.get(f"/students/{student['id']}/profile")
    data = resp.json()
    assert data["knowledge_points"] == []
    assert data["weak_points"] == []
    assert data["recent_accuracy"] is None
    assert data["homework_count"] == 0
