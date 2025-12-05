from pydantic import BaseModel, EmailStr


class LeadIn(BaseModel):
    name: str
    email: EmailStr
    source: str | None = None
