import kroma
from . import splash
from .configuration import config


def _get_boolean_color(value: bool) -> kroma.ANSIColors:
    return kroma.ANSIColors.GREEN if value else kroma.ANSIColors.RED


def print_welcome_text():
    welcome = "Welcome to the HardwareSwap Listing Scraper (Discord Pings Edition), "
    username = f"u/{config.reddit_username}!"
    dashes = "-" * (len(welcome) + len(username))

    print(f"\n{dashes}")
    splash.print_splash_text_background()
    print(f"\n{dashes}")
    print(f"{welcome}{kroma.style(text=username, foreground=kroma.ANSIColors.BLUE)}")
    print(f"Debug Mode: {kroma.style(text=str(config.debug_mode), foreground=_get_boolean_color(config.debug_mode))}")
    print(f"Parse Body: {kroma.style(text=str(config.parse_body), foreground=_get_boolean_color(config.parse_body))}")
    print(f"Parse Imgur Links: {kroma.style(text=str(config.parse_imgur_links), foreground=_get_boolean_color(config.parse_imgur_links))}")  # noqa: E501
    print(f"Send Test Webhooks: {kroma.style(text=str(config.send_test_webhooks), foreground=_get_boolean_color(config.send_test_webhooks))}")  # noqa: E501
    print(f"Press {kroma.style(text='Ctrl+C', foreground=kroma.ANSIColors.YELLOW)} to exit.")
    print(f"{dashes}")
