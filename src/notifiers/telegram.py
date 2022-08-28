import logging
from time import sleep
import random
import datetime
from telegram import Update, ParseMode
from telegram.error import TelegramError, NetworkError, TimedOut, BadRequest
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.bot import BotCommand
from models import Item, Config
from models.errors import TelegramConfigurationError, MaskConfigurationError

log = logging.getLogger('tgtg')


class Telegram():
    """
    Notifier for Telegram.
    """
    MAX_RETRIES = 10

    def __init__(self, config: Config):
        self.updater = None
        self.config = config
        self.enabled = config.telegram["enabled"]
        self.token = config.telegram["token"]
        self.body = config.telegram["body"]
        self.chat_ids = config.telegram["chat_ids"]
        self.mute = None
        self.retries = 0
        if self.enabled and not self.token:
            raise TelegramConfigurationError("Missing Telegram token")
        if self.enabled:
            try:
                Item.check_mask(self.body)
                self.updater = Updater(token=self.token)
                self.updater.bot.get_me(timeout=60)
            except MaskConfigurationError as err:
                raise TelegramConfigurationError(err.message) from err
            except TelegramError as err:
                raise TelegramConfigurationError() from err
            if not self.chat_ids:
                self._get_chat_id()
            self.updater.dispatcher.add_handler(CommandHandler("help", self._help))
            self.updater.dispatcher.add_handler(CommandHandler("mute", self._mute))
            self.updater.dispatcher.add_handler(CommandHandler("unmute", self._unmute))
            self.updater.dispatcher.add_error_handler(self._error)
            self.updater.bot.set_my_commands([
                BotCommand('help', 'Display available Commands'),
                BotCommand('mute', 'Deactivate Telegram Notifications for 1 or x days'),
                BotCommand('unmute', 'Reactivate Telegram Notifications')
            ])
            self.updater.start_polling()

    def send(self, item: Item) -> None:
        """Send item information as Telegram message"""
        if self.enabled:
            if self.mute and self.mute > datetime.datetime.now():
                return
            if self.mute:
                log.info("Reactivated Telegram Notifications")
                self.mute = None
            log.debug("Sending Telegram Notification")
            fmt = ParseMode.MARKDOWN
            message = item.unmask(self.body)
            log.debug(message)
            for chat_id in self.chat_ids:
                try:
                    self.updater.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=fmt,
                        timeout=60,
                        disable_web_page_preview=True)
                    self.retries = 0
                except BadRequest as err:
                    log.error('Telegram Error: %s', err)
                except (NetworkError, TimedOut) as err:
                    log.warning('Telegram Error: %s', err)
                    self.retries += 1
                    if self.retries > Telegram.MAX_RETRIES:
                        raise err
                    self.updater.stop()
                    self.updater.start_polling()
                    self.send(item)
                except TelegramError as err:
                    log.error('Telegram Error: %s', err)

    def _help(self, update: Update, context: CallbackContext) -> None:
        """Send message containing available bot commands"""
        del context
        update.message.reply_text('Deactivate Telegram Notifications for x days using\n/mute x\nReactivate with /unmute')

    def _mute(self, update: Update, context: CallbackContext) -> None:
        """Deactivates Telegram Notifications for x days"""
        days = int(context.args[0]) if context.args and context.args[0].isnumeric() else 1
        self.mute = datetime.datetime.now() + datetime.timedelta(days=days)
        log.info('Deactivated Telegram Notifications for %s days', days)
        log.info('Reactivation at %s', self.mute)
        update.message.reply_text(f"Deactivated Telegram Notifications for {days} days.\nReactivating at {self.mute} or use /unmute.")

    def _unmute(self, update: Update, context: CallbackContext) -> None:
        """Reactivate Telegram Notifications"""
        del context
        self.mute = None
        log.info("Reactivated Telegram Notifications")
        update.message.reply_text("Reactivated Telegram Notifications")
    
    def _error(self, update: Update, context: CallbackContext) -> None:
        """Log Errors caused by Updates."""
        log.warning('Update "%s" caused error "%s"', update, context.error)

    def _get_chat_id(self) -> None:
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
                if update.message and update.message.text:
                    if update.message.text.isdecimal() and int(update.message.text) == code:
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
