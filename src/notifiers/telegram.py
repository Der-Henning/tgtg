import logging
from time import sleep
import random
import telegram
from models import Item, Config, TelegramConfigurationError

log = logging.getLogger('tgtg')


class Telegram():
    def __init__(self, config: Config):
        self.config = config
        self.enabled = config.telegram["enabled"]
        self.token = config.telegram["token"]
        self.chat_id = config.telegram["chat_id"]
        if self.enabled and not self.token:
            raise TelegramConfigurationError("Missing Telegram token")
        if self.enabled:
            try:
                self.bot = telegram.Bot(token=self.token)
                self.bot.get_me(timeout=60)
            except Exception as err:
                raise TelegramConfigurationError()
        if self.enabled and not self.chat_id:
            self._get_chat_id()

    def send(self, item: Item):
        if self.enabled:
            log.debug("Sending Telegram Notification")
            fmt = telegram.ParseMode.MARKDOWN
            name = item.display_name
            items = item.items_available
            price = item.price
            currency = item.currency
            pickupdate = item.pickupdate

            message = "*%s*\n*Available*: %d\n*Price*: %.2f %s\n*Pickup*: %s" % (
                name, items, price, currency, pickupdate)
            for chat_id in str(self.chat_id).split(','):
                try:
                    self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=fmt,
                        timeout=60
                    )
                except Exception as err:
                    log.error(err)
                    #raise TelegramConfigurationError()

    def _get_chat_id(self):
        """Initializes an interaction with the user to obtain the telegram chat id. \n
        On using the config.ini configuration the chat id will be stored in the config.ini.
        """
        log.warning(
            "You enabled the Telegram notifications without providing a chat id!")
        code = random.randint(1111, 9999)
        log.warning("Send %s to the bot in your desired chat.", code)
        log.warning("Waiting for code ...")
        while not self.chat_id:
            updates = self.bot.get_updates(timeout=60)
            for update in reversed(updates):
                if int(update.message.text) == code:
                    log.warning(
                        "Received code from %s %s on chat id %s",
                        update.message.from_user.first_name,
                        update.message.from_user.last_name,
                        update.message.chat_id
                    )
                    self.chat_id = str(update.message.chat_id)
            sleep(1)
        if self.config.set("TELEGRAM", "chat_id", self.chat_id):
            log.warning("Saved chat id in your config file")
        else:
            log.warning(
                "For persistence please set TELEGRAM_CHAT_ID=%s", self.chat_id
            )
