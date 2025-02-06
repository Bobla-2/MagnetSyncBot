from telegram_app import TelegramBot
from module.crypto_token import config
import argparse
import time

def parse_arguments():
    parser = argparse.ArgumentParser(description="Bot settings")
    parser.add_argument("-p", "--proxy", type=str, help="Set the proxy")
    parser.add_argument("-j", "--jellyfin", type=bool, help="enable generate simlink for jellyfin [True, False]")
    args = parser.parse_args()
    if args.proxy:
        config.proxy = args.proxy
    if args.jellyfin:
        config.jellyfin = args.jellyfin
    print(f"Принят параметр: {args}")


if __name__ == '__main__':
    parse_arguments()

    tg_bot = TelegramBot()
    tg_bot.setup(config.get_token())
    print("BOT STARTED")
    while True:
        try:
            tg_bot.run()
        except Exception as e:
            print(f"tg_bot.run() ERROR {e}")
            time.sleep(1)