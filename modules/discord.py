import requests
import time
import markdown
import re as regexp
from bs4 import BeautifulSoup
from .logger import logger
from .price import Price


# todo: move to config file
# i should probably do this to my ebay scraper as well
class Emojis:
    CALENDAR = "<:calendar:1453717238702932028>"
    PRICE = "<:price:1453719493686853632>"
    SELLER = "<:seller:1453721027103428609>"
    WARNING = "⚠️"
    EXCLAMATION = "<:exclamation_mark:1477510984225525800>"
    INFO = "<:info:1477510894069092493>"
    CHECK = "<:check:1477511079625101415>"


# def clean_body(input_string: str, max_len: int = 1024) -> str:
#     try:
#         trunc_text = "\n... (view full post on Reddit)"
#         max_len = max_len - len(trunc_text)
#         if max_len < 0:
#             return ""

#         # converts markdown -> html and then html -> text
#         txt = BeautifulSoup(markdown.markdown(input_string), "html.parser").get_text()
#         txt = "\n".join(f"> {line}" if line.strip() else ">" for line in txt.splitlines())

#         if len(txt) < max_len:
#             # all good
#             txt = txt
#         else:
#             # split into lines and trim until we're under the limit
#             txt_lines = txt.splitlines()
#             while len("\n".join(txt_lines)) > max_len and txt_lines:
#                 txt_lines.pop()
#             txt = "\n".join(txt_lines)

#         idx = 0
#         while True:
#             if idx >= 10:
#                 break

#             if regexp.match(
#                 r"^>*\s*$",
#                 txt.splitlines()[-1],
#                 regexp.MULTILINE | regexp.IGNORECASE | regexp.UNICODE
#             ):
#                 txt = "\n".join(line for line in txt.splitlines()[:-1])

#             idx += 1

#         return txt + trunc_text
#     except Exception:
#         logger.exception("Error parsing body")
#         return input_string


def clean_body(input_string: str, max_len: int = 1024) -> str:
    try:
        trunc_text = "\n... (view full post on Reddit)"
        max_len -= len(trunc_text)

        if max_len < 0:
            return ""

        txt = BeautifulSoup(
            markdown.markdown(input_string),
            "html.parser"
        ).get_text()

        txt = "\n".join(
            f"> {line}" if line.strip() else ">"
            for line in txt.splitlines()
        )

        lines = txt.splitlines()
        if len(txt) > max_len:
            while lines and len("\n".join(lines)) > max_len:
                lines.pop()
            txt = "\n".join(lines)

        for _ in range(10):
            lines = txt.splitlines()
            if not lines:
                break

            last = lines[-1]

            if regexp.match(
                r"^>*\s*$",
                last,
                regexp.MULTILINE | regexp.IGNORECASE | regexp.UNICODE
            ):
                lines.pop()
                txt = "\n".join(lines)
            else:
                break

        return txt + trunc_text

    except Exception:
        logger.exception("Error parsing body")
        return input_string


def create_embed(
    url: str,
    author: str,
    trades: str,
    title: str,
    have: str,
    want: str,
    joined: str,
    post_karma: str,
    comment_karma: str,
    date_posted: str,
    post_body: str,
    prices: Price | None,
    image_url: str | None
) -> dict:
    body = clean_body(post_body, max_len=512)

    title = f"u/{author} posted a new listing: {title}"
    if len(title) > 256:
        title = title[:253] + "..."

    embed = {
        "title": title,
        "url": url,
        "color": 0x3498db,

        "fields": [
            {
                "name": f"{Emojis.SELLER} User Info:",
                "value": (
                    f"- Posted by **[u/{author}](https://www.reddit.com/user/{author})**\n"
                    f"- **{trades}** trades\n"
                    f"- Joined **{joined}**\n"
                    f"- **{post_karma}** post karma\n"
                    f"- **{comment_karma}** comment karma"
                ),
                "inline": False
            },
            {
                "name": f"{Emojis.CHECK} Has:",
                "value": have,
                "inline": False
            },
            {
                "name": f"{Emojis.EXCLAMATION} Wants:",
                "value": want,
                "inline": False
            },
            {
                "name": f"{Emojis.CALENDAR} Date Posted:",
                "value": date_posted,
                "inline": False
            },
            {
                "name": f"{Emojis.INFO} Post Content:",
                "value": body,
                "inline": False
            }
        ],
        "thumbnail": {
            "url": "https://raw.githubusercontent.com/PowerPCFan/hardwareswap-listing-scraper/refs/heads/main/assets/3.png"  # noqa: E501
        },
    }

    if image_url:
        embed["image"] = {"url": image_url}

    # this is so messy lmao
    if prices:
        fields = embed.get("fields", None)
        if fields:
            fields = list(fields)
            if prices.price_string and len(prices.prices) > 0:
                fields.insert(-2, {
                    "name": Emojis.PRICE + (" Prices:" if len(prices.prices) > 1 else " Price:"),
                    "value": prices.price_string,
                    "inline": False
                })
                embed["fields"] = fields

    return embed


def send_webhook(
    webhook_url: str,
    content: str | None,
    embed: dict | None,
    username: str | None,
    raise_exception_instead_of_print: bool = False
) -> None:
    # Prepare the JSON payload
    json_data = {
        "content": content if content is not None else "",
        "embeds": [embed] if embed is not None else [],
        "username": username if username is not None else ""
    }

    logger.debug(f"Sending Discord webhook to {webhook_url[:30]} (truncated)...")

    # Send the webhook
    try:
        response = requests.post(webhook_url, json=json_data, timeout=5)

        if response.status_code == 429:
            logger.warning("Discord rate limit hit, retrying after delay...")
            default_retry = 1.5

            try:
                retry_after = dict(response.json()).get("retry_after", default_retry)
                logger.debug(f"Rate limit retry delay: {retry_after}s")
                time.sleep(retry_after)
                response = requests.post(webhook_url, json=json_data, timeout=5)
            except ValueError:
                logger.debug(f"Using default retry delay: {default_retry}s")
                time.sleep(default_retry)
                response = requests.post(webhook_url, json=json_data, timeout=5)

        if response.status_code not in [200, 204]:
            logger.error(f"Webhook failed with status {response.status_code}: {response.text}")
        else:
            logger.debug("Discord webhook sent successfully")
    except requests.exceptions.RequestException as e:
        error_msg = f"Error sending webhook: {e}"
        logger.error(error_msg)
        if raise_exception_instead_of_print:
            raise Exception(error_msg)
