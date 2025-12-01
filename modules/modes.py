import reddit
from configuration import config
from utils import parse_have_want, print_new_post


def match(subreddit: reddit.Subreddit) -> None:
    post_stream = subreddit.stream.submissions(skip_existing=True)

    for submission in post_stream:
        h, w = parse_have_want(submission.title)

        for ping_config in config.pings:
            author_has_lower = [s.lower() for s in ping_config.h]
            author_wants_lower = [s.lower() for s in ping_config.w]

            if any(s in h.lower() for s in author_has_lower) and any(s in w.lower() for s in author_wants_lower):
                print_new_post(
                    subreddit=subreddit,
                    author=submission.author,
                    h=h,
                    w=w,
                    url=submission.url,
                    utc_date=submission.created_utc,
                    flair=submission.author_flair_text,
                    title=submission.title,
                    ping_config=ping_config
                )
