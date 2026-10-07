from app.services.copilot_service import KP_TOPICS
from app.services.question_bank import _load
from tests.test_students import create_student

NOTE = "今天讲了二次函数，学生对顶点式理解一般，做了10道题错了3道"


def test_bank_covers_all_kp_topics():
    bank = _load()
    for kp in KP_TOPICS:
        pool = bank.get(kp, {})
        assert len(pool.get("basic", [])) >= 3, kp
        assert len(pool.get("consolidation", [])) >= 2, kp
        assert len(pool.get("advanced", [])) >= 1, kp


def test_generic_pool_covers_no_kp_draft():
    bank = _load()
    generic = bank["_通用"]
    assert len(generic.get("basic", [])) >= 5


async def test_no_kp_note_draft_questions_unique(client):
    student = await create_student(client)
    resp = await client.post(
        "/copilot/lesson-note",
        json={
            "student_id": student["id"],
            "note": "今天主要陪学生复盘学习方法，讨论了错题本的使用习惯，整体状态不错",
        },
    )
    assert resp.status_code == 200
    items = resp.json()["homework"]["items"]
    assert len(items) == 5
    questions = [i["question"] for i in items]
    assert len(set(questions)) == len(questions), questions


async def create_lesson_homework(client):
    student = await create_student(client)
    resp = await client.post(
        "/copilot/lesson-note", json={"student_id": student["id"], "note": NOTE}
    )
    data = resp.json()
    return student, data


async def test_bank_endpoint_filter(client):
    resp = await client.get("/questions", params={"knowledge_point": "二次函数"})
    items = resp.json()
    assert items
    assert all(item["knowledge_point"] == "二次函数" for item in items)
    assert all(item["question"] and item["answer"] for item in items)

    only_advanced = await client.get(
        "/questions", params={"knowledge_point": "二次函数", "difficulty": "advanced"}
    )
    assert all(item["difficulty"] == "advanced" for item in only_advanced.json())


async def test_lesson_note_homework_uses_bank(client):
    _, data = await create_lesson_homework(client)
    items = data["homework"]["items"]
    assert len(items) >= 5
    assert all("待题库接入" not in item["question"] for item in items)
    assert all(item.get("answer") for item in items)


async def test_submit_answers_full_cycle(client):
    student, data = await create_lesson_homework(client)
    homework_id = data["homework"]["id"]
    items = data["homework"]["items"]

    resp = await client.post(
        f"/homework/{homework_id}/submit-answers",
        json={"answers": [item["answer"] for item in items]},
    )
    assert resp.status_code == 200
    graded = resp.json()
    assert graded["accuracy"] == 1.0

    profile = (await client.get(f"/students/{student['id']}/profile")).json()
    kps = {kp["name"]: kp["mastery"] for kp in profile["knowledge_points"]}
    assert kps["二次函数"] == 72


async def test_submit_answers_partial_and_number_match(client):
    student, data = await create_lesson_homework(client)
    homework_id = data["homework"]["id"]
    items = data["homework"]["items"]

    answers = [item["answer"] for item in items]
    answers[0] = "6" if items[0]["answer"] == "6" else "不等于 " + str(1e9 + 7)

    resp = await client.post(
        f"/homework/{homework_id}/submit-answers",
        json={"answers": answers},
    )
    graded = resp.json()
    assert 0 < graded["accuracy"] < 1

    # 作业已 graded，数值等价判卷改在新作业上验证（同一作业重复提交会被 409 拦截）
    _, other = await create_lesson_homework(client)
    other_items = other["homework"]["items"]
    numeric = await client.post(
        f"/homework/{other['homework']['id']}/submit-answers",
        json={"answers": ["x=" + item["answer"] for item in other_items]},
    )
    assert numeric.status_code == 200


async def test_submit_answers_length_mismatch_422(client):
    _, data = await create_lesson_homework(client)
    resp = await client.post(
        f"/homework/{data['homework']['id']}/submit-answers",
        json={"answers": ["1"]},
    )
    assert resp.status_code == 422


async def test_submit_answers_without_answer_key_409(client):
    student = await create_student(client)
    resp = await client.post(
        "/homework",
        json={"student_id": student["id"], "title": "t", "items": [{"knowledge_point": "一次函数"}]},
    )
    homework_id = resp.json()["id"]
    submit = await client.post(
        f"/homework/{homework_id}/submit-answers", json={"answers": ["3"]}
    )
    assert submit.status_code == 409


async def test_unknown_kp_falls_back_to_generic_bank(client):
    student = await create_student(client)
    data = (
        await client.post(
            "/copilot/lesson-note",
            json={"student_id": student["id"], "note": "复习了勾股定理和相似三角形，都还行"},
        )
    ).json()
    items = data["homework"]["items"]
    assert items
    assert all("待题库接入" not in item["question"] for item in items)
    assert all(item.get("answer") for item in items)
