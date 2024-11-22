from __future__ import annotations

import codecs
import configparser
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from os import environ
from pathlib import Path
from typing import IO, Any, Union

import humanize

from tgtg_scanner.errors import ConfigurationError
from tgtg_scanner.models.cron import Cron
from tgtg_scanner.tgtg.tgtg_client import BASE_URL

log = logging.getLogger("tgtg")

CONFIG_FILE_HEADER = """## TGTG Scanner Configuration
## --------------------------
## This is the configuration file for the TGTG Scanner.
## You can find more information about the configuration on the project page:
## https://github.com/Der-Henning/tgtg/wiki/Configuration

"""

DEPRECATION_NOTICE = "{} is deprecated and will be removed in a future release. Please use {} instead."


@dataclass
class BaseConfig(ABC):
    """Base configuration"""

    @abstractmethod
    def _read_ini(self, parser: configparser.ConfigParser):
        pass

    @abstractmethod
    def _read_env(self):
        pass

    @staticmethod
    def _decode(value: str) -> str:
        return codecs.escape_decode(bytes(value, "utf-8"))[0].decode("utf-8")  # type: ignore[attr-defined]

    def _ini_get(self, parser: configparser.ConfigParser, section: str, key: str, attr: str):
        value = parser.get(section, key, fallback=None)
        if value is not None:
            setattr(self, attr, self._decode(value))

    def _ini_get_boolean(self, parser: configparser.ConfigParser, section: str, key: str, attr: str):
        try:
            value = parser.getboolean(section, key, fallback=None)
        except ValueError as err:
            raise ConfigurationError(f"Invalid boolean value for {section}.{key} - {err}") from err
        if value is not None:
            setattr(self, attr, value)

    def _ini_get_int(self, parser: configparser.ConfigParser, section: str, key: str, attr: str):
        try:
            value = parser.getint(section, key, fallback=None)
        except ValueError as err:
            raise ConfigurationError(f"Invalid integer value for {section}.{key} - {err}") from err
        if value is not None:
            setattr(self, attr, value)

    def _ini_get_list(self, parser: configparser.ConfigParser, section: str, key: str, attr: str):
        value = parser.get(section, key, fallback=None)
        if value is not None:
            setattr(self, attr, [self._decode(val.strip()) for val in value.split(",")])

    def _ini_get_dict(self, parser: configparser.ConfigParser, section: str, key: str, attr: str):
        value = parser.get(section, key, fallback=None)
        if value is not None:
            try:
                setattr(self, attr, json.loads(value))
            except json.JSONDecodeError as err:
                raise ConfigurationError(f"Invalid JSON value for {section}.{key} - {err}") from err

    def _ini_get_cron(self, parser: configparser.ConfigParser, section: str, key: str, attr: str):
        value = parser.get(section, key, fallback=None)
        if value is not None:
            try:
                setattr(self, attr, Cron(value))
            except ValueError as err:
                raise ConfigurationError(f"Invalid cron value for {section}.{key} - {err}") from err

    def _env_get(self, key: str, attr: str):
        value = environ.get(key, None)
        if value is not None:
            setattr(self, attr, self._decode(value))

    def _env_get_boolean(self, key: str, attr: str):
        value = environ.get(key, None)
        if value is not None:
            setattr(self, attr, value.lower() in {"true", "1", "t", "y", "yes"})

    def _env_get_int(self, key: str, attr: str):
        value = environ.get(key, None)
        if value is not None:
            try:
                setattr(self, attr, int(value))
            except ValueError as err:
                raise ConfigurationError(f"Invalid integer value for {key} - {err}") from err

    def _env_get_list(self, key: str, attr: str):
        value = environ.get(key, None)
        if value is not None:
            setattr(self, attr, [self._decode(val.strip()) for val in value.split(",")])

    def _env_get_dict(self, key: str, attr: str):
        value = environ.get(key, None)
        if value is not None:
            try:
                setattr(self, attr, json.loads(value))
            except json.JSONDecodeError as err:
                raise ConfigurationError(f"Invalid JSON value for {key} - {err}") from err

    def _env_get_cron(self, key: str, attr: str):
        value = environ.get(key, None)
        if value is not None:
            try:
                setattr(self, attr, Cron(value))
            except ValueError as err:
                raise ConfigurationError(f"Invalid cron value for {key} - {err}") from err


