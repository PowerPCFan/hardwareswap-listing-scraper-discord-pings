import requests
import re as regexp
import random
import time
from typing import Any
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
        json={
            "0": {
                "json": {
                    "url": album_url,
                },
            }
        },
    )

    data: dict = resp.json()

    if not data or len(data) == 0:
        return None

    first_item: Any = data[0] if isinstance(data, list) else data

    if "error" in first_item:
        return None

    result: dict[str, Any] | None = first_item.get("result")
    if not result:
        return None

    result_data: dict[str, Any] | None = result.get("data")
    if not result_data:
        return None

    link_string: str | None = result_data.get("json")
    if not link_string:
        return None

    links: list[str] = link_string.split("\n")

    for link in links:
        if not link.startswith("https://i.imgur.com/"):
            return None

    return links


def get_primary_image_from_album(album_url: str) -> str | None:
    links = grab_direct_links(album_url)

    if not links or len(links) == 0:
        return None

    return links[0]


def extract_imgur_links_from_post(post_body: str) -> list[str]:
    pattern = r"https?:\/\/(?:www\.)?imgur\.com\/(?:a|gallery)\/[A-Za-z0-9_-]+"
    matches: list[str] = regexp.findall(pattern=pattern, string=post_body)
    if not matches:
        return []

    return matches


def get_primary_image_from_reddit_post(post_body: str) -> str | None:
    album_url = extract_imgur_links_from_post(post_body)

    if not config.parse_imgur_links:
        return None

    if not album_url or len(album_url) == 0:
        # return default image
        return None

    links = grab_direct_links(album_url[0])

    if not links or len(links) == 0:
        return None

    # Sleep 1-3 secs before returning since this API isn't meant to be public so it has weird rate limiting issues
    time.sleep(random.uniform(1, 3))

    return links[0]
