from config import Config
from bot import CustomBot

bot = CustomBot(
    config=Config(),
)
bot.run()
