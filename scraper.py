#!/usr/bin/env python3

import sys
import traceback
import kroma
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
        print(kroma.style(text="\nTesting webhooks...", foreground=kroma.ANSIColors.BLUE))

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

        print(kroma.style(text="All webhooks tested successfully.", foreground=kroma.ANSIColors.GREEN))

    # print welcome text (splash text and config summary)
    welcome.print_welcome_text()

    # Start matching mode
    modes.match(subreddit)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(kroma.style(text="\nExiting...", foreground=kroma.ANSIColors.YELLOW))
        sys.exit(0)
    except Exception as e:
        print(
            f"{'-' * 36}\n"
            f"{kroma.style(text='ERROR: An unexpected error occurred:', foreground=kroma.ANSIColors.RED)}\n"
            f"{'-' * 36}\n"
            f"{str(e)}"
        )

        if config.debug_mode:
            print("-" * 36)
            print(kroma.style(text="DEBUG TRACEBACK:", foreground=kroma.ANSIColors.RED))
            print("-" * 36)
            traceback.print_exception(type(e), e, e.__traceback__)

        sys.exit(1)
