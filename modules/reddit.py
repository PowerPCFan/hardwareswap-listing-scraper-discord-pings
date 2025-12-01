import kroma
import praw
from praw.models import Subreddit, Submission, Redditor  # noqa: F401
from .configuration import config


def initialize() -> Subreddit:
    print(f"{kroma.style(text='Connecting to Reddit...', foreground=kroma.ANSIColors.BLUE)}")

    reddit = praw.Reddit(
        client_id=config.reddit_id,
        client_secret=config.reddit_secret,
        user_agent=f"script:hardwareswap-listing-scraper (by u/{config.reddit_username})"
    )

    subreddit = reddit.subreddit("hardwareswap")

    print(f"{kroma.style(text='Connected successfully.', foreground=kroma.ANSIColors.GREEN)}")

    return subreddit
