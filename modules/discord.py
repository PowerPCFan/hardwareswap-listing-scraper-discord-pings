import requests
from .logger import logger
import time
from .imgur import get_primary_image_from_reddit_post
from .price import get_prices_from_reddit_post


def create_embed(
    url: str, author: str, trades: str, have: str, want: str,
    joined: str, post_karma: str, comment_karma: str, date_posted: str, post_body: str
) -> dict:

    embed = {
        "title": f"A new listing by u/{author} has been posted on r/HardwareSwap!",
        "url": url,
        "color": 0x3498db,

        "fields": [
            {
                "name": "User:",
                "value": f"[u/{author}](https://www.reddit.com/user/{author})",
                "inline": True
            },
            {
                "name": "User Info:",
                "value": (
                    "ℹ️ *Be sure to check these values, they can be helpful for spotting scams!*\n"
                    f"- **{trades}** trades\n"
                    f"- Joined **{joined}**\n"
                    f"- **{post_karma}** post karma\n"
                    f"- **{comment_karma}** comment karma"
                ),
                "inline": False
            },
            {
                "name": "Has:",
                "value": have,
                "inline": False
            },
            {
                "name": "Wants:",
                "value": want,
                "inline": False
            },
            {
                "name": "Date Posted:",
                "value": date_posted,
                "inline": True
            }
        ],
        "thumbnail": {
            "url": "https://raw.githubusercontent.com/PowerPCFan/hardwareswap-listing-scraper/refs/heads/main/assets/3.png"  # noqa: E501
        },
    }

    primary_image = get_primary_image_from_reddit_post(post_body)
    if primary_image:
        embed["image"] = {"url": primary_image}

    # this is so messy lmao
    prices = get_prices_from_reddit_post(post_body)
    if prices:
        fields = embed.get("fields", None)
        if fields:
            fields = list(fields)
            if prices.price_string and len(prices.prices) > 0:
                fields.insert(-1, {
                    "name": "Prices:" if len(prices.prices) > 1 else "Price:",
                    "value": prices.price_string,
                    "inline": False
                })
                embed["fields"] = fields

    return embed


def send_webhook(
    webhook_url: str,
    content: str | None,
    embed: dict | None,
    username: str | None,
    raise_exception_instead_of_print: bool = False
) -> None:
    # Prepare the JSON payload
    json_data = {
        "content": content if content is not None else "",
        "embeds": [embed] if embed is not None else [],
        "username": username if username is not None else ""
    }

    logger.debug(f"Sending Discord webhook to: {webhook_url[:30]}...")

    # Send the webhook
    try:
        response = requests.post(webhook_url, json=json_data)

        if response.status_code == 429:
            logger.warning("Discord rate limit hit, retrying after delay...")
            default_retry = 1.5

            try:
                retry_after = dict(response.json()).get("retry_after", default_retry)
                logger.debug(f"Rate limit retry delay: {retry_after}s")
                time.sleep(retry_after)
                response = requests.post(webhook_url, json=json_data)
            except ValueError:
                logger.debug(f"Using default retry delay: {default_retry}s")
                time.sleep(default_retry)
                response = requests.post(webhook_url, json=json_data)

        if response.status_code not in [200, 204]:
            logger.error(f"Webhook failed with status {response.status_code}: {response.text}")
        else:
            logger.debug("Discord webhook sent successfully")
    except requests.exceptions.RequestException as e:
        error_msg = f"Error sending webhook: {e}"
        logger.error(error_msg)
        if raise_exception_instead_of_print:
            raise Exception(error_msg)
