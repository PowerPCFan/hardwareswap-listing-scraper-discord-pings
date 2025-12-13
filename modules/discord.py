import requests
import time
import re as regexp
from .logger import logger
from .price import Price


def create_embed(
    url: str,
    author: str,
    trades: str,
    have: str,
    want: str,
    joined: str,
    post_karma: str,
    comment_karma: str,
    date_posted: str,
    post_body: str,
    prices: Price | None,
    image_url: str | None
) -> dict:
    post_body_value_field = ""
    max_embed_field_length = 1024

    # turn post body into markdown blockquote
    for line in post_body.split("\n"):
        line = "> " + line
        post_body_value_field += line + "\n"

    # strip some markdown like headings (use regex to ensure the # is at the start of the line)
    post_body_value_field = regexp.sub(r"^(?:\s*>)*\s*#{1,6}\s*", "> ", post_body_value_field, flags=regexp.MULTILINE)

    # Converts something like [https://google.com](https://google.com) to just https://google.com,
    # since Discord doesn't display links with a URL as display text (even if it's the same url) to avoid phishing.
    # Doesn't touch links like [Google](https://google.com) since those are valid in Discord.
    post_body_value_field = regexp.sub(r"\[([^\]]+)\]\(\1\)", r"\1", post_body_value_field, flags=regexp.MULTILINE)

    # truncate if too long
    if len(post_body_value_field) > max_embed_field_length:
        truncation_text = "... (view full post content on Reddit)"
        length = max_embed_field_length - len(truncation_text)
        post_body_value_field = post_body_value_field[:length] + truncation_text

        # silly goobery thingy
        if post_body_value_field.endswith("\n> "):
            post_body_value_field = post_body_value_field[:-3] + "\n" + truncation_text
        post_body_value_field = post_body_value_field.replace(f"> {truncation_text}", truncation_text)

    embed = {
        "title": f"A new listing by u/{author} has been posted on r/HardwareSwap!",
        "url": url,
        "color": 0x3498db,

        "fields": [
            {
                "name": "User:",
                "value": f"[u/{author}](https://www.reddit.com/user/{author})",
                "inline": False
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
                "inline": False
            },
            {
                "name": "Post Content:",
                "value": post_body_value_field,
                "inline": False
            }
        ],
        "thumbnail": {
            "url": "https://raw.githubusercontent.com/PowerPCFan/hardwareswap-listing-scraper/refs/heads/main/assets/3.png"  # noqa: E501
        },
    }

    if image_url:
        embed["image"] = {"url": image_url}

    # this is so messy lmao
    if prices:
        fields = embed.get("fields", None)
        if fields:
            fields = list(fields)
            if prices.price_string and len(prices.prices) > 0:
                fields.insert(-2, {
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

    logger.debug(f"Sending Discord webhook to: {webhook_url}...")

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
