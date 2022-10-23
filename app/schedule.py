# Author: Yunquan (Clooney) Gu

from apscheduler.events import EVENT_JOB_ERROR
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

try:
    logger.info("Init Schedule")
    Schedule = AsyncIOScheduler(
        executors={
            'default': AsyncIOExecutor()
        },
        timezone='EST',
    )
    Schedule.add_listener(lambda exp: logger.exception(exp.exception), EVENT_JOB_ERROR)
except BaseException as e:
    logger.exception(e)
