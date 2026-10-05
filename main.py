from contextlib import asynccontextmanager

import app.models  # noqa: F401  (register ORM metadata before create_all)
from app.config import settings
from app.database import Base, engine
from app.routers import business, classes, copilot, homework, questions, students
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title=settings.app_name, version="0.3.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students.router)
app.include_router(classes.router)
app.include_router(copilot.router)
app.include_router(homework.router)
app.include_router(business.router)
app.include_router(questions.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"app": settings.app_name, "version": "0.1.0", "docs": "/docs"}
