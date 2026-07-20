from pydantic import BaseModel, EmailStr
from datetime import datetime

# What the client sends when registering
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

# What the client sends when logging in
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# What we send back to the client (never includes password)
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True  # allows Pydantic to read data from SQLAlchemy model objects

# What we send back after successful login
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"