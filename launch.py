from bot import CustomBot
from config import Config

bot = CustomBot(
    config=Config(),
)
bot.run()
