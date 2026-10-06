"""TeacherOS dashboard — MUJI-minimal Streamlit UI over the FastAPI backend.

Run:
    uvicorn main:app --port 8000        # terminal 1
    streamlit run dashboard.py          # terminal 2
"""

import httpx
import streamlit as st

st.set_page_config(page_title="TeacherOS", page_icon="📘", layout="wide")

NAVY = "#1a365d"
SLATE = "#334155"
LIGHT = "#f7fafc"
TIMEOUT = 8.0

st.markdown(
    f"""
    <style>
        .stApp {{ background: {LIGHT}; color: {SLATE}; }}
        h1, h2, h3 {{ color: {NAVY}; }}
        div[data-testid="stMetricValue"] {{ color: {SLATE}; }}
        div[data-testid="stMetricLabel"] {{ color: {SLATE}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("TeacherOS")
    st.caption("独立教师的教学与经营工作台")
    page = st.radio("页面", ["总览", "学生", "AI 助教", "经营"], label_visibility="collapsed")


def _error(context: str, exc: Exception):
    st.error(f"{context} 失败（确认已启动 `uvicorn main:app --port 8000`）：{exc}")


def fetch_students():
    try:
        resp = httpx.get("http://127.0.0.1:8000/students", timeout=TIMEOUT, follow_redirects=False)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        _error("读取学生", exc)
        return None


def fetch_profile(student_id: int):
    try:
        resp = httpx.get(
            f"http://127.0.0.1:8000/students/{student_id}/profile",
            timeout=TIMEOUT,
            follow_redirects=False,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        _error("读取画像", exc)
        return None


def fetch_summary(month: str):
    params = {"month": month} if month else None
    try:
        resp = httpx.get(
            "http://127.0.0.1:8000/business/summary",
            params=params,
            timeout=TIMEOUT,
            follow_redirects=False,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        _error("读取经营数据", exc)
        return None


def create_lesson_note(student_id: int, note: str, create_records: bool):
    try:
        resp = httpx.post(
            "http://127.0.0.1:8000/copilot/lesson-note",
            json={"student_id": student_id, "note": note, "create_records": create_records},
            timeout=30.0,
            follow_redirects=False,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        _error("生成课程记录", exc)
        return None


def load_students():
    return fetch_students() or []


if page == "总览":
    st.header("总览")
    summary = fetch_summary("")
    students = load_students()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("在读学生", len(students))
    with col2:
        st.metric("本月收入", f"¥{summary['income']:.0f}" if summary else "-")
    with col3:
        st.metric("本月课时", summary["class_count"] if summary else "-")
    with col4:
        avg = summary.get("avg_price") if summary else None
        st.metric("平均课单价", f"¥{avg:.0f}" if avg else "-")

    st.subheader("学生列表")
    if students:
        st.dataframe(
            [{"姓名": s["name"], "年级": s["grade"], "科目": s["subject"],
              "当前": s["current_score"], "目标": s["target_score"]} for s in students],
            use_container_width=True,
        )
    else:
        st.info("还没有学生，先在 API 里创建一个（POST /students）。")


elif page == "学生":
    st.header("学生画像")
    students = load_students()
    if not students:
        st.info("暂无学生")
        st.stop()
    names = {f"{s['name']}（{s['grade']}{s['subject']}）": s["id"] for s in students}
    chosen = st.selectbox("选择学生", list(names))
    profile = fetch_profile(names[chosen])

    if profile:
        col1, col2, col3 = st.columns(3)
        with col1:
            acc = profile["recent_accuracy"]
            st.metric("最近作业正确率", f"{acc * 100:.0f}%" if acc is not None else "暂无")
        with col2:
            st.metric("课时数", profile["session_count"])
        with col3:
            st.metric("作业次数", profile["homework_count"])

        st.subheader("知识点掌握度")
        for kp in profile["knowledge_points"]:
            st.write(f"**{kp['name']}** — {kp['mastery']}%")
            st.progress(kp["mastery"] / 100)

        if profile["weak_points"]:
            st.warning("薄弱点：" + "、".join(profile["weak_points"]))


elif page == "AI 助教":
    st.header("AI 助教 · 一句话课程记录")
    students = load_students()
    if not students:
        st.info("暂无学生")
        st.stop()
    names = {f"{s['name']}（{s['grade']}{s['subject']}）": s["id"] for s in students}
    chosen = st.selectbox("选择学生", list(names))
    note = st.text_area(
        "课后笔记",
        value="今天讲了二次函数，学生对顶点式理解一般，做了10道题错了3道",
        height=120,
    )
    create_records = st.checkbox("同时创建课程记录与作业", value=True)

    if st.button("生成", type="primary"):
        result = create_lesson_note(names[chosen], note, create_records)
        if result:
            structured = result["structured"]
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("结构化结果")
                st.write(f"**主题**：{structured.get('topic') or '-'}")
                st.write(f"**知识点**：{'、'.join(structured.get('knowledge_points') or []) or '-'}")
                st.write(f"**课堂表现**：{structured.get('performance_score')} / 5")
                errors = structured.get("error_stats") or {}
                if errors.get("accuracy") is not None:
                    st.write(f"**练习正确率**：{errors['accuracy']}%")
                st.write("**建议**")
                for tip in structured.get("suggestions") or []:
                    st.write(f"- {tip}")
            with col2:
                st.subheader("家长微信消息（可直接复制）")
                st.text_area("", value=result["parent_message"], height=240, key="parent_msg")
                if result.get("homework"):
                    st.caption(
                        f"已布置 {len(result['homework']['items'])} 题，"
                        f"预计 {result['homework_estimated_minutes']} 分钟"
                    )

            if not structured.get("ai_enriched"):
                st.caption("本结果由规则解析生成（AI 增强不可用），字段可能不完整。")

            plan = result.get("next_lesson_plan") or {}
            if plan.get("message"):
                st.subheader("下节课计划")
                st.write(plan["message"])
                parts = []
                if plan.get("review"):
                    parts.append("复习：" + "、".join(plan["review"]))
                if plan.get("practice"):
                    parts.append("巩固：" + "、".join(plan["practice"]))
                if plan.get("estimated_minutes"):
                    parts.append(f"预计 {plan['estimated_minutes']} 分钟")
                if parts:
                    st.caption(" ｜ ".join(parts))


elif page == "经营":
    st.header("经营")
    month = st.text_input("月份（YYYY-MM，留空为当月）", value="")
    summary = fetch_summary(month)
    if summary:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("收入", f"¥{summary['income']:.0f}")
            st.metric("支出", f"¥{summary['expense']:.0f}")
        with col2:
            st.metric("活跃学生", summary["active_students"])
            st.metric("新增学生", summary["new_students"])
        with col3:
            st.metric("课时数", summary["class_count"])
            rps = summary.get("revenue_per_student")
            st.metric("生均收入", f"¥{rps:.0f}" if rps else "-")
