from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserUpdateResponse(BaseModel):
    user: UserResponse
    access_token: str | None = None
    token_type: str = "bearer"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class JobCreate(BaseModel):
    job_title: str = Field(min_length=1, max_length=200)
    job_description: str = Field(min_length=10)


class JobUpdate(BaseModel):
    job_title: str = Field(min_length=1, max_length=200)
    job_description: str = Field(min_length=10)


class JobResponse(BaseModel):
    id: int
    crud_id: str
    job_title: str
    job_description: str
    created_at: datetime | None
    model_config = {"from_attributes": True}


class ResumeResponse(BaseModel):
    id: int
    resume_id: str
    job_id: int
    filename: str
    uploaded_at: datetime
    model_config = {"from_attributes": True}


class ScreeningResultResponse(BaseModel):
    id: int
    resume_id: int
    filename: str
    score: float
    matched_keywords: str | None
    screened_at: datetime


class MessageResponse(BaseModel):
    message: str
