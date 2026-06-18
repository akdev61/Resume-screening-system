from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from app.models import Job, User
from app.schemas import JobCreate, JobResponse, JobUpdate, MessageResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobResponse])
def list_jobs(search: str | None = Query(default=None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Job).filter(Job.owner_id == current_user.id)
    if search:
        t = f"%{search.strip()}%"
        q = q.filter(or_(Job.job_title.ilike(t), Job.job_description.ilike(t)))
    return q.order_by(Job.created_at.desc()).all()


@router.post("", response_model=JobResponse, status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = Job(job_title=payload.job_title, job_description=payload.job_description, owner_id=current_user.id)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/{crud_id}", response_model=JobResponse)
def get_job(crud_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.crud_id == crud_id, Job.owner_id == current_user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.put("/{crud_id}", response_model=JobResponse)
def update_job(crud_id: str, payload: JobUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.crud_id == crud_id, Job.owner_id == current_user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    job.job_title = payload.job_title
    job.job_description = payload.job_description
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{crud_id}", response_model=MessageResponse)
def delete_job(crud_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.crud_id == crud_id, Job.owner_id == current_user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    db.delete(job)
    db.commit()
    return MessageResponse(message="Job deleted")
