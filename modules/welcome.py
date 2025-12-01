import kroma
import modules.splash as splash
from configuration import config


def print_welcome_text():
    welcome = "Welcome to the HardwareSwap Listing Scraper (Discord Pings Edition), "
    username = f"u/{config.reddit_username}!"
    dashes = "-" * (len(welcome) + len(username))

    print(f"\n{dashes}")
    splash.print_splash_text_background()
    print(f"\n{dashes}")
    print(f"{welcome}{kroma.style(text=username, foreground=kroma.ANSIColors.BLUE)}")
    print(f"Press {kroma.style(text='Ctrl+C', foreground=kroma.ANSIColors.YELLOW)} to exit.")
    print(f"{dashes}")
