import json
import re
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClassSession, Homework, Student
from app.services import mastery_service, question_bank
from app.services.llm.provider import get_provider

KP_TOPICS = [
    "有理数", "整式", "一元一次方程", "几何图形初步", "相交线与平行线",
    "实数", "平面直角坐标系", "二元一次方程组", "不等式", "数据的收集与整理",
    "分式", "反比例函数", "勾股定理", "平行四边形", "一次函数",
    "二次函数", "圆", "概率", "相似三角形", "全等三角形",
    "锐角三角函数", "因式分解", "轴对称", "统计", "几何证明",
]

PERF_PATTERNS = [
    (r"较差|薄弱|不会|没掌握|不牢|错误多|容易错|吃力|跟不上", 2),
    (r"一般|还行|马马虎虎", 3),
    (r"良好|不错|还可以", 4),
    (r"很好|掌握得?好|熟练|优秀|出色", 5),
]

PERF_DESC = {
    1: "还需要较多关注",
    2: "还有提升空间，需要重点巩固",
    3: "总体正常",
    4: "比较不错",
    5: "相当好",
}

LLM_SYSTEM = (
    "You are a teaching assistant. Extract structured info from a Chinese tutor's "
    "lesson note. Reply with ONLY a JSON object with keys: topic (str), "
    "knowledge_points (list[str], Chinese), performance_score (int 1-5), "
    "problems (list[str], Chinese), suggestions (list[str], Chinese)."
)


def extract_knowledge_points(note: str) -> list[str]:
    found: list[str] = []
    for kp in KP_TOPICS:
        if kp in note:
            found.append(kp)
    for match in re.finditer(r"[\u4e00-\u9fa5A-Za-z]{1,4}函数", note):
        text = match.group(0)
        for verb in ("复习了", "学习了", "讲了", "复习", "学习", "讲", "了"):
            if text.startswith(verb) and len(text) > len(verb) + 1:
                text = text[len(verb):]
                break
        if any(topic in text for topic in found):
            continue
        if text not in found:
            found.append(text)
    return found[:12]


def detect_performance(note: str) -> int:
    for pattern, score in PERF_PATTERNS:
        if re.search(pattern, note):
            return score
    return 3


def extract_error_stats(note: str) -> dict | None:
    match = re.search(r"(\d+)\s*道[题习题]?.{0,8}?错(?:了)?\s*(\d+)", note)
    if match:
        total, wrong = int(match.group(1)), int(match.group(2))
        accuracy = round((total - wrong) / total * 100) if total > 0 else None
        return {"total": total, "wrong": wrong, "accuracy": accuracy}
    match = re.search(r"错(?:了)?\s*(\d+)\s*道", note)
    if match:
        return {"total": None, "wrong": int(match.group(1)), "accuracy": None}
    return None


def extract_topic(note: str, knowledge_points: list[str]) -> str:
    if knowledge_points:
        return knowledge_points[0]
    match = re.search(r"(?:讲了?|复习了?|学习了?)\s*([\u4e00-\u9fa5A-Za-z0-9]{2,10})", note)
    return match.group(1) if match else ""


def build_structured(note: str) -> dict:
    kps = extract_knowledge_points(note)
    perf = detect_performance(note)
    errors = extract_error_stats(note) or {}
    topic = extract_topic(note, kps)

    problems: list[str] = []
    if perf <= 2 and kps:
        problems.append(f"{'、'.join(kps[:3])}掌握不牢固，需要专项巩固")
    accuracy = errors.get("accuracy")
    if accuracy is not None and accuracy < 70:
        problems.append(f"课堂练习正确率约 {accuracy}%，基础概念和计算需要加强")
    if not problems:
        problems.append("暂无明显问题，保持当前节奏")

    suggestions: list[str] = []
    if kps:
        suggestions.append(f"下节课优先复习「{kps[0]}」")
    if perf <= 3 and kps:
        suggestions.append(f"针对「{kps[-1]}」增加巩固练习")
    suggestions.append("课后作业按时完成，教师批改后更新学情")

    structured = {
        "topic": topic,
        "knowledge_points": kps,
        "performance_score": perf,
        "error_stats": errors,
        "problems": problems,
        "suggestions": suggestions,
        "ai_enriched": False,
    }
    weak = kps if perf <= 3 else kps[:1]
    structured["weak_knowledge_points"] = weak
    return structured


async def enrich_with_llm(note: str, base: dict) -> dict:
    provider = get_provider()
    if provider.name == "mock":
        return base
    try:
        raw = await provider.complete(LLM_SYSTEM, note)
        data = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
        merged = dict(base)
        if data.get("topic"):
            merged["topic"] = str(data["topic"])[:128]
        if isinstance(data.get("knowledge_points"), list) and data["knowledge_points"]:
            cleaned = [str(k).strip()[:64] for k in data["knowledge_points"]]
            merged["knowledge_points"] = [k for k in dict.fromkeys(cleaned) if k][:12]
        if isinstance(data.get("performance_score"), int) and 1 <= data["performance_score"] <= 5:
            merged["performance_score"] = data["performance_score"]
        if isinstance(data.get("problems"), list):
            merged["problems"] = [str(p) for p in data["problems"]][:8]
        if isinstance(data.get("suggestions"), list):
            merged["suggestions"] = [str(s) for s in data["suggestions"]][:8]
        perf = int(merged.get("performance_score", 3))
        merged["weak_knowledge_points"] = (
            merged["knowledge_points"] if perf <= 3 else merged["knowledge_points"][:1]
        )
        merged["ai_enriched"] = True
        return merged
    except Exception:
        return base


