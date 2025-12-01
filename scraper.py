#!/usr/bin/env python3

import sys
import kroma
import modules.welcome as welcome
import modules.reddit as reddit
import modules.modes as modes


def main() -> None:
    subreddit = reddit.initialize()
    welcome.print_welcome_text()

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

        sys.exit(1)
