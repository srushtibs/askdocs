from fastapi import FastAPI
from sqlalchemy import text
from .database import engine, Base
from . import models  # noqa: F401
from .auth import router as auth_router
from .documents import router as documents_router

with engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
Base.metadata.create_all(engine)

app = FastAPI(title="AskDocs")
app.include_router(auth_router)
app.include_router(documents_router)

@app.get("/health")
def health():
    return {"status": "ok"}
