from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: int
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str