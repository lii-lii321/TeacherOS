from tests.test_students import create_student


async def test_business_summary(client):
    a = await create_student(client, name="A同学")
    b = await create_student(client, name="B同学")

    await client.post("/payments", json={"student_id": a["id"], "amount": 300, "kind": "income"})
    await client.post("/payments", json={"student_id": b["id"], "amount": 200, "kind": "income"})
    await client.post("/payments", json={"student_id": a["id"], "amount": 50, "kind": "expense", "note": "教材"})
    await client.post("/classes", json={"student_id": a["id"], "topic": "复习"})

    resp = await client.get("/business/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["income"] == 500
    assert data["expense"] == 50
    assert data["class_count"] == 1
    assert data["active_students"] == 2
    assert data["new_students"] == 2
    assert data["avg_price"] == 500
    assert data["revenue_per_student"] == 250


async def test_summary_specific_month_empty(client):
    resp = await client.get("/business/summary", params={"month": "2020-01"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["income"] == 0
    assert data["active_students"] == 0
    assert data["avg_price"] is None


async def test_summary_invalid_month(client):
    resp = await client.get("/business/summary", params={"month": "2026-13"})
    assert resp.status_code == 422


async def test_payment_missing_student(client):
    resp = await client.post("/payments", json={"student_id": 999, "amount": 100})
    assert resp.status_code == 404


async def test_payments_list_with_filter(client):
    a = await create_student(client, name="A同学")
    b = await create_student(client, name="B同学")
    await client.post("/payments", json={"student_id": a["id"], "amount": 300, "kind": "income"})
    await client.post("/payments", json={"student_id": b["id"], "amount": 200, "kind": "income"})

    resp = await client.get("/payments")
    assert resp.status_code == 200
    listed = resp.json()
    assert len(listed) == 2
    assert listed[0]["student_id"] == b["id"]
    assert listed[0]["amount"] == 200

    only_a = await client.get("/payments", params={"student_id": a["id"]})
    assert [(p["student_id"], p["amount"]) for p in only_a.json()] == [(a["id"], 300)]


async def test_payment_backfill_occurred_at(client):
    student = await create_student(client, name="补录同学")
    resp = await client.post(
        "/payments",
        json={
            "student_id": student["id"],
            "amount": 300,
            "kind": "income",
            "occurred_at": "2026-01-15T00:00:00",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["occurred_at"].startswith("2026-01-15")
    listed = (await client.get("/payments")).json()
    assert listed[0]["occurred_at"].startswith("2026-01-15")

    january = (await client.get("/business/summary", params={"month": "2026-01"})).json()
    assert january["income"] == 300
    assert january["active_students"] == 1

    current = (await client.get("/business/summary")).json()
    assert current["income"] == 0
