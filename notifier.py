import functools
import traceback

import yaml
from slack_sdk.webhook import WebhookClient

url = yaml.safe_load(open("config.yaml"))["slack"]["webhook_url"]
wh = WebhookClient(url)


def send_slack(text: str):
    wh.send(text=text)


def slack_exception_handler(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        try:
            return func(*a, **kw)
        except Exception:
            send_slack(
                f":warning: {func.__name__} failed\n```{traceback.format_exc()}```"
            )
            raise

    return wrapper
