import time
import re as regexp
from . import reddit
from . import discord
from .logger import logger
from .configuration import config
from datetime import datetime


def reddit_timestamp_creator(unix_epoch: float) -> str:
    # Convert to local datetime object
    dt = datetime.fromtimestamp(unix_epoch)

    # Extract components
    month = dt.month
    day = dt.day
    year = dt.year
    hour = dt.hour
    minute = dt.minute

    am_pm = "am" if hour < 12 else "pm"
    hour_12 = hour % 12 or 12

    return f"{month}/{day}/{year} at {hour_12}:{minute:02d} {am_pm}"


def reddit_account_age_timestamp_generator(unix_epoch) -> str:
    return time.strftime("%B %d, %Y", time.localtime(unix_epoch))


def get_trades_number(flair: str) -> str:
    if isinstance(flair, str) and flair and flair.startswith("Trades: "):
        trades = flair.removeprefix("Trades: ").strip().lower()
    elif isinstance(flair, str):
        trades = flair.strip().lower()
    else:
        trades = "none"

    return "0" if trades == "none" else trades


def get_karma_string(author: reddit.Redditor) -> tuple[str, str, str]:
    j = reddit_account_age_timestamp_generator(author.created_utc)
    pk = author.link_karma
    ck = author.comment_karma

    return j, pk, ck


def parse_have_want(title: str, body: str | None = None, include_body: bool = False) -> tuple[str, str, str]:
    h_match = regexp.search(r'\[H\](.*?)\[W\]', title, regexp.IGNORECASE)
    w_match = regexp.search(r'\[W\](.*)', title, regexp.IGNORECASE)

    title_only_h = h_match.group(1).strip() if h_match else ""
    w = w_match.group(1).strip() if w_match else ""  # W is always from title only

    if include_body and body:
        # h = parsed have value from title + post body (when body parsing is enabled in conf)
        h = f"{title_only_h} {body}".strip()
    else:
        # use the old method (title-only)
        h = title_only_h

    return h, w, title_only_h


def print_new_post(
    author: reddit.Redditor, h: str, w: str, title_only_h: str, url: str, utc_date: float, flair: str,
    webhook: str, role: int, post_body: str, category_name: str | None = None, is_all_listings_webhook: bool = False
) -> None:
    j, pk, ck = get_karma_string(author)  # use the full author var because the function needs the entire author object
    trades = get_trades_number(flair)

    date_posted = reddit_timestamp_creator(utc_date)

    webhook_type = "all listings" if is_all_listings_webhook else f"category '{category_name}'"
    logger.debug(f"Sending webhook for {webhook_type} to Discord")

    discord.send_webhook(
        webhook_url=webhook,
        content=f"<@&{str(role)}>" if role else "",
        username="HardwareSwap Listing Scraper Alerts",
        embed=discord.create_embed(
            url=url,
            author=author.name,
            trades=trades,
            have=str(title_only_h).replace("[H]", "").strip(),
            want=str(w).replace("[W]", "").strip(),
            joined=j,
            post_karma=pk,
            comment_karma=ck,
            date_posted=date_posted,
            post_body=post_body
        ),
        raise_exception_instead_of_print=config.debug_mode
    )