@dataclass
class NotifierConfig(BaseConfig):
    """Base Notifier configuration"""

    enabled: bool = False
    cron: Cron = field(default_factory=Cron)


@dataclass
class AppriseConfig(NotifierConfig):
    """Apprise Notifier configuration"""

    url: Union[str, None] = None
    title: str = "New Magic Bags"
    body: str = "${{display_name}} - new amount: ${{items_available}} - ${{link}}"

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "APPRISE", "Enabled", "enabled")
        self._ini_get_cron(parser, "APPRISE", "Cron", "cron")
        self._ini_get(parser, "APPRISE", "URL", "url")
        self._ini_get(parser, "APPRISE", "Title", "title")
        self._ini_get(parser, "APPRISE", "Body", "body")

    def _read_env(self):
        self._env_get_boolean("APPRISE", "enabled")
        self._env_get_cron("APPRISE_CRON", "cron")
        self._env_get("APPRISE_URL", "url")
        self._env_get("APPRISE_TITLE", "title")
        self._env_get("APPRISE_BODY", "body")


@dataclass
class TelegramConfig(NotifierConfig):
    """Telegram Notifier configuration"""

    token: Union[str, None] = None
    chat_ids: list[str] = field(default_factory=list)
    disable_commands: bool = False
    only_reservations: bool = False
    timeout: int = 60
    body: str = (
        "*${{display_name}}*\n*Available*: ${{items_available}}\n*Price*: ${{price}} ${{currency}}\n*Pickup*: ${{pickupdate}}"
    )
    image: Union[str, None] = None

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "TELEGRAM", "Enabled", "enabled")
        self._ini_get_cron(parser, "TELEGRAM", "Cron", "cron")
        self._ini_get(parser, "TELEGRAM", "Token", "token")
        if parser.has_option("TELEGRAM", "chat_ids"):
            log.warning(DEPRECATION_NOTICE.format("[TELEGRAM] chat_ids", "ChatIDs"))
        self._ini_get_list(parser, "TELEGRAM", "chat_ids", "chat_ids")  # legacy support
        self._ini_get_list(parser, "TELEGRAM", "ChatIDs", "chat_ids")
        self._ini_get_boolean(parser, "TELEGRAM", "DisableCommands", "disable_commands")
        self._ini_get_boolean(parser, "TELEGRAM", "OnlyReservations", "only_reservations")
        self._ini_get_int(parser, "TELEGRAM", "Timeout", "timeout")
        self._ini_get(parser, "TELEGRAM", "Body", "body")
        self._ini_get(parser, "TELEGRAM", "Image", "image")

    def _read_env(self):
        self._env_get_boolean("TELEGRAM", "enabled")
        self._env_get_cron("TELEGRAM_CRON", "cron")
        self._env_get("TELEGRAM_TOKEN", "token")
        self._env_get_list("TELEGRAM_CHAT_IDS", "chat_ids")
        self._env_get_boolean("TELEGRAM_DISABLE_COMMANDS", "disable_commands")
        self._env_get_boolean("TELEGRAM_ONLY_RESERVATIONS", "only_reservations")
        self._env_get_int("TELEGRAM_TIMEOUT", "timeout")
        self._env_get("TELEGRAM_BODY", "body")
        self._env_get("TELEGRAM_IMAGE", "image")


@dataclass
class PushSaferConfig(NotifierConfig):
    """PushSafer Notifier configuration"""

    key: Union[str, None] = None
    device_id: Union[str, None] = None

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "PUSHSAFER", "Enabled", "enabled")
        self._ini_get_cron(parser, "PUSHSAFER", "Cron", "cron")
        self._ini_get(parser, "PUSHSAFER", "Key", "key")
        self._ini_get(parser, "PUSHSAFER", "DeviceID", "device_id")

    def _read_env(self):
        if environ.get("PUSH_SAFER", None):
            log.warning(DEPRECATION_NOTICE.format("PUSH_SAFER", "PUSHSAFER"))
        self._env_get_boolean("PUSH_SAFER", "enabled")
        self._env_get_boolean("PUSHSAFER", "enabled")
        if environ.get("PUSH_SAFER_CRON", None):
            log.warning(DEPRECATION_NOTICE.format("PUSH_SAFER_CRON", "PUSHSAFER_CRON"))
        self._env_get_cron("PUSH_SAFER_CRON", "cron")
        self._env_get_cron("PUSHSAFER_CRON", "cron")
        if environ.get("PUSH_SAFER_KEY", None):
            log.warning(DEPRECATION_NOTICE.format("PUSH_SAFER_KEY", "PUSHSAFER_KEY"))
        self._env_get("PUSH_SAFER_KEY", "key")
        self._env_get("PUSHSAFER_KEY", "key")
        if environ.get("PUSH_SAFER_DEVICE_ID", None):
            log.warning(DEPRECATION_NOTICE.format("PUSH_SAFER_DEVICE_ID", "PUSHSAFER_DEVICE_ID"))
        self._env_get("PUSH_SAFER_DEVICE_ID", "device_id")
        self._env_get("PUSHSAFER_DEVICE_ID", "device_id")


