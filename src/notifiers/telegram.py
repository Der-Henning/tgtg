import datetime
import logging
import random
from time import sleep

from telegram import ParseMode, Update
from telegram.bot import BotCommand
from telegram.error import BadRequest, NetworkError, TelegramError, TimedOut
from telegram.ext import CallbackContext, CommandHandler, Updater

from models import Config, Item, Order
from models.errors import MaskConfigurationError, TelegramConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class Telegram(Notifier):
    """
    Notifier for Telegram.
    """
    MAX_RETRIES = 10

    def __init__(self, config: Config):
        self.updater = None
        self.config = config
        self.enabled = config.telegram.get("enabled", False)
        self.token = config.telegram.get("token")
        self.body = config.telegram.get("body")
        self.chat_ids = config.telegram.get("chat_ids")
        self.timeout = config.telegram.get("timeout", 60)
        self.cron = config.telegram.get("cron")
        self.mute = None
        self.retries = 0
        if self.enabled and (not self.token or not self.body):
            raise TelegramConfigurationError()
        if self.enabled:
            try:
                Item.check_mask(self.body)
                self.updater = Updater(token=self.token)
                self.updater.bot.get_me(timeout=self.timeout)
            except MaskConfigurationError as err:
                raise TelegramConfigurationError(err.message) from err
            except TelegramError as err:
                raise TelegramConfigurationError() from err
            if not self.chat_ids:
                self._get_chat_id()
            self.updater.dispatcher.add_handler(
                CommandHandler("help", self._help))
            self.updater.dispatcher.add_handler(
                CommandHandler("mute", self._mute))
            self.updater.dispatcher.add_handler(
                CommandHandler("unmute", self._unmute))
            self.updater.dispatcher.add_error_handler(self._error)
            self.updater.bot.set_my_commands([
                BotCommand('help', 'Display available Commands'),
                BotCommand(
                    'mute',
                    'Deactivate Telegram Notifications for 1 or x days'),
                BotCommand('unmute', 'Reactivate Telegram Notifications')
            ])
            self.updater.start_polling()
        self.send_order_notification = config.notifiers.get("order_ready_notification", False)
        self.order_body = config.notifiers.get("order_body")

    def _send(self, item: Item) -> None:
        """Send item information as Telegram message"""
        if self.mute and self.mute > datetime.datetime.now():
            return
        if self.mute:
            log.info("Reactivated Telegram Notifications")
            self.mute = None
        fmt = ParseMode.MARKDOWN
        message = item.unmask(self.body)
        log.debug(message)
        for chat_id in self.chat_ids:
            try:
                self.updater.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=fmt,
                    timeout=self.timeout,
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
                
    def _send_order(self, order: Order) -> None:
        log.info("SENDING")
        if self.send_order_notification:
            fmt = ParseMode.MARKDOWN
            message = order.unmask(self.order_body)
            log.debug(message)
            for chat_id in self.chat_ids:
                try:
                    self.updater.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=fmt,
                        timeout=self.timeout,
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
                    self.send_order(order)
                except TelegramError as err:
                    log.error('Telegram Error: %s', err)
        
    def _help(self, update: Update, context: CallbackContext) -> None:
        """Send message containing available bot commands"""
        del context
        update.message.reply_text('Deactivate Telegram Notifications for '
                                  'x days using\n/mute x\nReactivate with '
                                  '/unmute')

    def _mute(self, update: Update, context: CallbackContext) -> None:
        """Deactivates Telegram Notifications for x days"""
        days = int(context.args[0]) if context.args and \
            context.args[0].isnumeric() else 1
        self.mute = datetime.datetime.now() + datetime.timedelta(days=days)
        log.info('Deactivated Telegram Notifications for %s days', days)
        log.info('Reactivation at %s', self.mute)
        update.message.reply_text(f"Deactivated Telegram Notifications "
                                  f"for {days} days.\nReactivating at "
                                  f"{self.mute} or use /unmute.")

    def _unmute(self, update: Update, context: CallbackContext) -> None:
        """Reactivate Telegram Notifications"""
        del context
        self.mute = None
        log.info("Reactivated Telegram Notifications")
        update.message.reply_text("Reactivated Telegram Notifications")

    def _error(self, update: Update, context: CallbackContext) -> None:
        """Log Errors caused by Updates."""
        log.debug('Update "%s" caused error "%s"', update, context.error)

    def _get_chat_id(self) -> None:
        """Initializes an interaction with the user
        to obtain the telegram chat id. \n
        On using the config.ini configuration the
        chat id will be stored in the config.ini.
        """
        log.warning("You enabled the Telegram notifications "
                    "without providing a chat id!")
        code = random.randint(1111, 9999)
        log.warning("Send %s to the bot in your desired chat.", code)
        log.warning("Waiting for code ...")
        while not self.chat_ids:
            updates = self.updater.bot.get_updates(timeout=self.timeout)
            for update in reversed(updates):
                if update.message and update.message.text:
                    if update.message.text.isdecimal() and \
                            int(update.message.text) == code:
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
                "For persistence please set TELEGRAM_CHAT_IDS=%s", ','.join(
                    self.chat_ids)
            )

    def stop(self) -> None:
        if self.updater is not None:
            self.updater.stop()

    def __repr__(self) -> str:
        return f"Telegram: {self.chat_ids}"
