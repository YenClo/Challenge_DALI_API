# Author: Yunquan (Clooney) Gu
import logging
import re
import sys
from pprint import pformat

from loguru import logger
from loguru._defaults import LOGURU_FORMAT


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentaion.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def format_record(record: dict) -> str:
    format_string = LOGURU_FORMAT
    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(
            record["extra"]["payload"], indent=4, compact=True, width=88
        )
        format_string += "\n<level>{extra[payload]}</level>"

    format_string += "{exception}\n"
    return format_string


def init_logging():
    loggers = (
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if name.startswith("uvicorn.")
    )
    intercept_handler = InterceptHandler()

    for uvicorn_logger in loggers:
        uvicorn_logger.handlers = [intercept_handler]

    logger.configure(
        handlers=[{"sink": sys.stdout, "level": logging.INFO, "format": format_record}]
    )
    logger.add('./log/runtime-{time}.log', rotation='1 week', retention='30 days')


class GlobalConfig:
    # TELEGRAM API
    TELEGRAM_TOKEN = "5660384590:AAEJvq5qnv-QxBkQcn3Usmp2Hy0-UxhSbMI"
    # TWITTER API
    API_KEY = "hb1H3xhDdGSTOwRrsrWdFv66i"
    API_KEY_SECRET = "YOVX9yZunrXbSEYfMbvmmKtbSHc2gYbel8UqGrdSdsG01ktFWS"
    BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAELrVgEAAAAAyplOHaQV5E0%2FAmJoTE%2BbEvO1xdA%3Dk4AV10N3vsI1fNPDnGB7G2eaOlWTchuLA8Po36wWRLSQtLn1gH"

    # Coin query in twitter seach
    COIN_QUERY = ['coin', 'token', 'crypto', 'metaverse', 'defi', 'nft', 'dao', 'bitcoin', 'eth', 'binance']
    COIN_FILTER = {'NFT', 'nft', 'AI', 'Crypto', 'crypto', 'nftart', 'web3', 'Web3', 'NFTartist', 'NFTs', 'NFT',
                   'NFTCommunity', 'nftartgallery', 'NFTshills', 'cryptoart', 'token', 'gateio'}

    # Regex patter to retrieve information
    COIN_PATTERN = re.compile(r"[$][a-zA-Z]+")
