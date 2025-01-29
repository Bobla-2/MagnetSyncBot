from telegram_app import TelegramBot
from module.crypto_token import config
import argparse


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

    tg_bot = TelegramBot(config.get_token())
    print("BOT STARTED")
    try:
        tg_bot.run()
    except Exception as e:
        print(f"tg_bot.run() ERROR {e}")