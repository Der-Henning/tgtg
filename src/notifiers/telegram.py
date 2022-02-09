import sys
import logging
import telegram
from models import Item, Config, TelegramConfigurationError

log = logging.getLogger('tgtg')


class Telegram():
    def __init__(self, config: Config):
        self.enabled = config.telegram["enabled"]
        self.token = config.telegram["token"]
        self.chat_id = config.telegram["chat_id"]
        if self.enabled and not self.token:
            raise TelegramConfigurationError("Missing Telegram token")
        if self.enabled:
            try:
                self.bot = telegram.Bot(token=self.token)
                self.bot.get_updates()
            except Exception as err:
                raise TelegramConfigurationError()
        if self.enabled and not self.chat_id:
            self._get_chat_id()

    def send(self, item: Item):
        if self.enabled:
            log.info("Sending Telegram Notification")
            fmt = telegram.ParseMode.MARKDOWN
            name = item.display_name
            items = item.items_available
            price = item.price
            currency = item.currency
            pickupdate = item.pickupdate

            message = "*%s*\n*Available*: %d\n*Price*: %.2f %s\n*Pickup*: %s" % (
                name, items, price, currency, pickupdate)
            try:
                self.bot.send_message(
                    chat_id=self.chat_id, text=message, parse_mode=fmt)
            except Exception:
                raise TelegramConfigurationError()

    def _get_chat_id(self):
        log.warning("You enabled the Telegram notifications without providing a chat id!")
        messages = self.bot.get_updates()
        while len(messages) == 0:
            input("Please send a message to your bot. \n Press Return to continue ...")
        log.warning("Chat id of the last message the bot received: %s",
                 messages[-1].message.chat.id)
        log.warning("Please copy the chat id to your config and restart the scanner")
        sys.exit()
