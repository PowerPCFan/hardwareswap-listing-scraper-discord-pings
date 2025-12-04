import logging
import time
import queue
import threading
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


class CustomLogger:
    def __init__(self, base_logger):
        self.base_logger: logging.Logger = base_logger

    def debug(self, msg, *args, **kwargs):
        return self.base_logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        return self.base_logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        return self.base_logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        return self.base_logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        return self.base_logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        return self.base_logger.exception(msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        return self.base_logger.log(level, msg, *args, **kwargs)

    @property
    def handlers(self):
        return self.base_logger.handlers

    def addHandler(self, handler):
        return self.base_logger.addHandler(handler)

    def removeHandler(self, handler):
        return self.base_logger.removeHandler(handler)

    def setLevel(self, level):
        return self.base_logger.setLevel(level)

    def getEffectiveLevel(self):
        return self.base_logger.getEffectiveLevel()

    def newline(self):
        print("\n", end="")

        for handler in self.base_logger.handlers:
            if isinstance(handler, DiscordWebhookHandler):
                try:
                    handler.message_queue.put("_ _")
                    return
                except Exception:
                    print("[ ERROR ] Failed to queue newline for Discord webhook!")

        try:
            webhook_sender.send(config.logger_webhook, "_ _")
        except Exception:
            print("[ ERROR ] Failed to send newline to Discord webhook!")


_base_logger = logging.getLogger("vscode-status")
_base_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setFormatter(fmt)
_base_logger.addHandler(handler)

logger = CustomLogger(_base_logger)


class DiscordWebhookHandler(logging.Handler):
    def __init__(self, webhook_url: str, ping_webhook: str | None = None, level: int = logging.NOTSET):
        super().__init__(level)
        self.webhook_url: str = webhook_url
        self.ping_webhook: str | None = ping_webhook
        self.message_queue = queue.Queue()
        self.worker_thread = None
        self.shutdown_flag = threading.Event()
        self._start_worker()

    def _start_worker(self):
        """Start the worker thread that processes the message queue"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()

    def _worker(self):
        """Worker thread that processes queued messages with delays"""
        while not self.shutdown_flag.is_set():
            try:
                content = self.message_queue.get(timeout=1.0)
                if content is None:
                    break

                webhook_sender.send(self.webhook_url, content)

                time.sleep(0.5)

                self.message_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"[ ERROR ] Discord webhook worker error: {e}")

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level_name = logging.getLevelName(record.levelno)
            asctime = time.strftime("%y/%m/%d %H:%M:%S", time.localtime(record.created))
            message = record.getMessage()

            ping_content = ""
            if self.ping_webhook and record.levelno >= logging.WARNING:
                ping_content = f"{self.ping_webhook} "

            content = (
                f"{ping_content}```\n"
                f"[ {level_name} ]    {message}    [{asctime} ({record.filename}:{record.funcName})]\n"
                f"```"
            )

            global _discord_webhook_send_count
            _discord_webhook_send_count += 1
            if _discord_webhook_send_count == 1:
                content = "_ _ \n_ _ \n_ _ \n" + content  # add newlines at the beginning of first log to separate logs

            self.message_queue.put(content)

        except Exception:
            # use print so i don't cause an infinite loop of errors
            print("[ ERROR ] Failed to queue log for Discord webhook!")

    def close(self):
        self.shutdown_flag.set()
        self.message_queue.put(None)  # Signal worker to stop
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        super().close()


def _has_discord_handler(logr) -> bool:
    handlers = getattr(logr, 'handlers', [])
    for h in handlers:
        if isinstance(h, DiscordWebhookHandler):
            return True
    return False


if config.logger_webhook and not _has_discord_handler(logger):
    try:
        discord_handler = DiscordWebhookHandler(config.logger_webhook, f"<@{str(config.logger_webhook_ping)}>")
        discord_handler.setLevel(logging.DEBUG)
        logger.addHandler(discord_handler)
    except Exception:
        logger.error("Failed to add Discord webhook handler to logger!")
        pass
