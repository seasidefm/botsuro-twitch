import os

from dotenv import load_dotenv
from bot import Bot
import sentry_sdk


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    print("Starting bot ->")
    load_dotenv()

    sentry_dsn = os.environ.get("SENTRY_DSN")
    sentry_sdk.init(
        sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
    )

    bot = Bot()
    bot.run()
