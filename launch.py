from bot import CustomBot
from config import Config


def main():
    bot = CustomBot(
        config=Config(),
    )
    bot.run()


if __name__ == "__main__":
    main()
