import re as regexp
from typing import NamedTuple


class Price(NamedTuple):
    # named tuple for easier handling of price data
    prices: list[float]
    price_string: str


def _normalize_price(price: str) -> float | None:
    # remove commas and whitespace
    normalized_price = price.replace(",", "").strip()

    # return none if the price is empty for some reason after normalization
    if not normalized_price:
        return None

    # return the converted value or none
    # will look something like `1299.99`
    try:
        return float(normalized_price)
    except ValueError:
        return None


def get_prices_from_reddit_post(post_body: str) -> Price | None:
    price_regex = r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)"
    # get a list with all price matches, might look like: ['1,299.99', '2500', '49.95']
    unprocessed_matches: list[str] = regexp.findall(price_regex, post_body)

    if not unprocessed_matches:
        return None

    matches: list[float] = []

    for match in unprocessed_matches:
        # normalize the prices to a float by removing commas. returns none if theres an error parsing to float
        normalized = _normalize_price(match)
        if normalized is not None:
            # only append if normalization was successful
            matches.append(normalized)

    return Price(
        prices=matches,
        price_string=", ".join(f"${match:,.2f}" for match in matches)
    )
