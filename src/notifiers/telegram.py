import datetime
import logging
import random
from time import sleep

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.bot import BotCommand
from telegram.error import BadRequest, NetworkError, TelegramError, TimedOut
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, Updater)
from telegram.utils.helpers import escape_markdown

from models import Config, Item, Reservations
from models.errors import MaskConfigurationError, TelegramConfigurationError
from models.reservations import Order, Reservation
from notifiers.base import Notifier

log = logging.getLogger('tgtg')


class Telegram(Notifier):
    """
    Notifier for Telegram.
    """
    MAX_RETRIES = 10

    def __init__(self, config: Config, reservations: Reservations):
        self.updater = None
        self.config = config
        self.enabled = config.telegram.get("enabled", False)
        self.token = config.telegram.get("token")
        self.body = config.telegram.get("body")
        self.image = config.telegram.get("image")
        self.chat_ids = config.telegram.get("chat_ids")
        self.timeout = config.telegram.get("timeout", 60)
        self.disable_commands = config.telegram.get(
            "disable_commands", False)
        self.cron = config.telegram.get("cron")
        self.mute = None
        self.retries = 0
        self.reservations = reservations
        if self.enabled and (not self.token or not self.body):
            raise TelegramConfigurationError()
        if self.enabled:
            if self.image not in [None, "", "${{item_logo_bytes}}",
                                  "${{item_cover_bytes}}"]:
                raise TelegramConfigurationError()
            try:
                Item.check_mask(self.body)
                self.updater = Updater(token=self.token,
                                       arbitrary_callback_data=True)
                self.updater.bot.get_me(timeout=self.timeout)
            except MaskConfigurationError as err:
                raise TelegramConfigurationError(err.message) from err
            except TelegramError as err:
                raise TelegramConfigurationError() from err
            if not self.chat_ids:
                self._get_chat_id()
            handlers = [
                CommandHandler("mute", self._mute),
                CommandHandler("unmute", self._unmute),
                CommandHandler("reserve", self._reserve_item_menu),
                CommandHandler("reservations", self._cancel_reservations_menu),
                CommandHandler("orders", self._cancel_orders_menu),
                CommandHandler("cancelall", self._cancel_all_orders),
                CallbackQueryHandler(self._callback_query_handler)]
            for handler in handlers:
                self.updater.dispatcher.add_handler(handler)
            self.updater.dispatcher.add_error_handler(self._error)
            self.updater.bot.set_my_commands([
                BotCommand('mute',
                           'Deactivate Telegram Notifications for '
                           '1 or x days'),
                BotCommand('unmute', 'Reactivate Telegram Notifications'),
                BotCommand('reserve', 'Reserve the next available Magic Bag'),
                BotCommand('reservations', 'List and cancel Reservations'),
                BotCommand('orders', 'List and cancel active Orders'),
                BotCommand('cancelall', 'Cancels all active orders')
            ])
            if not self.disable_commands:
                self.updater.start_polling()

    def _unmask(self, text: str, item: Item) -> str:
        if text in ["${{item_logo_bytes}}", "${{item_cover_bytes}}"]:
            matches = item._get_variables(text)
            return getattr(item, matches[0].group(1))
        for match in item._get_variables(text):
            if hasattr(item, match.group(1)):
                val = str(getattr(item, match.group(1)))
                val = escape_markdown(val, version=2)
                text = text.replace(match.group(0), val)
        return text

    def _send(self, item: Item) -> None:
        """Send item information as Telegram message"""
        if self.mute and self.mute > datetime.datetime.now():
            return
        if self.mute:
            log.info("Reactivated Telegram Notifications")
            self.mute = None
        message = self._unmask(self.body, item)
        image = None
        if self.image:
            image = self._unmask(self.image, item)
        self._send_message(message, image)

    def _send_reservation(self, reservation: Reservation) -> None:
        message = escape_markdown(
            f"{reservation.display_name} is reserved for 5 minutes",
            version=2)
        self._send_message(message)

    def _send_message(self, message: str, image: bytes = None) -> None:
        log.debug("%s message: %s", self.name, message)
        fmt = ParseMode.MARKDOWN_V2
        for chat_id in self.chat_ids:
            try:
                if image:
                    self.updater.bot.send_photo(
                        chat_id=chat_id,
                        photo=image,
                        caption=message,
                        parse_mode=fmt,
                        timeout=self.timeout)
                else:
                    self.updater.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=fmt,
                        timeout=self.timeout,
                        disable_web_page_preview=True)
                self.retries = 0
            except BadRequest as err:
                err_message = err.message
                if err_message.startswith("Can't parse entities:"):
                    err_message += ". For details see https://github.com/"
                    err_message += "Der-Henning/tgtg/wiki/Configuration"
                    err_message += "#note-on-markdown-v2"
                log.error('Telegram Error: %s', err_message)
            except (NetworkError, TimedOut) as err:
                log.warning('Telegram Error: %s', err)
                self.retries += 1
                if self.retries > Telegram.MAX_RETRIES:
                    raise err
                self.updater.stop()
                self.updater.start_polling()
                self._send_message(message)
            except TelegramError as err:
                log.error('Telegram Error: %s', err)

    def _mute(self, update: Update, context: CallbackContext) -> None:
        """Deactivates Telegram Notifications for x days"""
        days = int(context.args[0]) if context.args and \
            context.args[0].isnumeric() else 1
        self.mute = datetime.datetime.now() + datetime.timedelta(days=days)
        log.info('Deactivated Telegram Notifications for %s days', days)
        log.info('Reactivation at %s', self.mute)
        update.message.reply_text(
            f"Deactivated Telegram Notifications for {days} days.\n"
            f"Reactivating at {self.mute} or use /unmute.")

    def _unmute(self, update: Update, context: CallbackContext) -> None:
        """Reactivate Telegram Notifications"""
        del context
        self.mute = None
        log.info("Reactivated Telegram Notifications")
        update.message.reply_text("Reactivated Telegram Notifications")

    def _reserve_item_menu(self,
                           update: Update,
                           context: CallbackContext) -> None:
        del context
        favorites = self.reservations.get_favorites()
        buttons = [[
            InlineKeyboardButton(
                f"{item.display_name}: {item.items_available}",
                callback_data=item)
        ] for item in favorites]
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(
            "Select a Bag to reserve",
            reply_markup=reply_markup)

    def _cancel_reservations_menu(self,
                                  update: Update,
                                  context: CallbackContext) -> None:
        del context
        buttons = [[
            InlineKeyboardButton(
                reservation.display_name,
                callback_data=reservation)
        ] for reservation in self.reservations.reservation_query]
        if len(buttons) == 0:
            update.message.reply_text("No active Reservations")
            return
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(
            "Active Reservations. Select to cancel.",
            reply_markup=reply_markup)

    def _cancel_orders_menu(self,
                            update: Update,
                            context: CallbackContext) -> None:
        del context
        self.reservations.update_active_orders()
        buttons = [[
            InlineKeyboardButton(
                order.display_name,
                callback_data=order)
        ] for order in self.reservations.active_orders]
        if len(buttons) == 0:
            update.message.reply_text("No active Orders")
            return
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text(
            "Active Orders. Select to cancel.",
            reply_markup=reply_markup)

    def _cancel_all_orders(self,
                           update: Update,
                           context: CallbackContext) -> None:
        del context
        self.reservations.cancel_all_orders()
        update.message.reply_text("Cancelled all active Orders")
        log.debug("Cancelled all active Orders")

    def _callback_query_handler(self,
                                update: Update,
                                context: CallbackContext) -> None:
        del context
        data = update.callback_query.data
        if isinstance(data, Item):
            self.reservations.reserve(
                data.item_id,
                data.display_name)
            update.callback_query.answer(
                f"Added {data.display_name} to reservation queue")
            log.debug('Added "%s" to reservation queue', data.display_name)
        if isinstance(data, Reservation):
            self.reservations.reservation_query.remove(data)
            update.callback_query.answer(
                f"Removed {data.display_name} form reservation queue")
            log.debug('Removed "%s" from reservation queue', data.display_name)
        if isinstance(data, Order):
            self.reservations.cancel_order(data)
            update.callback_query.answer(
                f"Canceled Order for {data.display_name}")
            log.debug('Canceled order for "%s"', data.display_name)

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
                            update.message.chat_id)
                        self.chat_ids = [str(update.message.chat_id)]
            sleep(1)
        if self.config.set("TELEGRAM", "chat_ids", ','.join(self.chat_ids)):
            log.warning("Saved chat id in your config file")
        else:
            log.warning(
                "For persistence please set TELEGRAM_CHAT_IDS=%s",
                ','.join(self.chat_ids))

    def stop(self) -> None:
        if self.updater is not None:
            self.updater.stop()

    def __repr__(self) -> str:
        return f"Telegram: {self.chat_ids}"
