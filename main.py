from telegram_app import TelegramBot
from flask_app import app
from module.crypto_token import config
import time
from module.logger.logger import SimpleLogger
import traceback


if __name__ == '__main__':
    SimpleLogger().log(f"[main] : config.UI_MODE =  {config.UI_MODE.lower()}")
    if config.UI_MODE.lower() == "web":
        app.run(host="0.0.0.0", port=8080, debug=True)
    elif config.UI_MODE.lower() == "tg":
        tg_bot = TelegramBot()
        SimpleLogger().log("[main] : BOT STARTED")
        while True:
            try:
                SimpleLogger().log("[main] : BOT setup")
                tg_bot.setup(config.tg_token)
                SimpleLogger().log("[main] : BOT run")
                tg_bot.run()
            except Exception as e:
                SimpleLogger().log(f"[main] : tg_bot.run() ERROR {e}")
                time.sleep(1)
    else:
        pass


