from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.auth import seed_default_moderator
from app.database import Base, SessionLocal, engine
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event to create tables and seed default moderator."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_default_moderator(db)
    yield


Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    seed_default_moderator(db)

app = FastAPI(
    title="WhistleDrop",
    description="A confidential, zero-knowledge reporting backend.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
