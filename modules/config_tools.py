import json
import os
from dataclasses import dataclass

CONFIG_JSON = "config.json"


@dataclass
class PingConfig:
    # chat if you're new to the stream
    # h is short for have
    # w is short for want
    # and calc is short for calculator

    category_name: str

    h: list[str]
    w: list[str]
    not_h: list[str]
    not_w: list[str]

    webhook: str
    role: int

    blocklist_override: list[str]


@dataclass
class Config:
    debug_mode: bool
    full_tracebacks: bool
    parse_body: bool
    parse_imgur_links: bool
    send_test_webhooks: bool
    combine_images: bool
    ping_for_warnings: bool
    check_if_post_was_deleted: bool
    file_logging: bool

    cdn_exploit_webhook: str

    logger_webhook: str

    reddit_id: str
    reddit_secret: str
    reddit_username: str

    pings: list[PingConfig]

    global_blocklist: list[str]

    logger_webhook_ping: int | None = None

    all_listings_webhook: str | None = None
    all_listings_role: int | None = None

    @staticmethod
    def load() -> "Config":
        if not os.path.exists(CONFIG_JSON):
            raise FileNotFoundError(f"Error: {CONFIG_JSON} not found.")

        with open(CONFIG_JSON) as f:
            data = json.load(f)

        pings_data = data.pop("pings", [])
        pings = [PingConfig(**ping_data) for ping_data in pings_data]

        return Config(pings=pings, **data)
