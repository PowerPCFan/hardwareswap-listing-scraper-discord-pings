import requests
import re as regexp
import random
import time
from .configuration import config


def grab_direct_links(album_url: str) -> list[str] | None:
    headers = {
        "content-type": "application/json",
        "origin": "https://imgur.plen.io",
        "referer": "https://imgur.plen.io/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",  # noqa: E501
    }

    resp = requests.post(
        url="https://imgur.plen.io/api/trpc/imgur.getLinks?batch=1",
        headers=headers,
        json={"0": {
            "json": {
                "url": album_url,
            },
        }},
    )

    data = resp.json()

    if data and len(data) > 0 and "error" in data[0]:
        return None

    if not data or len(data) == 0:
        return None

    if "result" not in data[0]:
        return None

    if "data" not in data[0]["result"]:
        return None

    if "json" not in data[0]["result"]["data"]:
        return None

    link_string: str = data[0]["result"]["data"]["json"]
    links: list[str] = link_string.split("\n")

    for link in links:
        if not link.startswith("https://i.imgur.com/"):
            return None

    return links


def get_primary_image_from_album(album_url: str) -> str | None:
    links = grab_direct_links(album_url)

    if not links or not links[0]:
        return None

    return links[0]


def extract_imgur_links_from_post(post_body: str) -> list[str]:
    pattern = r"https?:\/\/(?:www\.)?imgur\.com\/(?:a|gallery)\/[A-Za-z0-9_-]+"
    matches = regexp.findall(pattern=pattern, string=post_body)
    if not matches:
        return []

    return matches


def get_primary_image_from_reddit_post(post_body: str) -> str | None:
    album_url = extract_imgur_links_from_post(post_body)

    if not config.parse_imgur_links:
        return None

    if not album_url or not album_url[0]:
        # return default image
        return None

    links = grab_direct_links(album_url[0])

    if not links or not links[0]:
        return None

    # Sleep before returning since this API isn't meant to be public so it has weird rate limiting issues
    time.sleep(random.uniform(1, 3))

    return links[0]
