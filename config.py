import os

try:
    import dotenv
except ImportError:
    pass
else:
    dotenv.load_dotenv("env")


class Config:
    def __init__(self):
        self.bot_token: str = os.environ["BOT_TOKEN"]
        self.log_webhook: str = os.environ["LOG_WEBHOOK"]
