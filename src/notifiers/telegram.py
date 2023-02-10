import asyncio
import datetime
import logging
import random

from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, NetworkError, TelegramError, TimedOut
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from models import Config, Item
from models.errors import MaskConfigurationError, TelegramConfigurationError
from notifiers import Notifier

log = logging.getLogger('tgtg')


class Telegram(Notifier):
    """
    Notifier for Telegram.
    """
    MAX_RETRIES = 10

    async def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        await instance.__init__(*args, **kwargs)
        return instance

    async def __init__(self, config: Config):
        self.application: Application = None
        self.config = config
        self.enabled = config.telegram.get("enabled", False)
        self.token = config.telegram.get("token")
        self.body = config.telegram.get("body")
        self.chat_ids = config.telegram.get("chat_ids")
        self.timeout = config.telegram.get("timeout", 60)
        self.cron = config.telegram.get("cron")
        self.mute = None
        self.retries = 0
        self.code = 0
        if self.enabled and (not self.token or not self.body):
            raise TelegramConfigurationError()
        if self.enabled:
            try:
                Item.check_mask(self.body)
                self.application = Application.builder() \
                    .token(self.token).build()
                await self.application.bot.get_me()
            except MaskConfigurationError as err:
                raise TelegramConfigurationError(err.message) from err
            except TelegramError as err:
                raise TelegramConfigurationError() from err
            self.application.add_handler(
                CommandHandler("help", self._help))
            self.application.add_handler(
                CommandHandler("mute", self._mute))
            self.application.add_handler(
                CommandHandler("unmute", self._unmute))
            self.application.add_error_handler(self._error)
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            await self.application.updater.bot.set_my_commands([
                BotCommand('help', 'Display available Commands'),
                BotCommand(
                    'mute',
                    'Deactivate Telegram Notifications for 1 or x days'),
                BotCommand('unmute', 'Reactivate Telegram Notifications')
            ])
            if not self.chat_ids:
                await self._get_chat_id()

    async def send(self, item: Item) -> None:
        """Send item information as Telegram message"""
        if self.enabled and self.cron.is_now:
            if self.mute and self.mute > datetime.datetime.now():
                return
            if self.mute:
                log.info("Reactivated Telegram Notifications")
                self.mute = None
            log.debug("Sending Telegram Notification")
            message = item.unmask(self.body)
            log.debug(message)
            for chat_id in self.chat_ids:
                try:
                    await self.application.updater.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)
                    self.retries = 0
                except BadRequest as err:
                    log.error('Telegram Error: %s', err)
                except (NetworkError, TimedOut) as err:
                    log.warning('Telegram Error: %s', err)
                    self.retries += 1
                    if self.retries > Telegram.MAX_RETRIES:
                        raise err
                    await self.application.updater.stop()
                    await self.application.stop()
                    await self.application.updater.start_polling()
                    await self.application.start()
                    await self.send(item)
                except TelegramError as err:
                    log.error('Telegram Error: %s', err)

    async def _help(self, update: Update,
                    context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send message containing available bot commands"""
        del context
        await update.effective_message.reply_text(
            'Deactivate Telegram Notifications for x days '
            'using\n/mute x\nReactivate with /unmute')

    async def _mute(self, update: Update,
                    context: ContextTypes.DEFAULT_TYPE) -> None:
        """Deactivates Telegram Notifications for x days"""
        days = int(context.args[0]) if context.args and \
            context.args[0].isnumeric() else 1
        self.mute = datetime.datetime.now() + datetime.timedelta(days=days)
        log.info('Deactivated Telegram Notifications for %s days', days)
        log.info('Reactivation at %s', self.mute)
        await update.effective_message.reply_text(
            f"Deactivated Telegram Notifications for {days} days."
            f"\nReactivating at {self.mute} or use /unmute.")

    async def _unmute(self, update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> None:
        """Reactivate Telegram Notifications"""
        del context
        self.mute = None
        log.info("Reactivated Telegram Notifications")
        await update.effective_message.reply_text(
            "Reactivated Telegram Notifications")

    async def _error(self, update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log Errors caused by Updates."""
        log.warning('Update "%s" caused error "%s"', update, context.error)

    async def _set_chat_id(self, update: Update,
                           context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        log.debug("Received: %s", update.message.text)
        if update.message.text.isdecimal() and \
                int(update.message.text) == self.code:
            log.warning(
                "Received code from %s %s on chat id %s",
                update.message.from_user.first_name,
                update.message.from_user.last_name,
                update.message.chat_id
            )
            self.chat_ids = [str(update.message.chat_id)]

    async def _get_chat_id(self) -> None:
        """Initializes an interaction with the user
        to obtain the telegram chat id. \n
        On using the config.ini configuration the
        chat id will be stored in the config.ini.
        """
        log.warning("You enabled the Telegram notifications "
                    "without providing a chat id!")
        self.code = random.randint(1111, 9999)
        log.warning("Send %s to the bot in your desired chat.", self.code)
        log.warning("Waiting for code ...")
        code_handler = MessageHandler(filters.TEXT & ~filters.COMMAND,
                                      self._set_chat_id)
        self.application.add_handler(code_handler)
        while not self.chat_ids:
            await asyncio.sleep(1)
        self.application.remove_handler(code_handler)
        if self.config.set("TELEGRAM", "chat_ids", ','.join(self.chat_ids)):
            log.warning("Saved chat id in your config file")
        else:
            log.warning(
                "For persistence please set TELEGRAM_CHAT_IDS=%s", ','.join(
                    self.chat_ids)
            )

    async def stop(self):
        if self.application is not None:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

    def __repr__(self) -> str:
        return f"Telegram: {self.chat_ids}"
