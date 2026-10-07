from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.auth import seed_default_moderator
from app.dashboard import DASHBOARD_HTML, get_dashboard_html
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


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard() -> HTMLResponse:
    """Serve the embedded single-page dashboard."""
    return HTMLResponse(content=get_dashboard_html())


STATIC_DIR = Path(__file__).resolve().parent / "static"

app.include_router(router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
