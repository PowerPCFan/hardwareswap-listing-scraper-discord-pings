from . import reddit
from .configuration import config
from .utils import parse_have_want, print_new_post


def match(subreddit: reddit.Subreddit) -> None:
    post_stream = subreddit.stream.submissions(skip_existing=True)

    for submission in post_stream:
        h, w = parse_have_want(submission.title)

        print_new_post(
            author=submission.author,
            h=h,
            w=w,
            url=submission.url,
            utc_date=submission.created_utc,
            flair=submission.author_flair_text,
            webhook=config.all_listings_webhook,
            role=config.all_listings_role,
            is_all_listings_webhook=True,
        )

        for ping_config in config.pings:
            author_has_lower = [s.lower() for s in ping_config.h]
            author_wants_lower = [s.lower() for s in ping_config.w]

            if any(s in h.lower() for s in author_has_lower) and any(s in w.lower() for s in author_wants_lower):
                print_new_post(
                    author=submission.author,
                    h=h,
                    w=w,
                    url=submission.url,
                    utc_date=submission.created_utc,
                    flair=submission.author_flair_text,
                    webhook=ping_config.webhook,
                    role=ping_config.role,
                    category_name=ping_config.category_name,
                )
