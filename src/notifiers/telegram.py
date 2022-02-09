import requests
from models import Item, Config, TelegramConfigurationError
import logging
import telegram

log = logging.getLogger('tgtg')

class Telegram():
    def __init__(self, config: Config):
        self.enabled = config.telegram["enabled"]
        self.token = config.telegram["token"]
        self.chat_id = config.telegram["chat_id"]
        self.bot = telegram.Bot(token=self.token)
    def send(self, item: Item):
        if self.enabled:
            log.info("Sending Telegram Notification")
            fmt = telegram.ParseMode.MARKDOWN
            name = item.display_name
            items = item.items_available
            price = item.price
            currency = item.currency
            pickup = item.pickupdate()

            message = "*%s*\n*Available*: %d\n*Price*: %.2f %s\n*Pickup*: %s" % (name, items, price,currency, pickup)
            try:
                self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode=fmt)
            except Exception:
                raise TelegramConfigurationError()


