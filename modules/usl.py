import requests
from .logger import logger


def is_on_usl(username: str) -> bool:
    url = "https://api.reddit.com/r/UniversalScammerList/wiki/database/{username}.json"

    username = username.lower()

    response = requests.get(url.format(username=username))

    if response.ok:
        return True  # User is on the USL
    elif response.status_code == 404:
        return False  # User is not on the USL
    else:
        logger.warning(f"Unexpected response from USL API for user u/{username}: {response.status_code}.")  # noqa: E501
        return False  # Unrecognized response, treat as on USL
