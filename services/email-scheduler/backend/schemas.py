from pydantic import BaseModel, EmailStr
from datetime import datetime


class EmailSchema(BaseModel):
    receiver_email: EmailStr
    subject: str
    message_body: str
    sending_time: datetime
