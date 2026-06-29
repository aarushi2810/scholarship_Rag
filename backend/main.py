"""FastAPI app for ScholarMatch AI."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth.routes import router as auth_router
from backend.db.postgres import init_db
from backend.routes.dashboard import router as dashboard_router
from backend.routes.profile import router as profile_router
from backend.routes.recommendations import router as recommendations_router
from backend.routes.saved import router as saved_router
from backend.routes.schemes import router as schemes_router
from backend.routes.chat import router as chat_router

app = FastAPI(title="ScholarMatch AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()



@app.get("/")

async def root():

    return {"status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(schemes_router)
app.include_router(recommendations_router)
app.include_router(saved_router)
app.include_router(dashboard_router)
app.include_router(chat_router)

