from telegram_app import TelegramBot
from module.crypto_token import config
import sys

if __name__ == '__main__':

    if len(sys.argv) > 1:
        param = sys.argv[1]
        config.proxy = param
        print(f"Принят параметр: {param}")
    tg_bot = TelegramBot(config.get_token())
    print("BOT STARTED")
    try:
        tg_bot.run()
    except Exception as e:
        print(f"tg_bot.run() ERROR {e}")