import asyncio
import datetime
import logging
from queue import Empty
from typing import Union

import discord
from discord.ext import commands, tasks

from tgtg_scanner.errors import DiscordConfigurationError, MaskConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation
from tgtg_scanner.notifiers.base import Notifier

log = logging.getLogger("tgtg")

discord.VoiceClient.warn_nacl = False


class Discord(Notifier):
    """Notifier for Discord"""

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super().__init__(config, reservations, favorites)
        self.enabled = config.discord.enabled
        self.prefix = config.discord.prefix
        self.token = config.discord.token
        self.channel = config.discord.channel
        self.body = config.discord.body
        self.disable_commands = config.discord.disable_commands
        self.cron = config.discord.cron
        self.mute: Union[datetime.datetime, None] = None
        self.bot_id = None
        self.channel_id = None
        self.server_id = None

        if self.enabled:
            if self.token is None or self.channel == 0:
                raise DiscordConfigurationError()
            try:
                Item.check_mask(self.body)
            except MaskConfigurationError as exc:
                raise DiscordConfigurationError(exc.message) from exc
            self.bot = commands.Bot(command_prefix=self.prefix, intents=discord.Intents.all())
            try:
                # Setting event loop explicitly for python 3.9 compatibility
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                asyncio.run(self.bot.login(self.token))
                asyncio.run(self.bot.close())
            except MaskConfigurationError as exc:
                raise DiscordConfigurationError(exc.message) from exc

    async def _send(self, item: Union[Item, Reservation]) -> None:  # type: ignore[override]
        """Sends item information using Discord bot"""
        if self.mute and self.mute > datetime.datetime.now():
            return
        if self.mute:
            log.info("Reactivated Discord Notifications")
            self.mute = None
        if isinstance(item, Item):
            message = item.unmask(self.body)
            self.bot.dispatch("send_notification", message)

    @tasks.loop(seconds=1)
    async def _listen_for_items(self):
        """Method for polling notifications every second"""
        try:
            item = self.queue.get(block=False)
            if item is None:
                self.bot.dispatch("close")
                return
            log.debug("Sending %s Notification", self.name)
            await self._send(item)
        except Empty:
            pass
        except Exception as exc:
            log.error("Failed sending %s: %s", self.name, exc)

    def _run(self):
        self.config.set_locale()
        # Setting event loop explicitly for python 3.9 compatibility
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.bot = commands.Bot(command_prefix=self.prefix, intents=discord.Intents.all())
        # Events include methods for post-init, shutting down, and notification sending
        self._setup_events()
        if not self.disable_commands:
            # Commands are handled separately, in case commands are not enabled
            self._setup_commands()
        asyncio.run(self._start_bot())

    async def _start_bot(self):
        async with self.bot:
            await self.bot.start(self.token)

    def _setup_events(self):
        @self.bot.event
        async def on_ready():
            """Callback after successful login (only explicitly used in test_notifiers.py)"""
            self.bot_id = self.bot.user.id
            self.channel_id = self.channel
            self.server_id = self.bot.guilds[0].id if len(self.bot.guilds) > 0 else 0
            self._listen_for_items.start()

        @self.bot.event
        async def on_send_notification(message):
            """Callback for item notification"""
            channel = self.bot.get_channel(self.channel) or await self.bot.fetch_channel(self.channel)
            if channel:
                await channel.send(message)

        @self.bot.event
        async def on_close():
            """Logout from Discord (only explicitly used in test_notifiers.py)"""
            await self.bot.close()

    def _setup_commands(self):
        @self.bot.command(name="mute")
        async def _mute(ctx, *args):
            """Deactivates Discord Notifications for x days"""
            days = int(args[0]) if len(args) > 0 and args[0].isnumeric() else 1
            self.mute = datetime.datetime.now() + datetime.timedelta(days=days)
            log.info("Deactivated Discord Notifications for %s day(s)", days)
            log.info("Reactivation at %s", self.mute)
            await ctx.send(
                f"Deactivated Discord notifications for {days} days.\nReactivating at {self.mute} or use `{self.prefix}unmute`."
            )

        @self.bot.command(name="unmute")
        async def _unmute(ctx):
            """Reactivate Discord notifications"""
            self.mute = None
            log.info("Reactivated Discord notifications")
            await ctx.send("Reactivated Discord notifications")

        @self.bot.command(name="listfavorites")
        async def _list_favorites(ctx):
            """List favorites using display name"""
            favorites = self.favorites.get_favorites()
            if not favorites:
                await ctx.send("You currently don't have any favorites.")
            else:
                await ctx.send("\n".join([f"• {item.item_id} - {item.display_name}" for item in favorites]))

        @self.bot.command(name="listfavoriteids")
        async def _list_favorite_ids(ctx):
            """List favorites using id"""
            favorites = self.favorites.get_favorites()
            if not favorites:
                await ctx.send("You currently don't have any favorites.")
            else:
                await ctx.send(" ".join([item.item_id for item in favorites]))

        @self.bot.command(name="addfavorites")
        async def _add_favorites(ctx, *args):
            """Add favorite(s)"""
            item_ids = list(
                filter(
                    lambda x: x.isdigit() and int(x) != 0,
                    map(
                        str.strip,
                        [split_args for arg in args for split_args in arg.split(",")],
                    ),
                )
            )
            if not item_ids:
                await ctx.channel.send(
                    "Please supply item ids in one of the following ways: "
                    f"'{self.prefix}addfavorites 12345 23456 34567' or "
                    f"'{self.prefix}addfavorites 12345,23456,34567'"
                )
                return

            self.favorites.add_favorites(item_ids)
            await ctx.send(f"Added the following item ids to favorites: {' '.join(item_ids)}")
            log.debug('Added the following item ids to favorites: "%s"', item_ids)

        @self.bot.command(name="removefavorites")
        async def _remove_favorites(ctx, *args):
            """Remove favorite(s)"""
            item_ids = list(
                filter(
                    lambda x: x.isdigit() and int(x) != 0,
                    map(
                        str.strip,
                        [split_args for arg in args for split_args in arg.split(",")],
                    ),
                )
            )
            if not item_ids:
                await ctx.channel.send(
                    "Please supply item ids in one of the following ways: "
                    f"'{self.prefix}removefavorites 12345 23456 34567' or "
                    f"'{self.prefix}removefavorites 12345,23456,34567'"
                )
                return

            self.favorites.remove_favorite(item_ids)
            await ctx.send(f"Removed the following item ids from favorites: {' '.join(item_ids)}")
            log.debug('Removed the following item ids from favorites: "%s"', item_ids)

        @self.bot.command(name="gettoken")
        async def _get_token(ctx):
            """Display token used to login (without needing to manually check in config.ini)"""
            await ctx.send(f"Token in use: {self.token}")

        @self.bot.command(name="getinfo")
        async def _get_info(ctx):
            """Display basic info about connection"""
            bot_id = ctx.me.id
            bot_name = ctx.me.display_name
            bot_mention = ctx.me.mention
            joined_at = ctx.me.joined_at
            channel_id = ctx.channel.id
            channel_name = ctx.channel.name
            guild_id = ctx.guild.id
            guild_name = ctx.guild.name

            response = (
                f"Hi! I'm {bot_mention}, the TGTG Bot on this server. I joined at {joined_at}\n"
                f"```Bot (ID):     {bot_name} ({bot_id})\n"
                f"Channel (ID): {channel_name} ({channel_id})\n"
                f"Server (ID):  {guild_name} ({guild_id})```"
            )

            await ctx.send(response)

    def __repr__(self) -> str:
        return f"Discord: Channel ID {self.channel}"
