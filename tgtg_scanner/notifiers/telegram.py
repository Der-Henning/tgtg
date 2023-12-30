import asyncio
import datetime
import logging
import random
import warnings
from queue import Empty
from time import sleep
from typing import Union

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, NetworkError, TelegramError, TimedOut
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown
from telegram.warnings import PTBUserWarning

from tgtg_scanner.errors import MaskConfigurationError, TelegramConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.models.favorites import AddFavoriteRequest, RemoveFavoriteRequest
from tgtg_scanner.models.reservations import Order, Reservation
from tgtg_scanner.notifiers.base import Notifier

log = logging.getLogger("tgtg")


class Telegram(Notifier):
    """Notifier for Telegram"""

    MAX_RETRIES = 10

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super().__init__(config, reservations, favorites)
        self.application: Application = None
        self.config = config
        self.enabled = config.telegram.enabled
        self.token = config.telegram.token
        self.body = config.telegram.body
        self.image = config.telegram.image
        self.chat_ids = config.telegram.chat_ids
        self.timeout = config.telegram.timeout
        self.disable_commands = config.telegram.disable_commands
        self.cron = config.telegram.cron
        self.mute: Union[datetime.datetime, None] = None
        self.retries = 0
        if self.enabled:
            if not self.token or not self.body:
                raise TelegramConfigurationError()
            if self.image not in [
                None,
                "",
                "${{item_logo_bytes}}",
                "${{item_cover_bytes}}",
            ]:
                raise TelegramConfigurationError()
            try:
                Item.check_mask(self.body)
                warnings.filterwarnings("ignore", category=PTBUserWarning, module="telegram")
                self.application = ApplicationBuilder().token(self.token).arbitrary_callback_data(True).build()
                self.application.add_error_handler(self._error)
            except MaskConfigurationError as err:
                raise TelegramConfigurationError(err.message) from err
            except TelegramError as err:
                raise TelegramConfigurationError(err.message) from err

    @property
    def _handlers(self):
        return [
            CommandHandler("mute", self._mute),
            CommandHandler("unmute", self._unmute),
            CommandHandler("reserve", self._reserve_item_menu),
            CommandHandler("reservations", self._cancel_reservations_menu),
            CommandHandler("orders", self._cancel_orders_menu),
            CommandHandler("cancelall", self._cancel_all_orders),
            CommandHandler("listfavorites", self._list_favorites),
            CommandHandler("listfavoriteids", self._list_favorite_ids),
            CommandHandler("addfavorites", self._add_favorites),
            CommandHandler("removefavorites", self._remove_favorites),
            MessageHandler(
                filters.Regex(r"^https:\/\/share\.toogoodtogo\.com\/item\/(\d+)\/?"),
                self._url_handler,
            ),
            CallbackQueryHandler(self._callback_query_handler),
        ]

    async def _start_polling(self):
        log.debug("Telegram: Starting polling")
        for handler in self._handlers:
            self.application.add_handler(handler)
        await self.application.initialize()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES, timeout=self.timeout, poll_interval=0.1)
        await self.application.bot.set_my_commands(
            [
                BotCommand("mute", "Deactivate Telegram Notifications for " "1 or x days"),
                BotCommand("unmute", "Reactivate Telegram Notifications"),
                BotCommand("reserve", "Reserve the next available Magic Bag"),
                BotCommand("reservations", "List and cancel Reservations"),
                BotCommand("orders", "List and cancel active Orders"),
                BotCommand("cancelall", "Cancels all active orders"),
                BotCommand("listfavorites", "List all favorites"),
                BotCommand("listfavoriteids", "List all item ids from favorites"),
                BotCommand("addfavorites", "Add item ids to favorites"),
                BotCommand("removefavorites", "Remove Item ids from favorites"),
            ]
        )
        await self.application.start()

    async def _stop_polling(self):
        log.debug("Telegram: stopping polling")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()

    def _run(self) -> None:
        event_loop = asyncio.new_event_loop()
        if not self.chat_ids:
            event_loop.run_until_complete(self._get_chat_ids())
        if not self.disable_commands:
            event_loop.run_until_complete(self._start_polling())
        while True:
            event_loop.run_until_complete(asyncio.sleep(0.1))
            try:
                item = self.queue.get(block=False)
                if item is None:
                    break
                log.debug("Sending %s Notification", self.name)
                event_loop.run_until_complete(self._send(item))
            except Empty:
                pass
            except Exception as exc:
                log.error("Failed sending %s: %s", self.name, exc)
        if not self.disable_commands:
            event_loop.run_until_complete(self._stop_polling())
        event_loop.close()

    def _unmask(self, text: str, item: Item) -> str:
        for match in item._get_variables(text):
            if hasattr(item, match.group(1)):
                val = str(getattr(item, match.group(1)))
                val = escape_markdown(val, version=2)
                text = text.replace(match.group(0), val)
        return text

    def _unmask_image(self, text: str, item: Item) -> Union[bytes, None]:
        if text in ["${{item_logo_bytes}}", "${{item_cover_bytes}}"]:
            matches = item._get_variables(text)
            return bytes(getattr(item, matches[0].group(1)))
        return None

    async def _send(self, item: Union[Item, Reservation]) -> None:  # type: ignore[override]
        """Send item information as Telegram message"""
        if self.mute and self.mute > datetime.datetime.now():
            return
        if self.mute:
            log.info("Reactivated Telegram Notifications")
            self.mute = None
        image = None
        if isinstance(item, Item):
            message = self._unmask(self.body, item)
            if self.image:
                image = self._unmask_image(self.image, item)
        elif isinstance(item, Reservation):
            message = escape_markdown(f"{item.display_name} is reserved for 5 minutes", version=2)
        await self._send_message(message, image)

    async def _send_message(self, message: str, image: Union[bytes, None] = None) -> None:
        log.debug("%s message: %s", self.name, message)
        fmt = ParseMode.MARKDOWN_V2
        for chat_id in self.chat_ids:
            try:
                if image:
                    await self.application.bot.send_photo(chat_id=chat_id, photo=image, caption=message, parse_mode=fmt)
                else:
                    await self.application.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=fmt,
                        disable_web_page_preview=True,
                    )
                self.retries = 0
            except BadRequest as err:
                err_message = err.message
                if err_message.startswith("Can't parse entities:"):
                    err_message += ". For details see https://github.com/"
                    err_message += "Der-Henning/tgtg/wiki/Configuration"
                    err_message += "#note-on-markdown-v2"
                log.error("Telegram Error: %s", err_message)
            except (NetworkError, TimedOut) as err:
                log.warning("Telegram Error: %s", err)
                self.retries += 1
                if self.retries > Telegram.MAX_RETRIES:
                    raise err
                await self._send_message(message)
            except TelegramError as err:
                log.error("Telegram Error: %s", err)

    async def _mute(self, update: Update, context: CallbackContext) -> None:
        """Deactivates Telegram Notifications for x days"""
        days = int(context.args[0]) if context.args and context.args[0].isnumeric() else 1
        self.mute = datetime.datetime.now() + datetime.timedelta(days=days)
        log.info("Deactivated Telegram Notifications for %s days", days)
        log.info("Reactivation at %s", self.mute)
        await update.message.reply_text(
            f"Deactivated Telegram Notifications for {days} days.\n" f"Reactivating at {self.mute} or use /unmute."
        )

    async def _unmute(self, update: Update, _) -> None:
        """Reactivate Telegram Notifications"""
        self.mute = None
        log.info("Reactivated Telegram Notifications")
        await update.message.reply_text("Reactivated Telegram Notifications")

    async def _reserve_item_menu(self, update: Update, _) -> None:
        favorites = self.favorites.get_favorites()
        buttons = [
            [InlineKeyboardButton(f"{item.display_name}: {item.items_available}", callback_data=item)] for item in favorites
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Select a Bag to reserve", reply_markup=reply_markup)

    async def _cancel_reservations_menu(self, update: Update, _) -> None:
        buttons = [
            [InlineKeyboardButton(reservation.display_name, callback_data=reservation)]
            for reservation in self.reservations.reservation_query
        ]
        if len(buttons) == 0:
            await update.message.reply_text("No active Reservations")
            return
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Active Reservations. Select to cancel.", reply_markup=reply_markup)

    async def _cancel_orders_menu(self, update: Update, _) -> None:
        self.reservations.update_active_orders()
        buttons = [
            [InlineKeyboardButton(order.display_name, callback_data=order)] for order in self.reservations.active_orders.values()
        ]
        if len(buttons) == 0:
            await update.message.reply_text("No active Orders")
            return
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Active Orders. Select to cancel.", reply_markup=reply_markup)

    async def _cancel_all_orders(self, update: Update, _) -> None:
        self.reservations.cancel_all_orders()
        await update.message.reply_text("Cancelled all active Orders")
        log.debug("Cancelled all active Orders")

    async def _list_favorites(self, update: Update, _) -> None:
        favorites = self.favorites.get_favorites()
        if not favorites:
            await update.message.reply_text("You currently don't have any favorites.")
        else:
            await update.message.reply_text("\n".join([f"• {item.item_id} - {item.display_name}" for item in favorites]))

    async def _list_favorite_ids(self, update: Update, _) -> None:
        favorites = self.favorites.get_favorites()
        if not favorites:
            await update.message.reply_text("You currently don't have any favorites.")
        else:
            await update.message.reply_text(" ".join([item.item_id for item in favorites]))

    async def _add_favorites(self, update: Update, context: CallbackContext) -> None:
        if not context.args:
            await update.message.reply_text(
                "Please supply item ids in one of the following ways: "
                + "'/addfavorites 12345 23456 34567' or "
                + "'/addfavorites 12345,23456,34567'"
            )
            return

        item_ids = list(
            filter(
                bool,
                map(
                    str.strip,
                    [split_args for arg in context.args for split_args in arg.split(",")],
                ),
            )
        )
        self.favorites.add_favorites(item_ids)
        await update.message.reply_text(f"Added the following item ids to favorites: {' '.join(item_ids)}")
        log.debug('Added the following item ids to favorites: "%s"', item_ids)

    async def _remove_favorites(self, update: Update, context: CallbackContext) -> None:
        if not context.args:
            await update.message.reply_text(
                "Please supply item ids in one of the following ways: "
                + "'/removefavorites 12345 23456 34567' or "
                + "'/removefavorites 12345,23456,34567'"
            )
            return

        item_ids = list(
            filter(
                bool,
                map(
                    str.strip,
                    [split_args for arg in context.args for split_args in arg.split(",")],
                ),
            )
        )
        self.favorites.remove_favorite(item_ids)
        await update.message.reply_text("Removed the following item ids from favorites: " + f"{' '.join(item_ids)}")
        log.debug("Removed the following item ids from favorites: " + '"%s"', item_ids)

    async def _url_handler(self, update: Update, context: CallbackContext) -> None:
        item_id = context.matches[0].group(1)
        item_favorite = self.favorites.is_item_favorite(item_id)
        item = self.favorites.get_item_by_id(item_id)
        if item.item_id is None:
            await update.message.reply_text("There is no Item with this link")
            return

        if item_favorite:
            await update.message.reply_text(
                f"{item.display_name} is in your favorites. " + "Do you want to remove it?",
                reply_markup=(
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Yes",
                                    callback_data=RemoveFavoriteRequest(item_id, item.display_name, True),
                                ),
                                InlineKeyboardButton(
                                    "No",
                                    callback_data=RemoveFavoriteRequest(item_id, item.display_name, False),
                                ),
                            ]
                        ]
                    )
                ),
            )
        else:
            await update.message.reply_text(
                f"{item.display_name} is not in your favorites. " + "Do you want to add it?",
                reply_markup=(
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Yes",
                                    callback_data=AddFavoriteRequest(item_id, item.display_name, True),
                                ),
                                InlineKeyboardButton(
                                    "No",
                                    callback_data=AddFavoriteRequest(item_id, item.display_name, False),
                                ),
                            ]
                        ]
                    )
                ),
            )

    async def _callback_query_handler(self, update: Update, _) -> None:
        data = update.callback_query.data
        if isinstance(data, Item):
            self.reservations.reserve(data.item_id, data.display_name)
            await update.callback_query.answer(f"Added {data.display_name} to reservation queue")
            log.debug('Added "%s" to reservation queue', data.display_name)
        if isinstance(data, Reservation):
            self.reservations.reservation_query.remove(data)
            await update.callback_query.answer(f"Removed {data.display_name} form reservation queue")
            log.debug('Removed "%s" from reservation queue', data.display_name)
        if isinstance(data, Order):
            self.reservations.cancel_order(data.id)
            await update.callback_query.answer(f"Canceled Order for {data.display_name}")
            log.debug('Canceled order for "%s"', data.display_name)
        if isinstance(data, AddFavoriteRequest):
            if data.proceed:
                self.favorites.add_favorites([data.item_id])
                await update.callback_query.edit_message_text(f"Added {data.item_display_name} to favorites")
                log.debug('Added "%s" to favorites', data.item_display_name)
                log.debug('Removed "%s" from favorites', data.item_display_name)
            else:
                await update.callback_query.delete_message()
        if isinstance(data, RemoveFavoriteRequest):
            if data.proceed:
                self.favorites.remove_favorite([data.item_id])
                await update.callback_query.edit_message_text(f"Removed {data.item_display_name} from favorites")
                log.debug('Removed "%s" from favorites', data.item_display_name)
            else:
                await update.callback_query.delete_message()

    async def _error(self, update: Update, context: CallbackContext) -> None:
        """Log Errors caused by Updates."""
        log.debug('Update "%s" caused error "%s"', update, context.error)

    async def _get_chat_ids(self) -> None:
        """Initializes an interaction with the user
        to obtain the telegram chat id. \n
        On using the config.ini configuration the
        chat id will be stored in the config.ini.
        """
        log.warning("You enabled the Telegram notifications " "without providing a chat id!")
        code = random.randint(1111, 9999)
        log.warning("Send %s to the bot in your desired chat.", code)
        log.warning("Waiting for code ...")
        while not self.chat_ids:
            updates = await self.application.bot.get_updates(timeout=self.timeout)
            for update in reversed(updates):
                if update.message and update.message.text:
                    if update.message.text.isdecimal() and int(update.message.text) == code:
                        log.warning(
                            "Received code from %s %s on chat id %s",
                            update.message.from_user.first_name,
                            update.message.from_user.last_name,
                            update.message.chat_id,
                        )
                        self.chat_ids = [str(update.message.chat_id)]
            sleep(1)
        if self.config.set("TELEGRAM", "chat_ids", ",".join(self.chat_ids)):
            log.warning("Saved chat id in your config file")
        else:
            log.warning(
                "For persistence please set TELEGRAM_CHAT_IDS=%s",
                ",".join(self.chat_ids),
            )

    def __repr__(self) -> str:
        return f"Telegram: {self.chat_ids}"
