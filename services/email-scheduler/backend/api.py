from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Annotated
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from fastapi import Depends, FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from database.db import get_db
from backend.schemas import EmailSchema
from fastapi.logger import logger
import logging

gunicorn_logger = logging.getLogger("gunicorn.error")
logger.handlers = gunicorn_logger.handlers

if __name__ != "main":
    logger.setLevel(gunicorn_logger.level)
else:
    logger.setLevel(logging.DEBUG)


app = FastAPI(redirect_slashes=True)

templates = Jinja2Templates(directory="frontend")

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", response_class=RedirectResponse)
def redirect_to_main_page():
    return RedirectResponse(url="/email-scheduler", status_code=303)


@app.get("/email-scheduler", response_class=HTMLResponse)
def get_form_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/message-scheduled", response_class=HTMLResponse)
def get_information_page(request: Request):
    return templates.TemplateResponse(request=request, name="info.html")


@app.post("/api/v1", response_class=RedirectResponse)
async def handle_email_request(
    db: Annotated[AsyncConnection, Depends(get_db)],
    receiver_email: str = Form(...),
    subject: str = Form(...),
    message_body: str = Form(...),
    sending_time: str = Form(...),
    tz_info: str = Form(...),
):

    logger.info(
        f"""Got data: (receiver_email: {receiver_email}, 
            subject: {subject}, 
            message_body: {message_body}, 
            sending_time: {sending_time}, 
            tz_info: {tz_info})"""
    )

    naive_dt = datetime.fromisoformat(sending_time)
    utc_dt = naive_dt.replace(tzinfo=ZoneInfo(tz_info)).astimezone(timezone.utc)

    logger.info(f"New utc time: {utc_dt}")

    data = EmailSchema(
        receiver_email=receiver_email,
        subject=subject,
        message_body=message_body,
        sending_time=utc_dt,
    )

    query = text("""
    INSERT INTO emails (is_sent, receiver_email, subject, message_body, sending_time)
    VALUES (:is_sent, :receiver_email, :subject, :message_body, :sending_time)
    """)

    await db.execute(
        query,
        {
            "is_sent": False,
            "receiver_email": data.receiver_email,
            "subject": data.subject,
            "message_body": data.message_body,
            "sending_time": data.sending_time,
        },
    )
    await db.commit()
    return RedirectResponse(url="/message-scheduled", status_code=303)
