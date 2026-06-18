from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import Base, engine
from app.routes import auth, jobs, resumes

Base.metadata.create_all(bind=engine)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="NLP Resume Screening System", version="2.0.0")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(resumes.router, prefix="/api")

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


def _page(name: str):
    return FileResponse(FRONTEND / name)


@app.get("/")
def root(): return _page("login.html")

@app.get("/register")
def register_page(): return _page("register.html")

@app.get("/dashboard")
def dashboard(): return _page("dashboard.html")

@app.get("/jobs-page")
def jobs_page(): return _page("jobs.html")

@app.get("/settings-page")
def settings_pg(): return _page("settings.html")

@app.get("/health")
def health(): return {"status": "ok"}
