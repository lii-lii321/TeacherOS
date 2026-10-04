async def test_healthz(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["app"] == "TeacherOS"
    assert resp.json()["docs"] == "/docs"
