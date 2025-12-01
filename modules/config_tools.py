import json
import os
import kroma
from dataclasses import dataclass
from typing import List

CONFIG_JSON = "config.json"


@dataclass
class PingConfig:
    # chat if you're new to the stream
    # h is short for have
    # w is short for want
    # and calc is short for calculator
    category_name: str
    h: List[str]
    w: List[str]
    webhook: str
    role: int


@dataclass
class Config:
    reddit_id: str
    reddit_secret: str
    reddit_username: str

    all_listings_webhook: str
    all_listings_role: int

    pings: List[PingConfig]

    @staticmethod
    def load(json_path="config.json") -> "Config":
        if not os.path.exists(json_path):
            raise FileNotFoundError(kroma.style(text=f"Error: {json_path} not found.", foreground=kroma.ANSIColors.RED))

        with open(json_path) as f:
            data = json.load(f)

        pings_data = data.pop("pings", [])
        pings = [PingConfig(**ping_data) for ping_data in pings_data]

        return Config(pings=pings, **data)
