import logging
from time import sleep
import random
import telegram
import datetime
from telegram.ext import Updater, CommandHandler
from telegram.bot import BotCommand
from models import Item, Config, TelegramConfigurationError

log = logging.getLogger('tgtg')


class Telegram():
    def __init__(self, config: Config):
        self.updater = None
        self.config = config
        self.enabled = config.telegram["enabled"]
        self.token = config.telegram["token"]
        self.body = config.telegram["body"]
        self.chat_ids = config.telegram["chat_ids"]
        self.mute = None
        if self.enabled and not self.token:
            raise TelegramConfigurationError("Missing Telegram token")
        if self.enabled:
            Item.check_mask(self.body)
            try:
                self.updater = Updater(token=self.token)
                self.updater.bot.get_me(timeout=60)
            except Exception as err:
                raise TelegramConfigurationError()
            if not self.chat_ids:
                self._get_chat_id()
            self.updater.dispatcher.add_handler(CommandHandler("help", self._help))
            self.updater.dispatcher.add_handler(CommandHandler("mute", self._mute))
            self.updater.dispatcher.add_handler(CommandHandler("unmute", self._unmute))
            self.updater.dispatcher.add_error_handler(self._error)
            self.updater.bot.set_my_commands([
                BotCommand('help', 'Displays available Commands'),
                BotCommand('mute', 'Deaktivates Telegram Notifications for x days'),
                BotCommand('unmute', 'Reactivates Telegram Notifications')
            ])
            self.updater.start_polling()

    def send(self, item: Item):
        if self.enabled:
            if self.mute and self.mute > datetime.datetime.now():
                return
            elif self.mute:
                log.info("Reactivated Telegram Notifications")
                self.mute = None
            log.debug("Sending Telegram Notification")
            fmt = telegram.ParseMode.MARKDOWN
            message = item.unmask(self.body)
            log.debug(message)
            for chat_id in self.chat_ids:
                try:
                    self.updater.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=fmt,
                        timeout=60,
                        disable_web_page_preview=True
                    )
                except Exception as err:
                    log.error(err)
                    #raise TelegramConfigurationError()

    def _help(self, update, context):
        """Send message containing available bot commands"""
        update.message.reply_text('Deactivate Telegram Notifications for x days using\n/mute x\nReactivate with /unmute')

    def _mute(self, update, context):
        """Deactivates Telegram Notifications for x days"""
        days = int(context.args[0]) if context.args and context.args[0].isnumeric() else 1
        self.mute = datetime.datetime.now() + datetime.timedelta(days=days)
        log.info('Deactivated Telegram Notifications for %s days', days)
        log.info('Reactivation at %s', self.mute)
        update.message.reply_text(f"Deactivated Telegram Notifications for {days} days.\nReactivating at {self.mute} or use /unmute.")

    def _unmute(self, update, context):
        """Reactivate Telegram Notifications"""
        self.mute = None
        log.info("Reactivated Telegram Notifications")
        update.message.reply_text("Reactivated Telegram Notifications")
    
    def _error(self, update, context):
        """Log Errors caused by Updates."""
        log.warning('Update "%s" caused error "%s"', update, context.error)

    def _get_chat_id(self):
        """Initializes an interaction with the user to obtain the telegram chat id. \n
        On using the config.ini configuration the chat id will be stored in the config.ini.
        """
        log.warning(
            "You enabled the Telegram notifications without providing a chat id!")
        code = random.randint(1111, 9999)
        log.warning("Send %s to the bot in your desired chat.", code)
        log.warning("Waiting for code ...")
        while not self.chat_ids:
            updates = self.updater.bot.get_updates(timeout=60)
            for update in reversed(updates):
                if int(update.message.text) == code:
                    log.warning(
                        "Received code from %s %s on chat id %s",
                        update.message.from_user.first_name,
                        update.message.from_user.last_name,
                        update.message.chat_id
                    )
                    self.chat_ids = [str(update.message.chat_id)]
            sleep(1)
        if self.config.set("TELEGRAM", "chat_ids", ','.join(self.chat_ids)):
            log.warning("Saved chat id in your config file")
        else:
            log.warning(
                "For persistence please set TELEGRAM_CHAT_IDS=%s", ','.join(self.chat_ids)
            )
