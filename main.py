from telegram_app import TelegramBot
from module.crypto_token import config
import argparse
import time
from module.logger.logger import SimpleLogger

def parse_arguments():
    parser = argparse.ArgumentParser(description="Bot settings")
    parser.add_argument("-p", "--proxy", type=str, help="Set the proxy")
    parser.add_argument("-j", "--jellyfin", type=bool, help="enable generate simlink for jellyfin [True, False]")
    args = parser.parse_args()
    if args.proxy:
        config.proxy = args.proxy
    if args.jellyfin:
        config.jellyfin = args.jellyfin
    SimpleLogger().log(f"Принят параметр: {args}")


if __name__ == '__main__':
    parse_arguments()

    tg_bot = TelegramBot()
    SimpleLogger().log("BOT STARTED")
    while True:
        try:
            tg_bot.setup(config.get_token())
            tg_bot.run()
        except Exception as e:
            SimpleLogger().log(f"tg_bot.run() ERROR {e}")
            time.sleep(1)


