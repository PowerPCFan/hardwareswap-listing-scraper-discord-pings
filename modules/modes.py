from . import reddit
from .configuration import config
from .utils import parse_have_want, print_new_post, matches_pattern, is_globally_blocked, matches_blocklist_override
from .logger import logger


def match(subreddit: reddit.Subreddit) -> None:
    logger.info("Starting to monitor for new submissions...")
    post_stream = subreddit.stream.submissions(skip_existing=(not config.debug_mode))

    for submission in post_stream:
        title = submission.title
        body = submission.selftext
        author = submission.author
        utc_date = submission.created_utc
        url = submission.url
        flair_text = submission.author_flair_text

        if None in [title, body, author, utc_date, url, flair_text]:
            logger.warning(f"Skipping submission with missing data: {submission.url or f'unknown URL, id: {submission.id or 'unknown id'}'}")  # type: ignore  # noqa: E501
            continue

        logger.debug(f"Processing new submission: {url}")

        h, w, title_only_h = parse_have_want(
            title=title,
            body=body if config.parse_body else None,
            include_body=config.parse_body
        )

        logger.info(f"New post from u/{author.name}: {url}")

        if config.all_listings_webhook and config.all_listings_role:
            # Send to all listings webhook (always send regardless of global blocklist)
            print_new_post(
                author=author,
                h=h,
                w=w,
                title_only_h=title_only_h,
                url=url,
                utc_date=utc_date,
                flair=flair_text,
                post_body=body,
                webhook=config.all_listings_webhook,
                role=config.all_listings_role,
                is_all_listings_webhook=True,
            )

        matched_categories = []

        for ping_config in config.pings:
            if (
                any(matches_pattern(h, pattern) for pattern in ping_config.h) and
                any(matches_pattern(w, pattern) for pattern in ping_config.w) and
                not any(matches_pattern(h, pattern) for pattern in ping_config.not_h) and
                not any(matches_pattern(w, pattern) for pattern in ping_config.not_w)
            ):
                has_override = matches_blocklist_override(h, w, title_only_h, ping_config.blocklist_override or [])

                if has_override or not is_globally_blocked(h, w, title_only_h):
                    matched_categories.append(ping_config.category_name)
                    if has_override:
                        logger.info(f"Post matches category: {ping_config.category_name} (blocklist override applied)")
                    else:
                        logger.info(f"Post matches category: {ping_config.category_name}")

                    print_new_post(
                        author=author,
                        h=h,
                        w=w,
                        title_only_h=title_only_h,
                        url=url,
                        utc_date=utc_date,
                        flair=flair_text,
                        post_body=body,
                        webhook=ping_config.webhook,
                        role=ping_config.role,
                        category_name=ping_config.category_name,
                    )

        if len(matched_categories) > 1:
            categories_str = ", ".join(matched_categories)
            logger.warning(
                f"Post matches multiple categories which may result in false positives. "
                f"URL: {url} | Categories: {categories_str}"
            )
        elif len(matched_categories) == 0:
            logger.debug(f"Post did not match any categories: {url}")
