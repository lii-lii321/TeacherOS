# TeacherOS

AI teaching & tutoring workbench for independent tutors — student profiles, lesson
records, homework with mastery tracking, an AI copilot that turns one-line lesson
notes into structured records + parent messages, and simple business analytics.

Part of a personal product matrix (TeacherOS → teaching delivery, TutorFlow →
client acquisition CRM, Data Analyst Agent → data-science engine).

## Features (v0.3)

- **Students** — CRUD, archive, target-vs-current scores, aggregate profile
  (knowledge-point mastery, weak points, recent homework accuracy).
- **AI Copilot** — paste a raw lesson note (`今天讲了二次函数，学生顶点式理解一般，做10题错3题`);
  the copilot extracts topic/knowledge points/performance/error stats, drafts
  homework, generates a parent-ready WeChat message, **updates knowledge-point
  mastery from the lesson signal, and produces a next-lesson plan** (review +
  practice + suggested flow). Rule-based by default (zero API key needed),
  optionally enriched by any OpenAI-compatible LLM.
- **Question bank & auto-grading** — 159 questions covering all 25 knowledge
  points (3 basic / 2 consolidation / 1 advanced each, plus a generic fallback
  pool). Copilot drafts pull real questions, and `/homework/{id}/submit-answers`
  grades student answers automatically (normalized string match with numeric
  fallback, decimal points preserved).
- **Homework & mastery engine** — per-item grading updates knowledge-point
  mastery via an EWMA update (`new = 0.7*old + 0.3*observed`), bounded to
  5–95. Re-grading an already graded homework is rejected with 409.
- **Business** — payments, monthly income/expense, active/new students,
  average price per class.

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
.venv\Scripts\uvicorn main:app --reload --port 8000
```

Open http://127.0.0.1:8000/docs for the interactive API.

Seed demo data:

```bash
.venv\Scripts\python scripts\seed_demo.py
```

Optional LLM enrichment (any OpenAI-compatible endpoint, e.g. DeepSeek/Qwen/GLM):

```bash
copy .env.example .env   # then edit TEACHEROS_LLM_* values
```

Dashboard (optional, MUJI-style Streamlit UI):

```bash
.venv\Scripts\pip install -r requirements-dashboard.txt
.venv\Scripts\streamlit run dashboard.py
```

## Architecture

```
main.py                  FastAPI entry (routers, CORS, lifespan create_all)
app/
├── config.py            pydantic-settings (TEACHEROS_* env)
├── database.py          async SQLAlchemy engine/session (SQLite dev, MySQL-ready)
├── models/              Student, KnowledgePoint, ClassSession, Homework, MasteryLog, Payment
├── schemas/             Pydantic v2 request/response models
├── routers/             students / classes / copilot / homework / business / questions
├── services/
│   ├── copilot_service.py    note → structured extraction → homework draft → parent msg
│   ├── mastery_service.py    EWMA mastery updates + profile aggregation
│   ├── homework_service.py   grading pipeline + answer matching
│   ├── question_bank.py      bank loader (filter / pick with generic fallback)
│   ├── trend_service.py      accuracy series, mastery history, suggestions
│   ├── business_service.py   monthly summary
│   └── llm/                  provider abstraction: mock | openai-compatible
├── data/
│   └── question_bank.json    159 questions across 25 KPs + generic pool
└── utils/
tests/                   pytest + httpx against in-memory SQLite
scripts/seed_demo.py     demo students/sessions/payments
dashboard.py             Streamlit UI
```

## API overview

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | app name, version, docs link |
| GET | `/healthz` | liveness probe |
| POST/GET/PATCH/DELETE | `/students` | manage students (DELETE = archive) |
| GET | `/students/{id}/profile` | mastery, weak points, recent accuracy |
| GET | `/students/{id}/trends` | accuracy series + direction, mastery history, recent sessions |
| POST/GET | `/classes` | lesson records |
| GET | `/classes/{id}` | single lesson record |
| POST | `/copilot/lesson-note` | note → session + homework + parent message |
| POST/GET | `/homework` | create homework (items may carry `answer` for auto-grading) / list (filter by `student_id`) |
| GET | `/homework/{id}` | homework detail with items |
| POST | `/homework/{id}/submit` | grade items manually, update mastery |
| POST | `/homework/{id}/submit-answers` | auto-grade by comparing answers (needs answer key) |
| POST/GET | `/payments` | record / list payments (filter by `student_id`) |
| GET | `/business/summary?month=YYYY-MM` | income, active students, avg price |
| GET | `/questions` | question bank (filter by `knowledge_point`, `difficulty`) |

## Roadmap

- [x] Phase 1 MVP — students, sessions, copilot note parsing, parent messages
- [x] Phase 2 — mastery engine, lesson-signal adjustments, mastery history, trends endpoint
- [x] Phase 3 (start) — next-lesson plan generation in copilot
- [x] Question bank — 159 questions across all 25 knowledge points, copilot
  drafts pull real questions, `/homework/{id}/submit-answers` auto-grades
- [ ] Phase 3 (rest) — multi-step copilot (note → plan → homework → feedback loop)
- [ ] Phase 4 — renewal/retention analytics, source tracking
- [ ] Phase 5 — real users (first 10 tutors)

## Testing

```bash
.venv\Scripts\python -m pytest -q
```
