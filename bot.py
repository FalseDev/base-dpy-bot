from botbase import Bot
from config import Config


class CustomBot(Bot):
    def __init__(self, *, config: Config):
        super().__init__(
            # TODO Modify these fields
            command_prefix="!",
            description="",
            config=config,
            load_extensions=True,
            loadjsk=True,
        )
