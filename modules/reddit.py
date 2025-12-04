from .logger import logger
import praw
from praw.models import Subreddit, Submission, Redditor  # noqa: F401
from .configuration import config


def initialize() -> Subreddit:
    logger.info("Connecting to Reddit...")

    reddit = praw.Reddit(
        client_id=config.reddit_id,
        client_secret=config.reddit_secret,
        user_agent=f"script:hardwareswap-listing-scraper (by u/{config.reddit_username})"
    )

    subreddit = reddit.subreddit("hardwareswap")

    logger.info("Connected successfully.")

    return subreddit
