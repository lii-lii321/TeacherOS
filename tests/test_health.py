from main import app


async def test_healthz(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["app"] == "TeacherOS"
    assert body["version"] == app.version
    assert body["docs"] == "/docs"
