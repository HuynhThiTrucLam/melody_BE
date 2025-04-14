from pydantic import BaseModel, EmailStr


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str
    purpose: str = "signup"


class SendCodeRequest(BaseModel):
    email: EmailStr
    purpose: str = "signup"
