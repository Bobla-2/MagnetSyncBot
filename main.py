from telegram_app import TelegramBot
from module.crypto_token.config import get_token


if __name__ == '__main__':
    tg_bot = TelegramBot(get_token())
    print("BOT STARTED")
    try:
        tg_bot.run()
    except Exception as e:
        print(f"tg_bot.run() ERROR {e}")