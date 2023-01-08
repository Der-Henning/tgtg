import configparser
import logging
from io import TextIOWrapper
from os import environ
from pathlib import Path
from typing import Any

from models.cron import Cron
from models.errors import ConfigurationError

log = logging.getLogger('tgtg')


DEFAULT_CONFIG = {
    'item_ids': [],
    'sleep_time': 60,
    'schedule_cron': Cron('* * * * *'),
    'debug': False,
    'metrics': False,
    'metrics_port': 8000,
    'disable_tests': False,
    'tgtg': {
        'username': None,
        'access_token': None,
        'refresh_token': None,
        'user_id': None,
        'timeout': 60,
        'access_token_lifetime': 14400,
        'max_polling_tries': 24,
        'polling_wait_time': 5
    },
    'push_safer': {
        'enabled': False,
        'key': '',
        'deviceId': '',
        'cron': Cron('* * * * *')
    },
    'smtp': {
        'enabled': False,
        'host': 'smtp.gmail.com',
        'port': 587,
        'tls': True,
        'ssl': False,
        'username': '',
        'password': '',
        'sender': '',
        'recipient': [],
        'cron': Cron('* * * * *'),
        'subject': 'New Magic Bags',
        'body': '<b>${{display_name}}</b> </br>'
                'New Amount: ${{items_available}}'
    },
    'ifttt': {
        'enabled': False,
        'event': 'tgtg_notification',
        'key': '',
        'body': '{"value1": "${{display_name}}", '
                '"value2": ${{items_available}}, '
                '"value3": "https://share.toogoodtogo.com/item/${{item_id}}"}',
        'timeout': 60,
        'cron': Cron('* * * * *')
    },
    'webhook': {
        'enabled': False,
        'url': '',
        'method': 'POST',
        'body': '',
        'type': '',
        'timeout': 60,
        'cron': Cron('* * * * *')
    },
    'telegram': {
        'enabled': False,
        'token': '',
        'chat_ids': [],
        'timeout': 60,
        'cron': Cron('* * * * *'),
        'body': '*${{display_name}}*\n'
                '*Available*: ${{items_available}}\n'
                '*Price*: ${{price}} ${{currency}}\n'
                '*Pickup*: ${{pickupdate}}'
    }
}


