from .logger import logger
import praw
from praw.models import Subreddit, Submission, Redditor  # noqa: F401
from .configuration import config


def initialize() -> Subreddit:
    logger.info("Initializing Reddit API connection...")
    logger.debug(f"Using Reddit username: u/{config.reddit_username}")

    reddit = praw.Reddit(
        client_id=config.reddit_id,
        client_secret=config.reddit_secret,
        user_agent=f"script:hardwareswap-listing-scraper-discord-pings-edition (by u/{config.reddit_username})"
    )

    logger.debug("Reddit instance created successfully")
    subreddit = reddit.subreddit("hardwareswap")
    logger.info("Successfully connected to r/hardwareswap")

    return subreddit
