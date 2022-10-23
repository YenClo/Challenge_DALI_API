# Author: Yunquan (Clooney) Gu
import asyncio

from loguru import logger
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.updater import Updater
from telegram.update import Update

from app.Twitter import Twitter
from app.config import init_logging, GlobalConfig
from app.schedule import Schedule

telegramUpdater = Updater(GlobalConfig.TELEGRAM_TOKEN)
twitterClient = Twitter(count=500)


def start(update: Update, context):
    update.message.reply_text("Enter the \\info to get the hottest crypto information")


def info(update: Update, context):
    update.message.reply_text(
        f"{twitterClient.text}"
    )


telegramUpdater.dispatcher.add_handler(CommandHandler('start', start))
telegramUpdater.dispatcher.add_handler(CommandHandler('info', info))
telegramUpdater.start_polling()


@logger.catch
async def startup():
    init_logging()

    # Set the coroutines Parsing job runs every 5 min.
    Schedule.add_job(func=twitterClient.acquire_hot_coins_list,
                     trigger='interval',
                     seconds=60 * 2,
                     )
    Schedule.start()
    await twitterClient.acquire_hot_coins_list()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(startup())
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.exception(e)
    finally:
        Schedule.shutdown()
