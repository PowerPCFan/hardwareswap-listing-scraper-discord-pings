import re as regexp
from typing import NamedTuple


class Price(NamedTuple):
    # named tuple for easier handling of price data
    prices: list[float]
    price_string: str


def _normalize_price(price: str, suffix: str = "") -> float | None:
    # remove commas and whitespace
    normalized_price = price.replace(",", "").strip()

    # return none if the price is empty for some reason after normalization
    if not normalized_price:
        return None

    # return the converted value or none
    # will look something like `1299.99`
    try:
        value = float(normalized_price)

        suffix_lower = suffix.lower().strip()
        if suffix_lower == "k":
            value *= 1000
        elif suffix_lower == "m":
            value *= 1_000_000

        return value
    except ValueError:
        return None


# Match common price forms in HWS posts:
# - $1299, $1,299.99, USD 1299
# - 1299$, 1.2k$, $1.2k
# - supports ranges like "$500-600" (second value can omit the dollar sign)
_PRICE_VALUE = r"\d{1,3}(?:,\d{3})*|\d+"
_PRICE_DECIMAL = r"(?:\.\d{1,2})?"
_PRICE_SUFFIX = r"[kKmM]?"

_PRICE_PATTERN = regexp.compile(
    rf"""
    (?<![\w.])
    (?:
        (?:\$|usd\s*)\s*(?P<first>{_PRICE_VALUE}{_PRICE_DECIMAL})\s*(?P<first_suffix>{_PRICE_SUFFIX})
        (?:\s*[-–to]+\s*(?:\$|usd\s*)?\s*(?P<second>{_PRICE_VALUE}{_PRICE_DECIMAL})\s*(?P<second_suffix>{_PRICE_SUFFIX}))?
      |
        (?P<trailing>{_PRICE_VALUE}{_PRICE_DECIMAL})\s*(?P<trailing_suffix>{_PRICE_SUFFIX})\s*\$
    )
    (?!\w)
    """,
    regexp.IGNORECASE | regexp.VERBOSE,
)


def get_prices_from_reddit_post(post_body: str) -> Price | None:
    matches: list[float] = []

    for match in _PRICE_PATTERN.finditer(post_body):
        # price with trailing $ format (e.g., "500$" or "1.2k$")
        trailing = match.group("trailing")
        trailing_suffix = match.group("trailing_suffix")
        if trailing:
            normalized = _normalize_price(trailing, trailing_suffix or "")
            if normalized is not None:
                matches.append(normalized)
            continue

        # leading currency format (e.g., "$500", "USD 500", "$500-600")
        first = match.group("first")
        first_suffix = match.group("first_suffix")
        if first:
            normalized_first = _normalize_price(first, first_suffix or "")
            if normalized_first is not None:
                matches.append(normalized_first)

        second = match.group("second")
        second_suffix = match.group("second_suffix")
        if second:
            normalized_second = _normalize_price(second, second_suffix or "")
            if normalized_second is not None:
                matches.append(normalized_second)

    if not matches:
        return None

    # Preserve order but avoid duplicate values from overlapping textual formats.
    deduped_matches = list(dict.fromkeys(matches))

    return Price(
        prices=deduped_matches,
        price_string=", ".join(f"${match:,.2f}" for match in deduped_matches)
    )
