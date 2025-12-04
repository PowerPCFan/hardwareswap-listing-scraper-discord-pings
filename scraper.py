#!/usr/bin/env python3

import sys
import traceback
from modules.logger import logger
import modules.welcome as welcome
import modules.reddit as reddit
import modules.modes as modes
import modules.discord as discord
from modules.configuration import config


def main() -> None:
    # init subreddit
    subreddit = reddit.initialize()

    # if send_test_webhooks is enabled, test every webhook
    # will raise exception if one webhook fails so then it will be caught in the main handler
    if config.send_test_webhooks:
        logger.info("Testing webhooks...")

        for webhook_url, category_name in (
            [(config.all_listings_webhook, "All Listings")] +
            [(ping.webhook, ping.category_name) for ping in config.pings]
        ):
            discord.send_webhook(
                webhook_url=webhook_url,
                content=f"Script started. This is a test webhook for the '{category_name}' category.",
                embed=None,
                username=category_name,
                raise_exception_instead_of_print=config.debug_mode
            )

        logger.info("All webhooks tested successfully.")

    # print welcome text (splash text and config summary)
    welcome.print_welcome_text()

    # Start matching mode
    modes.match(subreddit)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error("-" * 36)
        logger.error("ERROR: An unexpected error occurred:")
        logger.error("-" * 36)
        logger.error(str(e))

        if config.debug_mode:
            logger.error("-" * 36)
            logger.error("DEBUG TRACEBACK:")
            logger.error("-" * 36)
            traceback.print_exception(type(e), e, e.__traceback__)

        sys.exit(1)
