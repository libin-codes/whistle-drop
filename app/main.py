"""WhistleDrop — confidential, zero-knowledge reporting backend."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WhistleDrop",
    description="A confidential, zero-knowledge reporting backend.",
    version="0.1.0",
)

app.include_router(router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
