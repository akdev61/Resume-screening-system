# NLP Resume Screening System

Summary
- FastAPI backend with a vanilla HTML/CSS/JS frontend for uploading PDF resumes, extracting text, and screening/ranking candidates using lightweight NLP.

Tech stack
- Backend: Python 3.11+/FastAPI, Uvicorn, Pydantic, SQLAlchemy
- Database: PostgreSQL, Alembic
- Frontend: Vanilla HTML/CSS/JavaScript (Fetch API)
- Storage: Local filesystem (`uploads/`)
- Dev & Deploy: Docker, docker-compose

Setup & Run (local)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL, SECRET_KEY
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run with Docker
```bash
docker-compose up --build
```


