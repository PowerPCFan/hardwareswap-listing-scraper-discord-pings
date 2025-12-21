import time
from . import usl
from . import reddit
from .configuration import config
from .utils import parse_have_want, print_new_post, matches_pattern, is_globally_blocked, matches_blocklist_override
from .logger import logger
from .imgur import get_image_for_embed
from .price import get_prices_from_reddit_post


def match(initialize_response: reddit.InitializeResponse) -> None:
    logger.info("Starting to monitor for new submissions...")
    post_stream = initialize_response.subreddit.stream.submissions(skip_existing=(not config.debug_mode))

    for submission in post_stream:
        title = submission.title
        body = submission.selftext
        author = submission.author
        utc_date = submission.created_utc
        url = submission.url
        flair_text = submission.author_flair_text

        logger.debug(f"Processing new submission: {url}")

        # note: flair not included bc sometimes users have no flair instead of the default "Trades: None" or whatever
        # also didn't include url since it exists 99.99999% of the time
        if None in [title, body, author, utc_date]:
            logger.warning(f"Skipping submission with missing data: {submission.url or 'Unknown URL'}")
            continue

        if config.filter_old_posts:
            # if the post is older than the threshold, skip it
            if ((time.time() - utc_date) > config.old_post_threshold_seconds) and not config.debug_mode:
                logger.warning(f"Submission older than {config.old_post_threshold_seconds} seconds was retrieved: {url}. Skipping.")  # noqa: E501
                continue

        if config.check_usl:
            if usl.is_on_usl(author.name):
                logger.info(f"u/{author.name} is on the USL. Skipping post {url}.")
                continue

        if config.check_if_post_was_deleted:
            time.sleep(10)  # allow 10 seconds for automod to delete the post
            refresh_post = reddit.Submission(reddit=initialize_response.reddit, id=submission.id)
            if refresh_post.removed_by_category:
                logger.info(f"Submission {url} was removed. Skipping.")
                continue

        h, w, title_only_h = parse_have_want(
            title=title,
            body=body if config.parse_body else None,
            include_body=config.parse_body
        )

        logger.info(f"New post from u/{author.name}: {url}")

        image_url = None
        prices = None
        img_and_prices_retrieved = False

        if config.all_listings_webhook and config.all_listings_role:
            image_url = get_image_for_embed(body)
            prices = get_prices_from_reddit_post(body)
            img_and_prices_retrieved = True

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
                image_url=image_url,
                prices=prices
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

                    if not img_and_prices_retrieved:
                        image_url = get_image_for_embed(body)
                        prices = get_prices_from_reddit_post(body)
                        img_and_prices_retrieved = True

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
                        image_url=image_url,
                        prices=prices
                    )

        if len(matched_categories) > 1:
            categories_str = ", ".join(matched_categories)
            # logger.warning(
            logger.info(
                f"Post matches multiple categories which may result in false positives. "
                f"URL: {url} | Categories: {categories_str}"
            )
        elif len(matched_categories) == 0:
            logger.debug(f"Post did not match any categories: {url}")