class Config():
    """
    Reads and provides configuration.\n
    If file is provided the config is read from the file.\n
    Else the config is read from environment variables.
    """

    item_ids: list
    sleep_time: int
    schedule_cron: str
    debug: bool
    metrics: bool
    metrics_port: int
    disable_tests: bool
    tgtg: dict
    push_safer: dict
    smtp: dict
    ifttt: dict
    webhook: dict
    telegram: dict

    def __init__(self, file: str = None):
        self.file = Path(file) if file is not None else None
        for key in DEFAULT_CONFIG:
            setattr(self, key, DEFAULT_CONFIG[key])

        if self.file is not None:
            if not self.file.exists():
                raise ConfigurationError(
                    f"Configuration file '{self.file.absolute()}' "
                    "does not exist!")
            self._read_ini()
            log.info("Loaded config from %s", self.file.absolute())
        else:
            self._read_env()
            log.info("Loaded config from environment variables")

        self.token_path = environ.get("TGTG_TOKEN_PATH", None)
        self._load_tokens()

    def _open(self, file: str, mode: str) -> TextIOWrapper:
        return open(Path(self.token_path, file), mode, encoding='utf-8')

    def _load_tokens(self) -> None:
        """
        Reads tokens from token files
        """
        if self.token_path is not None:
            try:
                with self._open('accessToken', 'r') as file:
                    self.tgtg["access_token"] = file.read()
                with self._open('refreshToken', 'r') as file:
                    self.tgtg["refresh_token"] = file.read()
                with self._open('userID', 'r') as file:
                    self.tgtg["user_id"] = file.read()
            except FileNotFoundError:
                log.warning("No token files in token path.")
            except EnvironmentError as err:
                log.error("Error loading Tokens - %s", err)

    def _getattr(self, attr: str) -> None:
        if '.' in attr:
            _attr, _key = attr.split('.')
            return self.__dict__[_attr][_key]
        return getattr(self, attr)

    def _setattr(self, attr: str, value: Any) -> None:
        if '.' in attr:
            _attr, _key = attr.split('.')
            self.__dict__[_attr][_key] = value
        else:
            setattr(self, attr, value)

    def _ini_get(self, config: configparser.ConfigParser,
                 section: str, key: str, attr: str) -> None:
        if section in config:
            self._setattr(attr, config[section].get(key, self._getattr(attr)))

    def _ini_get_boolean(self, config: configparser.ConfigParser,
                         section: str, key: str, attr: str) -> None:
        if section in config:
            self._setattr(attr, config[section].getboolean(
                key, self._getattr(attr)))

    def _ini_get_int(self, config: configparser.ConfigParser,
                     section: str, key: str, attr: str) -> None:
        if section in config:
            self._setattr(attr, config[section].getint(
                key, self._getattr(attr)))

    def _ini_get_float(self, config: configparser.ConfigParser,
                       section: str, key: str, attr: str) -> None:
        if section in config:
            self._setattr(attr, config[section].getfloat(
                key, self._getattr(attr)))

    def _ini_get_array(self, config: configparser.ConfigParser,
                       section: str, key: str, attr: str) -> None:
        if section in config:
            value = config[section].get(key, None)
            if value:
                arr = [val.strip() for val in value.split(',')]
                self._setattr(attr, arr)

    def _ini_get_cron(self, config: configparser.ConfigParser,
                      section: str, key: str, attr: str) -> None:
        if section in config:
            value = config[section].get(key, None)
            if value is not None:
                self._setattr(attr, Cron(value))

    def _read_ini(self) -> None:
        try:
            config = configparser.ConfigParser()
            config.read(self.file, encoding='utf-8')

            self._ini_get_boolean(config, "MAIN", "debug", "debug")
            self._ini_get_array(config, "MAIN", "ItemIDs", "item_ids")
            self._ini_get_int(config, "MAIN", "SleepTime", "sleep_time")
            self._ini_get_cron(config, "MAIN", "ScheduleCron", "schedule_cron")
            self._ini_get_boolean(config, "MAIN", "Metrics", "metrics")
            self._ini_get_int(config, "MAIN", "MetricsPort", "metrics_port")
            self._ini_get_boolean(config, "MAIN", "DisableTests",
                                  "disable_tests")

            self._ini_get(config, "TGTG", "Username", "tgtg.username")
            self._ini_get(config, "TGTG", "AccessToken", "tgtg.access_token")
            self._ini_get(config, "TGTG", "RefreshToken", "tgtg.refresh_token")
            self._ini_get(config, "TGTG", "UserId", "tgtg.user_id")
            self._ini_get_int(config, "TGTG", "Timeout", "tgtg.timeout")
            self._ini_get_int(config, "TGTG", "AccessTokenLifetime",
                              "tgtg.access_token_lifetime")
            self._ini_get_int(config, "TGTG", "MaxPollingTries",
                              "tgtg.max_polling_tries")
            self._ini_get_int(config, "TGTG", "PollingWaitTime",
                              "tgtg.polling_wait_time")

            self._ini_get_boolean(config, "PUSHSAFER",
                                  "enabled", "push_safer.enabled")
            self._ini_get(config, "PUSHSAFER", "Key", "push_safer.key")
            self._ini_get(config, "PUSHSAFER", "DeviceID",
                          "push_safer.deviceId")
            self._ini_get_cron(config, "PUSHSAFER", "cron", "push_safer.cron")

            self._ini_get_boolean(config, "SMTP", "enabled", "smtp.enabled")
            self._ini_get(config, "SMTP", "Host", "smtp.host")
            self._ini_get_int(config, "SMTP", "Port", "smtp.port")
            self._ini_get_boolean(config, "SMTP", "TLS", "smtp.tls")
            self._ini_get_boolean(config, "SMTP", "SSL", "smtp.ssl")
            self._ini_get(config, "SMTP", "Username", "smtp.username")
            self._ini_get(config, "SMTP", "Password", "smtp.password")
            self._ini_get_cron(config, "SMTP", "cron", "smtp.cron")
            self._ini_get(config, "SMTP", "Sender", "smtp.sender")
            self._ini_get_array(config, "SMTP", "Recipient", "smtp.recipient")
            self._ini_get(config, "SMTP", "Subject", "smtp.subject")
            self._ini_get(config, "SMTP", "Body", "smtp.body")

            self._ini_get_boolean(config, "IFTTT", "enabled", "ifttt.enabled")
            self._ini_get(config, "IFTTT", "Event", "ifttt.event")
            self._ini_get(config, "IFTTT", "Key", "ifttt.key")
            self._ini_get(config, "IFTTT", "Body", "ifttt.body")
            self._ini_get_int(config, "IFTTT", "Timeout", "ifttt.timeout")
            self._ini_get_cron(config, "IFTTT", "cron", "ifttt.cron")

            self._ini_get_boolean(config, "WEBHOOK", "enabled",
                                  "webhook.enabled")
            self._ini_get(config, "WEBHOOK", "URL", "webhook.url")
            self._ini_get(config, "WEBHOOK", "Method", "webhook.method")
            self._ini_get(config, "WEBHOOK", "body", "webhook.body")
            self._ini_get(config, "WEBHOOK", "type", "webhook.type")
            self._ini_get_int(config, "WEBHOOK", "timeout", "webhook.timeout")
            self._ini_get_cron(config, "WEBHOOK", "cron", "webhook.cron")

            self._ini_get_boolean(config, "TELEGRAM",
                                  "enabled", "telegram.enabled")
            self._ini_get(config, "TELEGRAM", "token", "telegram.token")
            self._ini_get_array(config, "TELEGRAM",
                                "chat_ids", "telegram.chat_ids")
            self._ini_get_int(config, "TELEGRAM",
                              "timeout", "telegram.timeout")
            self._ini_get_cron(config, "TELEGRAM", "cron", "telegram.cron")
            self._ini_get(config, "TELEGRAM", "body", "telegram.body")
        except ValueError as err:
            raise ConfigurationError(err) from err

    def _env_get(self, key: str, attr: str) -> None:
        value = environ.get(key, None)
        if value is not None:
            value = value.replace('\\n', '\n')
            self._setattr(attr, value)

    def _env_get_boolean(self, key: str, attr: str) -> None:
        value = environ.get(key, None)
        if value is not None:
            self._setattr(attr, value.lower() in ('true', '1', 't'))

    def _env_get_int(self, key: str, attr: str) -> None:
        self._setattr(attr, int(environ.get(key, self._getattr(attr))))

    def _env_get_float(self, key: str, attr: str) -> None:
        self._setattr(attr, float(environ.get(key, self._getattr(attr))))

    def _env_get_array(self, key: str, attr: str) -> None:
        value = environ.get(key, None)
        if value:
            arr = [val.strip() for val in value.split(',')]
            self._setattr(attr, arr)

    def _env_get_cron(self, key: str, attr: str) -> None:
        value = environ.get(key, None)
        if value is not None:
            self._setattr(attr, Cron(value))

    def _read_env(self) -> None:
        try:
            self._env_get_boolean("DEBUG", "debug")
            self._env_get_array("ITEM_IDS", "item_ids")
            self._env_get_int("SLEEP_TIME", "sleep_time")
            self._env_get_cron("SCHEDULE_CRON", "schedule_cron")
            self._env_get_boolean("METRICS", "metrics")
            self._env_get_int("METRICS_PORT", "metrics_port")
            self._env_get_boolean("DISABLE_TESTS", "disable_tests")

            self._env_get("TGTG_USERNAME", "tgtg.username")
            self._env_get("TGTG_ACCESS_TOKEN", "tgtg.access_token")
            self._env_get("TGTG_REFRESH_TOKEN", "tgtg.refresh_token")
            self._env_get("TGTG_USER_ID", "tgtg.user_id")
            self._env_get_int("TGTG_TIMEOUT", "tgtg.timeout")
            self._env_get_int("TGTG_ACCESS_TOKEN_LIFETIME",
                              "tgtg.access_token_lifetime")
            self._env_get_int("TGTG_MAX_POLLING_TRIES",
                              "tgtg.max_polling_tries")
            self._env_get_int("TGTG_POLLING_WAIT_TIME",
                              "tgtg.polling_wait_time")

            self._env_get_boolean("PUSH_SAFER", "push_safer.enabled")
            self._env_get("PUSH_SAFER_KEY", "push_safer.key")
            self._env_get("PUSH_SAFER_DEVICE_ID", "push_safer.deviceId")
            self._env_get_cron("PUSH_SAFER_CRON", "push_safer.cron")

            self._env_get_boolean("SMTP", "smtp.enabled")
            self._env_get("SMTP_HOST", "smtp.host")
            self._env_get_int("SMTP_PORT", "smtp.port")
            self._env_get_boolean("SMTP_TLS", "smtp.tls")
            self._env_get_boolean("SMTP_SSL", "smtp.ssl")
            self._env_get("SMTP_USERNAME", "smtp.username")
            self._env_get("SMTP_PASSWORD", "smtp.password")
            self._env_get("SMTP_SENDER", "smtp.sender")
            self._env_get_array("SMTP_RECIPIENT", "smtp.recipient")
            self._env_get_cron("SMTP_CRON", "smtp.cron")
            self._env_get("SMTP_SUBJECT", "smtp.subject")
            self._env_get("SMTP_BODY", "smtp.body")

            self._env_get_boolean("IFTTT", "ifttt.enabled")
            self._env_get("IFTTT_EVENT", "ifttt.event")
            self._env_get("IFTTT_KEY", "ifttt.key")
            self._env_get("IFTTT_BODY", "ifttt.body")
            self._env_get_int("IFTTT_TIMEOUT", "ifttt.timeout")
            self._env_get_cron("IFTTT_CRON", "ifttt.cron")

            self._env_get_boolean("WEBHOOK", "webhook.enabled")
            self._env_get("WEBHOOK_URL", "webhook.url")
            self._env_get("WEBHOOK_METHOD", "webhook.method")
            self._env_get("WEBHOOK_BODY", "webhook.body")
            self._env_get("WEBHOOK_TYPE", "webhook.type")
            self._env_get_int("WEBHOOK_TIMEOUT", "webhook.timeout")
            self._env_get_cron("WEBHOOK_CRON", "webhook.cron")

            self._env_get_boolean("TELEGRAM", "telegram.enabled")
            self._env_get("TELEGRAM_TOKEN", "telegram.token")
            self._env_get_array("TELEGRAM_CHAT_IDS", "telegram.chat_ids")
            self._env_get_int("TELEGRAM_TIMEOUT", "telegram.timeout")
            self._env_get_cron("TELEGRAM_CRON", "telegram.cron")
            self._env_get("TELEGRAM_BODY", "telegram.body")
        except ValueError as err:
            raise ConfigurationError(err) from err

    def set(self, section: str, option: str, value: Any) -> bool:
        """
        Sets an option in config.ini if provided.
        """
        if self.file is not None:
            try:
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(self.file)
                if section not in config.sections():
                    config.add_section(section)
                config.set(section, option, str(value))
                with open(self.file, 'w', encoding='utf-8') as configfile:
                    config.write(configfile)
                return True
            except EnvironmentError as err:
                log.error("error writing config.ini! - %s", err)
        return False

    def save_tokens(self, access_token: str, refresh_token: str,
                    user_id: str) -> None:
        """
        Saves TGTG Access Tokens to config.ini
        if provided or as files to token_path.
        """
        if self.file is not None:
            try:
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(self.file)
                if "TGTG" not in config.sections():
                    config.add_section("TGTG")
                config.set("TGTG", "AccessToken", access_token)
                config.set("TGTG", "RefreshToken", refresh_token)
                config.set("TGTG", "UserId", user_id)
                with open(self.file, 'w', encoding='utf-8') as configfile:
                    config.write(configfile)
            except EnvironmentError as err:
                log.error("error saving credentials to config.ini! - %s", err)
        if self.token_path is not None:
            try:
                with self._open('accessToken', 'w') as file:
                    file.write(access_token)
                with self._open('refreshToken', 'w') as file:
                    file.write(refresh_token)
                with self._open('userID', 'w') as file:
                    file.write(user_id)
            except EnvironmentError as err:
                log.error("error saving credentials! - %s", err)
