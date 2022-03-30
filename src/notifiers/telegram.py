import logging
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
            for chat_id in self.chat_id.split(','):
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
        log.warning(
            "You enabled the Telegram notifications without providing a chat id!")
        messages = []
        messages = self.bot.get_updates(timeout=10)
        while len(messages) == 0:
            input("Please send a message to your bot. \n Press Return to continue ...")
            messages = self.bot.get_updates(timeout=60)
        chat_id = messages[-1].message.chat.id
        log.warning("Chat id of the last message the bot received: %s", chat_id)
        self.chat_id = chat_id
        if self.config.set("TELEGRAM", "chat_id", str(chat_id)):
            log.warning("Saved chat id in your config file")
        else:
            log.warning(
                "It is recommended to set the TELEGRAM_CHAT_ID variable")