@dataclass
class ConsoleConfig(NotifierConfig):
    """Console Notifier configuration"""

    body: str = "${{display_name}} - new amount: ${{items_available}} - ${{link}}"

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "CONSOLE", "Enabled", "enabled")
        self._ini_get_cron(parser, "CONSOLE", "Cron", "cron")
        self._ini_get(parser, "CONSOLE", "Body", "body")

    def _read_env(self):
        self._env_get_boolean("CONSOLE", "enabled")
        self._env_get_cron("CONSOLE_CRON", "cron")
        self._env_get("CONSOLE_BODY", "body")


@dataclass
class SMTPConfig(NotifierConfig):
    """SMTP Notifier configuration"""

    host: Union[str, None] = None
    port: Union[int, None] = None
    username: Union[str, None] = None
    password: Union[str, None] = None
    use_tls: bool = False
    use_ssl: bool = False
    timeout: int = 60
    sender: Union[str, None] = None
    recipients: list[str] = field(default_factory=list)
    recipients_per_item: Union[str, None] = None
    subject: str = "New Magic Bags"
    body: str = "<b>${{display_name}}</b> </br>New Amount: ${{items_available}}"

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "SMTP", "Enabled", "enabled")
        self._ini_get_cron(parser, "SMTP", "Cron", "cron")
        self._ini_get(parser, "SMTP", "Host", "host")
        self._ini_get_int(parser, "SMTP", "Port", "port")
        self._ini_get(parser, "SMTP", "Username", "username")
        self._ini_get(parser, "SMTP", "Password", "password")
        self._ini_get_boolean(parser, "SMTP", "TLS", "use_tls")
        self._ini_get_boolean(parser, "SMTP", "SSL", "use_ssl")
        self._ini_get_int(parser, "SMTP", "Timeout", "timeout")
        self._ini_get(parser, "SMTP", "Sender", "sender")
        if parser.has_option("SMTP", "Recipient"):
            log.warning(DEPRECATION_NOTICE.format("[SMTP] Recipient", "Recipients"))
        self._ini_get_list(parser, "SMTP", "Recipient", "recipients")  # legacy support
        self._ini_get_list(parser, "SMTP", "Recipients", "recipients")
        self._ini_get(parser, "SMTP", "RecipientsPerItem", "recipients_per_item")
        self._ini_get(parser, "SMTP", "Subject", "subject")
        self._ini_get(parser, "SMTP", "Body", "body")

    def _read_env(self):
        self._env_get_boolean("SMTP", "enabled")
        self._env_get_cron("SMTP_CRON", "cron")
        self._env_get("SMTP_HOST", "host")
        self._env_get_int("SMTP_PORT", "port")
        self._env_get("SMTP_USERNAME", "username")
        self._env_get("SMTP_PASSWORD", "password")
        self._env_get_boolean("SMTP_TLS", "use_tls")
        self._env_get_boolean("SMTP_SSL", "use_ssl")
        self._env_get_int("SMTP_TIMEOUT", "timeout")
        self._env_get("SMTP_SENDER", "sender")
        if environ.get("SMTP_RECIPIENT", None):
            log.warning(DEPRECATION_NOTICE.format("SMTP_RECIPIENT", "SMTP_RECIPIENTS"))
        self._env_get_list("SMTP_RECIPIENT", "recipients")  # legacy support
        self._env_get_list("SMTP_RECIPIENTS", "recipients")
        self._env_get("SMTP_RECIPIENTS_PER_ITEM", "recipients_per_item")
        self._env_get("SMTP_SUBJECT", "subject")
        self._env_get("SMTP_BODY", "body")


