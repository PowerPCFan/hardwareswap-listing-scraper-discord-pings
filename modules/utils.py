import kroma
import time
import re as regexp
import discord
import reddit
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


def parse_have_want(title: str) -> tuple[str, str]:
    h_match = regexp.search(r'\[H\](.*?)\[W\]', title, regexp.IGNORECASE)
    w_match = regexp.search(r'\[W\](.*)', title, regexp.IGNORECASE)

    h = h_match.group(1).strip() if h_match else ""
    w = w_match.group(1).strip() if w_match else ""
    return h, w


def print_new_post(
    subreddit: reddit.Subreddit, author: reddit.Redditor, h: str, w: str,
    url: str, utc_date: float, flair: str, title: str, ping_config
) -> None:

    j, pk, ck = get_karma_string(author)  # use the full author var because the function needs the entire author object
    trades = get_trades_number(flair)

    date_posted = reddit_timestamp_creator(utc_date)

    print("\n")  # newline for spacing

    print(
        f"New post by {kroma.style(f'u/{author.name}', foreground=kroma.ANSIColors.BLUE)} "
        f"({kroma.style(trades, foreground=kroma.ANSIColors.YELLOW)} {'trades' if trades != 1 else 'trade'} | "
        f"joined {kroma.style(j, foreground=kroma.ANSIColors.CYAN)} | "
        f"post karma {kroma.style(pk, foreground=kroma.HTMLColors.ORANGE)} | "
        f"comment karma {kroma.style(ck, foreground=kroma.HTMLColors.PURPLE)}):"
    )

    print(f"[H]: {kroma.style(h, foreground=kroma.ANSIColors.GREEN)}")
    print(f"[W]: {kroma.style(w, foreground=kroma.ANSIColors.RED)}")
    print(f"URL: {kroma.style(url, foreground="#99ccff")}")
    print(f"Posted {kroma.style(date_posted, foreground="#ffffff")}")
    print(kroma.style(f"Matches category '{ping_config.category_name}'", italic=True, bold=True))

    discord.send_webhook(
        webhook_url=ping_config.webhook,
        content=f"<@&{ping_config.role}>" if ping_config.role else "",
        username="HardwareSwap Listing Scraper Alerts",
        embed=discord.create_embed(
            url=url,
            author=author.name,
            trades=trades,
            have=str(h).replace("[H]", "").strip(),
            want=str(w).replace("[W]", "").strip(),
            joined=j,
            post_karma=pk,
            comment_karma=ck,
            date_posted=date_posted
        )
    )
