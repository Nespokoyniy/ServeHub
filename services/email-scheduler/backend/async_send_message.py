import aiosmtplib
from database.db import engine
import dotenv
import os
from email.message import EmailMessage
from datetime import datetime, timezone
from sqlalchemy import text
from backend.logger import logger


dotenv.load_dotenv()


async def async_send_message():
    logger.info("Function started")
    async with engine.connect() as db:
        token = os.getenv("SMTP_PASSWORD")
        sender_email = os.getenv("SMTP_USER_NAME")

        query = text("""SELECT id, receiver_email, subject, message_body
                     FROM emails WHERE sending_time <= :now AND is_sent = False""")
        # query = text("""SELECT id, receiver_email, subject, message_body, sending_time
        #               FROM emails WHERE is_sent = False""")

        current_time = datetime.now(timezone.utc)

        logger.info(f"Got current time: {current_time}")
        data = await db.execute(query, {"now": current_time})
        logger.info(f"Got data: {data}")
        emails_to_send = data.all()
        logger.info(f"Got emails_to_send: {emails_to_send}")

        if not emails_to_send:
            logger.info(f"There is no emails in the database")
            return

        # for row in emails_to_send:
        #     msg = EmailMessage()
        #     msg.set_content(row.message_body)
        #     msg["Subject"] = row.subject
        #     msg["From"] = sender_email
        #     msg["To"] = row.receiver_email

        #     logger.info(f"DB Time: {row.sending_time} | Type: {type(row.sending_time)}")
        #     logger.info(f"Now Time: {current_time} | Type: {type(current_time)}")

        try:
            async with aiosmtplib.SMTP(hostname="smtp.gmail.com", port=587) as server:
                logger.info(f"SMTP connected")
                await server.login(sender_email, token)
                logger.info(f"SMTP logged in")

                for row in emails_to_send:
                    try:
                        msg = EmailMessage()
                        msg.set_content(row.message_body)
                        msg["Subject"] = row.subject
                        msg["From"] = sender_email
                        msg["To"] = row.receiver_email

                        await server.send_message(msg)
                        logger.info(f"An email was sent to: {row.receiver_email}")

                        update_query = text(
                            "UPDATE emails SET is_sent = True WHERE id = :id"
                        )
                        await db.execute(update_query, {"id": row.id})
                        logger.info(f"Updated is_sent emails value")
                        await db.commit()
                    except Exception as e:
                        logger.exception(
                            f"An error occured while sending an email (id: {row.id}): {e}"
                        )
                        await db.rollback()
        except Exception as e:
            logger.exception(f"An error occured while connecting to SMTP: {e}")