@dataclass
class IFTTTConfig(NotifierConfig):
    """IFTTT Notifier configuration"""

    event: str = "tgtg_notification"
    key: Union[str, None] = None
    body: str = '{"value1": "${{display_name}}", "value2": ${{items_available}}, "value3": "${{link}}"}'
    timeout: int = 60

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "IFTTT", "Enabled", "enabled")
        self._ini_get_cron(parser, "IFTTT", "Cron", "cron")
        self._ini_get(parser, "IFTTT", "Event", "event")
        self._ini_get(parser, "IFTTT", "Key", "key")
        self._ini_get(parser, "IFTTT", "Body", "body")
        self._ini_get_int(parser, "IFTTT", "Timeout", "timeout")

    def _read_env(self):
        self._env_get_boolean("IFTTT", "enabled")
        self._env_get_cron("IFTTT_CRON", "cron")
        self._env_get("IFTTT_EVENT", "event")
        self._env_get("IFTTT_KEY", "key")
        self._env_get("IFTTT_BODY", "body")
        self._env_get_int("IFTTT_TIMEOUT", "timeout")


@dataclass
class NtfyConfig(NotifierConfig):
    """Ntfy Notifier configuration"""

    server: str = "https://ntfy.sh"
    topic: Union[str, None] = None
    title: str = "New Magic Bags"
    message: str = "${{display_name}} - New Amount: ${{items_available}} - ${{link}}"
    body: Union[str, None] = None
    priority: str = "default"
    tags: str = "shopping,tgtg"
    click: str = "${{link}}"
    username: Union[str, None] = None
    password: Union[str, None] = None
    token: Union[str, None] = None
    timeout: int = 60

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "NTFY", "Enabled", "enabled")
        self._ini_get_cron(parser, "NTFY", "Cron", "cron")
        self._ini_get(parser, "NTFY", "Server", "server")
        self._ini_get(parser, "NTFY", "Topic", "topic")
        self._ini_get(parser, "NTFY", "Title", "title")
        self._ini_get(parser, "NTFY", "Message", "message")
        self._ini_get(parser, "NTFY", "Body", "body")
        self._ini_get(parser, "NTFY", "Priority", "priority")
        self._ini_get(parser, "NTFY", "Tags", "tags")
        self._ini_get(parser, "NTFY", "Click", "click")
        self._ini_get(parser, "NTFY", "Username", "username")
        self._ini_get(parser, "NTFY", "Password", "password")
        self._ini_get(parser, "NTFY", "Token", "token")
        self._ini_get_int(parser, "NTFY", "Timeout", "timeout")

    def _read_env(self):
        self._env_get_boolean("NTFY", "enabled")
        self._env_get_cron("NTFY_CRON", "cron")
        self._env_get("NTFY_SERVER", "server")
        self._env_get("NTFY_TOPIC", "topic")
        self._env_get("NTFY_TITLE", "title")
        self._env_get("NTFY_MESSAGE", "message")
        self._env_get("NTFY_BODY", "body")
        self._env_get("NTFY_PRIORITY", "priority")
        self._env_get("NTFY_TAGS", "tags")
        self._env_get("NTFY_CLICK", "click")
        self._env_get("NTFY_USERNAME", "username")
        self._env_get("NTFY_PASSWORD", "password")
        self._env_get("NTFY_TOKEN", "token")
        self._env_get_int("NTFY_TIMEOUT", "timeout")


@dataclass
class WebhookConfig(NotifierConfig):
    """Webhook Notifier configuration"""

    url: Union[str, None] = None
    method: str = "POST"
    headers: dict[str, str | bytes] = field(default_factory=dict)
    body: str = ""
    type: str = "text/plain"
    timeout: int = 60
    username: Union[str, None] = None
    password: Union[str, None] = None

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "WEBHOOK", "Enabled", "enabled")
        self._ini_get_cron(parser, "WEBHOOK", "Cron", "cron")
        self._ini_get(parser, "WEBHOOK", "URL", "url")
        self._ini_get(parser, "WEBHOOK", "Method", "method")
        self._ini_get_dict(parser, "WEBHOOK", "Headers", "headers")
        self._ini_get(parser, "WEBHOOK", "Body", "body")
        self._ini_get(parser, "WEBHOOK", "Type", "type")
        self._ini_get(parser, "WEBHOOK", "Username", "username")
        self._ini_get(parser, "WEBHOOK", "Password", "password")
        self._ini_get_int(parser, "WEBHOOK", "Timeout", "timeout")

    def _read_env(self):
        self._env_get_boolean("WEBHOOK", "enabled")
        self._env_get_cron("WEBHOOK_CRON", "cron")
        self._env_get("WEBHOOK_URL", "url")
        self._env_get("WEBHOOK_METHOD", "method")
        self._env_get_dict("WEBHOOK_HEADERS", "headers")
        self._env_get("WEBHOOK_BODY", "body")
        self._env_get("WEBHOOK_TYPE", "type")
        self._env_get("WEBHOOK_USERNAME", "username")
        self._env_get("WEBHOOK_PASSWORD", "password")
        self._env_get_int("WEBHOOK_TIMEOUT", "timeout")