def generate_homework_draft(structured: dict, offset: int = 0) -> list[dict]:
    kps = structured.get("knowledge_points") or []
    weak = structured.get("weak_knowledge_points") or kps[:1]
    items: list[dict] = []

    def add(kp: str, difficulty: str, count: int) -> None:
        picked = question_bank.pick_questions(kp, difficulty, count, offset=offset)
        for index in range(count):
            bank_item = picked[index] if index < len(picked) else None
            entry = {
                "id": len(items) + 1,
                "knowledge_point": kp,
                "difficulty": difficulty,
                "question": bank_item["question"] if bank_item else f"【{kp}·{difficulty}】题目内容待题库接入",
            }
            if bank_item and bank_item.get("answer"):
                entry["answer"] = bank_item["answer"]
            items.append(entry)

    if not kps:
        add("综合", "basic", 5)
        return items
    for kp in weak[:2]:
        add(kp, "basic", 3)
        add(kp, "consolidation", 2)
    add(weak[0] if weak else kps[0], "advanced", 1)
    return items[:12]


def generate_parent_message(student: Student, structured: dict) -> str:
    topic = structured.get("topic") or "本次课程内容"
    perf = int(structured.get("performance_score", 3))
    perf_desc = PERF_DESC.get(perf, "总体正常")
    accuracy = (structured.get("error_stats") or {}).get("accuracy")
    acc_line = f"课堂练习正确率约 {accuracy}%。" if accuracy is not None else ""
    kps = structured.get("knowledge_points") or []
    focus = "、".join(kps[:2]) if kps else "本次课内容"
    homework = structured.get("homework") or {}
    hw_line = (
        f"已根据今天的情况布置了针对性作业（共 {homework.get('count', 0)} 题，"
        f"预计 {homework.get('estimated_minutes', 0)} 分钟），"
    ) if homework else ""
    return (
        f"{student.name}家长您好，今天{student.subject or ''}课已完成。"
        f"本次课主要讲了「{topic}」，孩子整体表现{perf_desc}。{acc_line}"
        f"{hw_line}重点巩固{focus}。下节课我会先检查作业，"
        f"再针对薄弱点做讲解。有任何问题随时联系我。"
    )


def build_next_lesson_plan(structured: dict, weak_names: list[str]) -> dict:
    kps = structured.get("knowledge_points") or []
    review = list(dict.fromkeys(weak_names or kps[:1]))[:2]
    practice = [kp for kp in kps if kp not in review][:2]
    focus = review[0] if review else (practice[0] if practice else "本阶段内容")
    if practice:
        message = f"下节课先复习「{focus}」，再针对「{'、'.join(practice)}」做巩固练习，最后预留 10 分钟小结与答疑。"
    else:
        message = f"下节课先复习「{focus}」，再做巩固练习，最后预留 10 分钟小结与答疑。"
    return {"review": review, "practice": practice, "estimated_minutes": 90, "message": message}


@dataclass
class CopilotOutcome:
    structured: dict
    parent_message: str
    session: ClassSession | None
    homework: Homework | None


async def process_lesson_note(
    db: AsyncSession, student: Student, note: str, create_records: bool = True
) -> CopilotOutcome:
    structured = await enrich_with_llm(note, build_structured(note))

    weak_names = list(structured.get("weak_knowledge_points") or [])
    if create_records:
        await mastery_service.adjust_from_lesson(
            db, student.id, structured.get("knowledge_points") or [], int(structured.get("performance_score", 3))
        )
        lowest = await mastery_service.lowest_mastery(db, student.id, 3)
        weak_names = [kp.name for kp in lowest if kp.mastery < 70] or [kp.name for kp in lowest[:1]]
    structured["next_lesson_plan"] = build_next_lesson_plan(structured, weak_names)

    hw_count = await db.scalar(select(func.count(Homework.id)).where(Homework.student_id == student.id)) or 0
    draft = generate_homework_draft(structured, offset=student.id + hw_count)
    structured["homework"] = {"count": len(draft), "estimated_minutes": len(draft) * 4}
    message = generate_parent_message(student, structured)

    session = homework = None
    if create_records:
        perf = int(structured.get("performance_score", 3))
        session = ClassSession(
            student_id=student.id,
            topic=structured.get("topic", ""),
            raw_note=note,
            structured=structured,
            understanding=perf,
            computation=perf,
            application=perf,
            ai_generated=True,
        )
        db.add(session)
        await db.flush()
        homework = Homework(
            student_id=student.id,
            session_id=session.id,
            title=f"{structured.get('topic') or '课后'}巩固作业",
            items=draft,
        )
        db.add(homework)
        await db.commit()
    return CopilotOutcome(structured=structured, parent_message=message, session=session, homework=homework)
