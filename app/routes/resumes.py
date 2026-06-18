import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Job, Resume, ScreeningResult, User
from app.schemas import MessageResponse, ResumeResponse, ScreeningResultResponse
from app.services.nlp import extract_text_from_pdf, score_resume_against_job

router = APIRouter(prefix="/jobs/{crud_id}/resumes", tags=["resumes"])

# 10 MB file size limit (was missing in old version)
MAX_FILE_SIZE = 10 * 1024 * 1024


# ── Shared helper ──────────────────────────────────────────────────────────────

def _get_job(db: Session, crud_id: str, owner_id: int) -> Job:
    """
    Fetch a job by crud_id scoped to the current user.
    Returns 404 whether the job doesn't exist OR belongs to someone else
    (avoids leaking existence of other users' jobs).
    """
    job = db.query(Job).filter(
        Job.crud_id == crud_id,
        Job.owner_id == owner_id,   # ownership check — fixes old version's security bug
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


# ── Routes ─────────────────────────────────────────────────────────────────────
# IMPORTANT: literal path segments (/screen/results) must be declared BEFORE
# parameterised ones (/{resume_id}) — FastAPI matches top-to-bottom.

@router.get("/screen/results", response_model=list[ScreeningResultResponse])
def get_screening_results(
    crud_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return saved screening results for a job, sorted by score descending."""
    job = _get_job(db, crud_id, current_user.id)
    rows = (
        db.query(ScreeningResult, Resume)
        .join(Resume, ScreeningResult.resume_id == Resume.id)
        .filter(ScreeningResult.job_id == job.id)
        .order_by(ScreeningResult.score.desc())
        .all()
    )
    return [
        ScreeningResultResponse(
            id=result.id,
            resume_id=resume.id,
            filename=resume.filename,
            score=result.score,
            matched_keywords=result.matched_keywords,
            screened_at=result.screened_at,
        )
        for result, resume in rows
    ]


@router.get("", response_model=list[ResumeResponse])
def list_resumes(
    crud_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all resumes uploaded for a job, newest first."""
    job = _get_job(db, crud_id, current_user.id)
    return (
        db.query(Resume)
        .filter(Resume.job_id == job.id)
        .order_by(Resume.uploaded_at.desc())
        .all()
    )


@router.post("/upload", response_model=MessageResponse, status_code=201)
async def upload_resumes(
    crud_id: str,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload one or more PDF resumes for a job.

    Fixes vs old version:
    - Validates ALL files before saving any (no partial-failure disk orphans)
    - File size check (10 MB cap) — was in old version, missing in ours
    - Each file gets its own Resume row (old version crammed all into one row)
    - Upload and screening are separate — no auto-screening on upload
    - Job ID in URL path, not a Form field
    - Ownership check via _get_job()
    """
    if not files:
        raise HTTPException(400, "No files provided")

    # ── Pass 1: validate everything before touching disk ──────────────────────
    file_contents: list[tuple[str, bytes]] = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"Only PDF files are allowed: '{f.filename}'")

        content = await f.read()

        if not content:
            raise HTTPException(400, f"File is empty: '{f.filename}'")

        if len(content) > MAX_FILE_SIZE:
            mb = MAX_FILE_SIZE // (1024 * 1024)
            raise HTTPException(400, f"'{f.filename}' exceeds the {mb} MB size limit")

        file_contents.append((f.filename, content))

    # ── Ownership check (after validation, before any disk writes) ────────────
    job = _get_job(db, crud_id, current_user.id)

    # ── Pass 2: save to disk + DB now that everything is valid ────────────────
    upload_root = Path(settings.upload_dir) / crud_id
    upload_root.mkdir(parents=True, exist_ok=True)

    saved = 0
    unreadable = 0

    for original_name, content in file_contents:
        # UUID prefix prevents filename collisions and path traversal
        safe_name = f"{uuid.uuid4().hex}_{Path(original_name).name}"
        stored_path = upload_root / safe_name
        stored_path.write_bytes(content)

        # Extract text immediately so it's ready when screening runs
        extracted = extract_text_from_pdf(content)
        if not extracted.strip():
            unreadable += 1

        # One Resume row per file (fixes old version's multi-file-per-row model)
        db.add(Resume(
            job_id=job.id,
            filename=original_name,
            stored_path=str(stored_path),
            extracted_text=extracted or None,
        ))
        saved += 1

    db.commit()

    msg = f"{saved} resume(s) uploaded successfully"
    if unreadable:
        msg += f" — warning: {unreadable} file(s) had no readable text (scanned/image PDFs)."
    return MessageResponse(message=msg)


@router.post("/screen", response_model=list[ScreeningResultResponse])
def screen_resumes(
    crud_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run NLP screening on all resumes for a job.
    Clears previous results, rescores everything, returns ranked list.

    Separated from upload (fixes old version's screen-on-upload coupling).
    Uses improved scorer: token overlap + skill match + phrase bonus.
    """
    job = _get_job(db, crud_id, current_user.id)

    resumes = db.query(Resume).filter(Resume.job_id == job.id).all()
    if not resumes:
        raise HTTPException(400, "No resumes uploaded for this job yet")

    # Wipe previous results so re-screening is always a clean slate
    db.query(ScreeningResult).filter(ScreeningResult.job_id == job.id).delete()

    results: list[ScreeningResultResponse] = []

    for resume in resumes:
        try:
            score, keywords = score_resume_against_job(
                job.job_description,
                resume.extracted_text or "",
            )
        except Exception as exc:
            raise HTTPException(
                500,
                f"Scoring failed for '{resume.filename}': {exc}",
            ) from exc

        row = ScreeningResult(
            job_id=job.id,
            resume_id=resume.id,
            score=score,
            matched_keywords=keywords,
            # screened_at uses Python-side default (lambda: datetime.now(utc))
            # so it's available immediately after flush() — no extra DB roundtrip
        )
        db.add(row)
        db.flush()
        db.refresh(row)  # pulls screened_at back from the row

        results.append(ScreeningResultResponse(
            id=row.id,
            resume_id=resume.id,
            filename=resume.filename,
            score=score,
            matched_keywords=keywords,
            screened_at=row.screened_at,
        ))

    db.commit()

    # Return sorted by score descending — highest match first
    results.sort(key=lambda r: r.score, reverse=True)
    return results


@router.delete("/{resume_id}", response_model=MessageResponse)
def delete_resume(
    crud_id: str,
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a resume and its stored PDF file. Ownership enforced via job lookup."""
    job = _get_job(db, crud_id, current_user.id)

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.job_id == job.id,
    ).first()
    if not resume:
        raise HTTPException(404, "Resume not found")

    # Remove file from disk before deleting DB row
    stored = Path(resume.stored_path)
    if stored.exists():
        stored.unlink()

    db.delete(resume)
    db.commit()
    return MessageResponse(message="Resume deleted")