@dataclass
class ScriptConfig(NotifierConfig):
    """Script Notifier configuration"""

    command: Union[str, None] = None

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "SCRIPT", "Enabled", "enabled")
        self._ini_get_cron(parser, "SCRIPT", "Cron", "cron")
        self._ini_get(parser, "SCRIPT", "Command", "command")

    def _read_env(self):
        self._env_get_boolean("SCRIPT", "enabled")
        self._env_get_cron("SCRIPT_CRON", "cron")
        self._env_get("SCRIPT_COMMAND", "command")


@dataclass
class DiscordConfig(NotifierConfig):
    """Discord configuration"""

    enabled: bool = False
    prefix: Union[str, None] = "!"
    token: Union[str, None] = None
    channel: int = 0
    body: str = (
        "*${{display_name}}*\n*Available*: ${{items_available}}\n*Price*: ${{price}} ${{currency}}\n*Pickup*: ${{pickupdate}}"
    )
    disable_commands: bool = False

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "DISCORD", "Enabled", "enabled")
        self._ini_get(parser, "DISCORD", "Prefix", "prefix")
        self._ini_get(parser, "DISCORD", "Token", "token")
        self._ini_get_int(parser, "DISCORD", "Channel", "channel")
        self._ini_get(parser, "DISCORD", "Body", "body")
        self._ini_get_boolean(parser, "DISCORD", "DisableCommands", "disable_commands")
        self._ini_get_cron(parser, "DISCORD", "Cron", "cron")

    def _read_env(self):
        self._env_get_boolean("DISCORD", "enabled")
        self._env_get("DISCORD_PREFIX", "prefix")
        self._env_get("DISCORD_TOKEN", "token")
        self._env_get_int("DISCORD_CHANNEL", "channel")
        self._env_get("DISCORD_BODY", "body")
        self._env_get_boolean("DISCORD_DISABLE_COMMANDS", "disable_commands")
        self._env_get_cron("DISCORD_CRON", "cron")


@dataclass
class TgtgConfig(BaseConfig):
    """Tgtg configuration"""

    username: Union[str, None] = None
    access_token: Union[str, None] = None
    refresh_token: Union[str, None] = None
    datadome: Union[str, None] = None
    timeout: int = 60
    access_token_lifetime: int = 14400
    max_polling_tries: int = 24
    polling_wait_time: int = 5
    base_url: str = BASE_URL

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get(parser, "TGTG", "Username", "username")
        self._ini_get(parser, "TGTG", "AccessToken", "access_token")
        self._ini_get(parser, "TGTG", "RefreshToken", "refresh_token")
        self._ini_get(parser, "TGTG", "Datadome", "datadome")
        self._ini_get_int(parser, "TGTG", "Timeout", "timeout")
        self._ini_get_int(parser, "TGTG", "AccessTokenLifetime", "access_token_lifetime")
        self._ini_get_int(parser, "TGTG", "MaxPollingTries", "max_polling_tries")
        self._ini_get_int(parser, "TGTG", "PollingWaitTime", "polling_wait_time")

    def _read_env(self):
        self._env_get("TGTG_USERNAME", "username")
        self._env_get("TGTG_ACCESS_TOKEN", "access_token")
        self._env_get("TGTG_REFRESH_TOKEN", "refresh_token")
        self._env_get("TGTG_DATADOME", "datadome")
        self._env_get_int("TGTG_TIMEOUT", "timeout")
        self._env_get_int("TGTG_ACCESS_TOKEN_LIFETIME", "access_token_lifetime")
        self._env_get_int("TGTG_MAX_POLLING_TRIES", "max_polling_tries")
        self._env_get_int("TGTG_POLLING_WAIT_TIME", "polling_wait_time")


