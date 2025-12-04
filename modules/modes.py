from . import reddit
from .configuration import config
from .utils import parse_have_want, print_new_post
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

        logger.debug(f"Processing new submission: {url}")

        h, w, title_only_h = parse_have_want(
            title=title,
            body=body if config.parse_body else None,
            include_body=config.parse_body
        )

        logger.info(f"New post from u/{author.name}: {url}")

        # Send to all listings webhook
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

        # Check for category matches
        matched_categories = []

        for ping_config in config.pings:
            author_has_lower = [s.lower() for s in ping_config.h]
            author_wants_lower = [s.lower() for s in ping_config.w]
            author_doesnt_have_lower = [s.lower() for s in ping_config.not_h]
            author_doesnt_want_lower = [s.lower() for s in ping_config.not_w]

            if (
                any(s in h.lower() for s in author_has_lower) and
                any(s in w.lower() for s in author_wants_lower) and
                not any(s in h.lower() for s in author_doesnt_have_lower) and
                not any(s in w.lower() for s in author_doesnt_want_lower)
            ):
                matched_categories.append(ping_config.category_name)
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
