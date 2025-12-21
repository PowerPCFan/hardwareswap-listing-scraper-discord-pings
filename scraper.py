#!/usr/bin/env python3

import sys
import traceback
from modules.logger import logger
import modules.reddit as reddit
import modules.modes as modes
import modules.discord as discord
from modules.configuration import config


def main() -> None:
    logger.info("Initializing HardwareSwap Listing Scraper...")

    # init subreddit
    logger.debug("Connecting to Reddit API...")
    initialize_response = reddit.initialize()
    logger.info("Successfully connected to Reddit")

    # if send_test_webhooks is enabled, test every webhook
    # will raise exception if one webhook fails so then it will be caught in the main handler
    if config.send_test_webhooks:
        logger.info("Testing webhooks...")

        for webhook_url, category_name in (
            [(config.all_listings_webhook, "All Listings")] +
            [(ping.webhook, ping.category_name) for ping in config.pings]
        ):
            if not webhook_url:
                continue

            logger.debug(f"Testing webhook for category: {category_name}")
            discord.send_webhook(
                webhook_url=webhook_url,
                content=f"Script started. This is a test webhook for the '{category_name}' category.",
                embed=None,
                username=category_name,
                raise_exception_instead_of_print=config.debug_mode
            )

        logger.info("All webhooks tested successfully.")

    # print welcome text
    logger.newline()
    logger.info("HardwareSwap Listing Scraper (Discord Pings Edition) starting...")
    logger.info(f"Reddit Username: u/{config.reddit_username}")
    logger.info(f"Debug Mode: {config.debug_mode}")
    logger.info(f"Full Tracebacks: {config.full_tracebacks}")
    logger.info(f"Parse Body: {config.parse_body}")
    logger.info(f"Parse Imgur Links: {config.parse_imgur_links}")
    logger.info(f"Send Test Webhooks: {config.send_test_webhooks}")
    logger.info(f"Combine Images: {config.combine_images}")
    logger.info(f"Ping for Warnings: {config.ping_for_warnings}")
    logger.info(f"Check If Post Was Deleted: {config.check_if_post_was_deleted}")
    logger.info(f"File Logging: {config.file_logging}")
    logger.info(f"Check USL: {config.check_usl}")
    logger.info(f"Configured {len(config.pings)} ping categories")
    logger.info(f"Configured global blocklist with {len(config.global_blocklist)} patterns")
    logger.info("Press Ctrl+C to exit")
    logger.newline()

    # Start matching mode
    logger.info("Starting listing monitoring...")
    modes.match(initialize_response)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Exiting app. There may be missing logs in Discord if the logging queue was not emptied.")
        sys.exit(0)
    except Exception as e:
        logger.critical("An unexpected error occurred!")
        logger.error(f"Error details: {str(e)}")

        if config.full_tracebacks:
            logger.error("Full traceback:")
            # traceback.print_exception(type(e), e, e.__traceback__)
            for line in traceback.format_exception(type(e), e, e.__traceback__):
                logger.error(line.strip())

        sys.exit(1)