@dataclass
class LocationConfig(BaseConfig):
    """Location configuration"""

    enabled: bool = False
    google_maps_api_key: Union[str, None] = None
    origin_address: Union[str, None] = None

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_boolean(parser, "LOCATION", "Enabled", "enabled")
        if parser.has_option("LOCATION", "Google_Maps_API_Key"):
            log.warning(DEPRECATION_NOTICE.format("[LOCATION] Google_Maps_API_Key", "GoogleMapsAPIKey"))
        self._ini_get(parser, "LOCATION", "Google_Maps_API_Key", "google_maps_api_key")  # legacy support
        self._ini_get(parser, "LOCATION", "GoogleMapsAPIKey", "google_maps_api_key")
        if parser.has_option("LOCATION", "Address"):
            log.warning(DEPRECATION_NOTICE.format("[LOCATION] Address", "OriginAddress"))
        self._ini_get(parser, "LOCATION", "Address", "origin_address")  # legacy support
        self._ini_get(parser, "LOCATION", "OriginAddress", "origin_address")

    def _read_env(self):
        self._env_get_boolean("LOCATION", "enabled")
        self._env_get("LOCATION_GOOGLE_MAPS_API_KEY", "google_maps_api_key")
        if environ.get("LOCATION_ADDRESS", None):
            log.warning(DEPRECATION_NOTICE.format("LOCATION_ADDRESS", "LOCATION_ORIGIN_ADDRESS"))
        self._env_get("LOCATION_ADDRESS", "origin_address")  # legacy support
        self._env_get("LOCATION_ORIGIN_ADDRESS", "origin_address")


