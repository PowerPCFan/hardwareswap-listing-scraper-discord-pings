import requests
import time
from .logger import logger


def is_on_usl(username: str) -> bool:
    username = username.lower()
    url = f"https://corsproxy.io/?url=https://api.reddit.com/r/UniversalScammerList/wiki/database/{username}.json"

    try:
        response = requests.get(url)
    except requests.RequestException as e:
        logger.warning(f"Error checking USL for {username}: {e}. Treating as on USL.")
        return True  # Assume user is on USL

    retries = 0
    while response.status_code == 429 and retries < 3:
        fallback = 5

        retry_after = int(response.headers.get("Retry-After", fallback))

        if retry_after > 30:
            retry_after = fallback

        time.sleep(retry_after)

        try:
            response = requests.get(url)
        except requests.RequestException as e:
            logger.warning(f"Error checking USL for {username}: {e}. Treating as on USL.")
            return True  # Assume user is on USL

        retries += 1

    if response.status_code == 200:
        return True  # User is on the USL
    elif response.status_code in (400, 403, 404):
        return False  # User is not on the USL
    else:
        logger.warning(f"Unexpected status code from USL API for user u/{username}: {response.status_code}. Treating as on USL.")  # noqa: E501
        return True  # Unrecognized response, treat as on USL
