import logging
import time
from .configuration import config
from . import webhook_sender

_discord_webhook_send_count = 0

try:
    LOGGER_DISCORD_WEBHOOK_URL = config.logger_webhook
except AttributeError:
    LOGGER_DISCORD_WEBHOOK_URL = None

ANSI = "\033["
RESET = f"{ANSI}0m"
RED = f"{ANSI}31m"
GREEN = f"{ANSI}32m"
BLUE = f"{ANSI}34m"
YELLOW = f"{ANSI}33m"
WHITE = f"{ANSI}37m"
PURPLE = f"{ANSI}35m"
CYAN = f"{ANSI}36m"
LIGHT_CYAN = f"{ANSI}96m"
SUPER_LIGHT_CYAN = f"{ANSI}38;5;153m"
ORANGE = f"{ANSI}38;5;208m"


class Logger(logging.Formatter):
    def __init__(self):
        super().__init__()
        self._format = "[ %(levelname)s ]    %(message)s    [%(asctime)s (%(filename)s:%(funcName)s)]"

        self.FORMATS = {
            logging.DEBUG: self._format,
            logging.INFO: self._format,
            logging.WARNING: self._format,
            logging.ERROR: self._format,
            logging.CRITICAL: self._format,
        }

    def format(self, record: logging.LogRecord) -> str:
        record.levelname = record.levelname.center(8)

        match record.levelno:
            case logging.INFO:
                record.levelname = f"{GREEN}{record.levelname}{RESET}"
            case logging.WARNING:
                record.levelname = f"{YELLOW}{record.levelname}{RESET}"
            case logging.ERROR:
                record.levelname = f"{RED}{record.levelname}{RESET}"
            case logging.CRITICAL:
                record.levelname = f"{PURPLE}{record.levelname}{RESET}"

        log_fmt = self.FORMATS.get(record.levelno)

        formatter = logging.Formatter(log_fmt, datefmt="%y/%m/%d %H:%M:%S")
        return formatter.format(record)


fmt = Logger()

logger = logging.getLogger("vscode-status")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(fmt)
logger.addHandler(handler)


# thanks for this part chatgpt
class DiscordWebhookHandler(logging.Handler):
    def __init__(self, webhook_url: str, level: int = logging.NOTSET):
        super().__init__(level)
        self.webhook_url: str = webhook_url

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level_name = logging.getLevelName(record.levelno)
            asctime = time.strftime("%y/%m/%d %H:%M:%S", time.localtime(record.created))
            message = record.getMessage()
            content = f"```\n[ {level_name} ]    {message}    [{asctime} ({record.filename}:{record.funcName})]\n```"

            global _discord_webhook_send_count
            _discord_webhook_send_count += 1
            if _discord_webhook_send_count == 1:
                content = "_ _ \n_ _ \n_ _ \n" + content  # add newlines at the beginning of first log to separate logs

            webhook_sender.send(self.webhook_url, content)

        except Exception:
            # use print so i don't cause an infinite loop of errors
            print("[ ERROR ] Failed to send log to Discord webhook!")
            pass


def _has_discord_handler(logr: logging.Logger) -> bool:
    for h in logr.handlers:
        if isinstance(h, DiscordWebhookHandler):
            return True
    return False


if config.logger_webhook and not _has_discord_handler(logger):
    try:
        discord_handler = DiscordWebhookHandler(config.logger_webhook)
        discord_handler.setLevel(logging.DEBUG)
        logger.addHandler(discord_handler)
    except Exception:
        logger.error("Failed to add Discord webhook handler to logger!")
        pass
