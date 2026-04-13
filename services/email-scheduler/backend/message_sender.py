from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend.async_send_message import async_send_message
import asyncio
from backend.logger import logger


async def main():
    logger.info("Function is starting...")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        async_send_message,
        trigger=IntervalTrigger(minutes=1),
        id="email_sending",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Function started successfully")

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Function is shutting down...")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
