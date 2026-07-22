from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True