@dataclass
class Config(BaseConfig):
    """Main configuration"""

    file: Union[str, None] = None
    item_ids: list[str] = field(default_factory=list)
    sleep_time: int = 60
    schedule_cron: Cron = field(default_factory=Cron)
    debug: bool = False
    locale: str = "en_US"
    metrics: bool = False
    metrics_port: int = 8000
    disable_tests: bool = False
    quiet: bool = False
    docker: bool = False
    activity: bool = True
    tgtg: TgtgConfig = field(default_factory=TgtgConfig)
    location: LocationConfig = field(default_factory=LocationConfig)
    token_path: Union[str, None] = None
    apprise: AppriseConfig = field(default_factory=AppriseConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    pushsafer: PushSaferConfig = field(default_factory=PushSaferConfig)
    console: ConsoleConfig = field(default_factory=ConsoleConfig)
    smtp: SMTPConfig = field(default_factory=SMTPConfig)
    ifttt: IFTTTConfig = field(default_factory=IFTTTConfig)
    ntfy: NtfyConfig = field(default_factory=NtfyConfig)
    webhook: WebhookConfig = field(default_factory=WebhookConfig)
    script: ScriptConfig = field(default_factory=ScriptConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)

    def __post_init__(self):
        if self.file:
            config_file = Path(self.file)
            if not config_file.is_file():
                raise ConfigurationError(f"Configuration file '{config_file.absolute()}' is not a file!")
            config_file = Path(self.file)
            parser = configparser.ConfigParser()
            parser.read(config_file, encoding="utf-8")
            self._read_ini(parser)
            self.tgtg._read_ini(parser)
            self.location._read_ini(parser)
            self.apprise._read_ini(parser)
            self.telegram._read_ini(parser)
            self.pushsafer._read_ini(parser)
            self.console._read_ini(parser)
            self.smtp._read_ini(parser)
            self.ifttt._read_ini(parser)
            self.ntfy._read_ini(parser)
            self.webhook._read_ini(parser)
            self.script._read_ini(parser)
            self.discord._read_ini(parser)

            log.info("Loaded config from %s", config_file.absolute())
        else:
            self._read_env()
            self.tgtg._read_env()
            self.location._read_env()
            self.apprise._read_env()
            self.telegram._read_env()
            self.pushsafer._read_env()
            self.console._read_env()
            self.smtp._read_env()
            self.ifttt._read_env()
            self.ntfy._read_env()
            self.webhook._read_env()
            self.script._read_env()
            self.discord._read_env()

            log.info("Loaded config from environment variables")

        self.token_path = environ.get("TGTG_TOKEN_PATH", None)
        self._load_tokens()
        self.set_locale()

    def set_locale(self) -> None:
        if self.locale and not self.locale.startswith("en"):
            try:
                log.debug("Activating locale %s", self.locale)
                humanize.i18n.activate(self.locale)
            except FileNotFoundError as err:
                raise ConfigurationError(f"Invalid locale '{self.locale}' - {err}") from err

    def _read_ini(self, parser: configparser.ConfigParser):
        self._ini_get_list(parser, "MAIN", "ItemIDs", "item_ids")
        self._ini_get_int(parser, "MAIN", "SleepTime", "sleep_time")
        self._ini_get_cron(parser, "MAIN", "ScheduleCron", "schedule_cron")
        self._ini_get_boolean(parser, "MAIN", "Debug", "debug")
        self._ini_get(parser, "MAIN", "Locale", "locale")
        self._ini_get_boolean(parser, "MAIN", "Metrics", "metrics")
        self._ini_get_int(parser, "MAIN", "MetricsPort", "metrics_port")
        self._ini_get_boolean(parser, "MAIN", "DisableTests", "disable_tests")
        self._ini_get_boolean(parser, "MAIN", "Quiet", "quiet")
        self._ini_get_boolean(parser, "MAIN", "Docker", "docker")
        self._ini_get_boolean(parser, "MAIN", "Activity", "activity")

    def _read_env(self):
        self._env_get_list("ITEM_IDS", "item_ids")
        self._env_get_int("SLEEP_TIME", "sleep_time")
        self._env_get_cron("SCHEDULE_CRON", "schedule_cron")
        self._env_get_boolean("DEBUG", "debug")
        self._env_get("LOCALE", "locale")
        self._env_get_boolean("METRICS", "metrics")
        self._env_get_int("METRICS_PORT", "metrics_port")
        self._env_get_boolean("DISABLE_TESTS", "disable_tests")
        self._env_get_boolean("QUIET", "quiet")
        self._env_get_boolean("DOCKER", "docker")
        self._env_get_boolean("ACTIVITY", "activity")

    def _open(self, file: str, mode: str) -> IO[Any]:
        if self.token_path is None:
            raise ConfigurationError("Token path is not set.")
        return open(Path(self.token_path, file), mode, encoding="utf-8")

    def _load_tokens(self) -> None:
        """
        Reads tokens from token files
        """
        if self.token_path is not None:
            try:
                with self._open("accessToken", "r") as file:
                    self.tgtg.access_token = file.read()
                with self._open("refreshToken", "r") as file:
                    self.tgtg.refresh_token = file.read()
                with self._open("datadome", "r") as file:
                    self.tgtg.datadome = file.read()
            except FileNotFoundError:
                log.warning("No token files in token path.")
            except EnvironmentError as err:
                log.error("Error loading Tokens - %s", err)

    def save_tokens(self, access_token: str, refresh_token: str, datadome: str) -> None:
        """
        Saves TGTG Access Tokens to config.ini
        if provided or as files to token_path.
        """
        if self.file is not None:
            try:
                config_file = Path(self.file)
                config = configparser.ConfigParser()
                config.optionxform = str  # type: ignore
                config.read(config_file, encoding="utf-8")
                if "TGTG" not in config.sections():
                    config.add_section("TGTG")
                config.set("TGTG", "AccessToken", access_token)
                config.set("TGTG", "RefreshToken", refresh_token)
                config.set("TGTG", "Datadome", datadome)
                with open(config_file, "w", encoding="utf-8") as configfile:
                    configfile.write(CONFIG_FILE_HEADER)
                    config.write(configfile)
            except EnvironmentError as err:
                log.error("error saving credentials to config.ini! - %s", err)
        if self.token_path is not None:
            try:
                with self._open("accessToken", "w") as file:
                    file.write(access_token)
                with self._open("refreshToken", "w") as file:
                    file.write(refresh_token)
                with self._open("datadome", "w") as file:
                    file.write(datadome)
            except EnvironmentError as err:
                log.error("error saving credentials! - %s", err)

    def set(self, section: str, option: str, value: str) -> bool:
        """
        Sets an option in config.ini if provided.
        """
        if self.file is not None:
            try:
                config = configparser.ConfigParser()
                config.optionxform = str  # type: ignore
                config.read(self.file, encoding="utf-8")
                if section not in config.sections():
                    config.add_section(section)
                config.set(section, option, str(value))
                with open(self.file, "w", encoding="utf-8") as configfile:
                    config.write(configfile)
                return True
            except EnvironmentError as err:
                log.error("error writing config.ini! - %s", err)
        return False
