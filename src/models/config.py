from os import environ, path
import configparser
import logging

from models.errors import ConfigurationError

log = logging.getLogger('tgtg')


class Config():
    """
    Reads and provides configuration.\n
    If file is provided the config is read from the file.\n
    Else the config is read from environment variables.
    """
    def __init__(self, file: str = None):
        self.file = file
        self.item_ids = []
        self.sleep_time = 60
        self.schedule_cron = '* * * * *'
        self.debug = False
        self.metrics = False
        self.metrics_port = 8000
        self.tgtg = {}
        self.push_safer = {}
        self.smtp = {}
        self.ifttt = {}
        self.webhook = {}
        self.telegram = {}
        self.token_path = environ.get("TGTG_TOKEN_PATH", None)
        self.disable_tests = False
        if file:
            self._ini_reader(file)
            log.info("Loaded config from config.ini")
        else:
            self._env_reader()
            self._load_tokens()
            log.info("Loaded config from environment variables")
        self.telegram["chat_ids"] = [] if not self.telegram["chat_ids"] else self.telegram["chat_ids"].split(',')
        if self.schedule_cron.strip() == "":
            self.schedule_cron = '* * * * *'

    def _load_tokens(self) -> None:
        """
        Reads tokens from token files
        """
        if self.token_path:
            try:
                with open(path.join(self.token_path, 'accessToken'), 'r', encoding='utf-8') as file:
                    self.tgtg["access_token"] = file.read()
                with open(path.join(self.token_path, 'refreshToken'), 'r', encoding='utf-8') as file:
                    self.tgtg["refresh_token"] = file.read()
                with open(path.join(self.token_path, 'userID'), 'r', encoding='utf-8') as file:
                    self.tgtg["user_id"] = file.read()
            except FileNotFoundError:
                log.warning("No token files in token path.")
            except EnvironmentError as err:
                log.error("Error loading Tokens - %s", err)

    def _ini_reader(self, file: str) -> None:
        """
        Reads config from config.ini
        """
        try:
            config = configparser.ConfigParser()
            config.read(file, encoding='utf-8')
            self.debug = config["MAIN"].getboolean("Debug", False)
            self.item_ids = config["MAIN"].get("ItemIDs").split(
                ',') if "ItemIDs" in config["MAIN"] else []
            self.sleep_time = config["MAIN"].getint("SleepTime")
            self.schedule_cron = config["MAIN"].get("ScheduleCron", '* * * * *')
            self.metrics = config["MAIN"].getboolean("Metrics", False)
            self.metrics_port = config["MAIN"].getint("MetricsPort", 8000)
            self.tgtg = {
                "username": config["TGTG"].get("Username"),
                "access_token": config["TGTG"].get("AccessToken"),
                "refresh_token": config["TGTG"].get("RefreshToken"),
                "user_id": config["TGTG"].get("UserId"),
                "timeout": config["TGTG"].getint("Timeout", 60),
                "access_token_lifetime": config["TGTG"].getint("AccessTokenLifetime", 3600 * 4),
                "max_polling_tries": config["TGTG"].getint("MaxPollingTries", 24),
                "polling_wait_time": config["TGTG"].getint("PollingWaitTime", 5)
            }
            self.push_safer = {
                "enabled": config["PUSHSAFER"].getboolean("enabled", False),
                "key": config["PUSHSAFER"].get("Key"),
                "deviceId": config["PUSHSAFER"].get("DeviceID"),
                "cron": config["PUSHSAFER"].get("cron", '* * * * *')
            }
            self.smtp = {
                "enabled": config["SMTP"].getboolean("enabled", False),
                "host": config["SMTP"].get("Host"),
                "port": config["SMTP"].getint("Port"),
                "tls": config["SMTP"].getboolean("TLS"),
                "username": config["SMTP"].get("Username"),
                "password": config["SMTP"].get("Password"),
                "cron": config["SMTP"].get("cron", '* * * * *'),
                "sender": config["SMTP"].get("Sender"),
                "recipient": config["SMTP"].get("Recipient"),
                "subject": config["SMTP"].get("Subject", "New Magic Bags"),
                "body": config["SMTP"].get("Body", "<b>${{display_name}}</b> </br>New Amount: ${{items_available}}")
            }
            self.ifttt = {
                "enabled": config["IFTTT"].getboolean("enabled", False),
                "event": config["IFTTT"].get("Event"),
                "key": config["IFTTT"].get("Key"),
                "body": config["IFTTT"].get("Body", None),
                "cron": config["IFTTT"].get("cron", '* * * * *')
            }
            self.webhook = {
                "enabled": config["WEBHOOK"].getboolean("enabled", False),
                "url": config["WEBHOOK"].get("URL"),
                "method": config["WEBHOOK"].get("Method", "GET"),
                "body": config["WEBHOOK"].get("body", None),
                "type": config["WEBHOOK"].get("type", "text/plain"),
                "timeout": config["WEBHOOK"].getint("timeout", 60),
                "cron": config["WEBHOOK"].get("cron", '* * * * *')
            }
            self.telegram = {
                "enabled": config["TELEGRAM"].getboolean("enabled", False),
                "token": config["TELEGRAM"].get("token", None),
                "chat_ids": config["TELEGRAM"].get("chat_ids", None),
                "timeout": config["TELEGRAM"].getint("timeout", 60),
                "cron": config["TELEGRAM"].get("cron", '* * * * *'),
                "body": config["TELEGRAM"].get("body", "*${{display_name}}*\n*Available*: ${{items_available}}\n*Price*: ${{price}} ${{currency}}\n*Pickup*: ${{pickupdate}}").replace('\\n', '\n')
            }
            #only for backwards compatibility
            if not self.telegram["chat_ids"] and config["TELEGRAM"].get("chat_id", None):
                self.telegram["chat_ids"] = config["TELEGRAM"].get("chat_id", None)
        except ValueError as err:
            raise ConfigurationError(err) from err

    def _env_reader(self) -> None:
        """
        Reads config from environment variables
        """
        try:
            self.item_ids = environ.get("ITEM_IDS").split(
                ",") if environ.get("ITEM_IDS") else []
            self.sleep_time = int(environ.get("SLEEP_TIME", 20))
            self.schedule_cron = environ.get("SCHEDULE_CRON", '* * * * *')
            self.debug = environ.get(
                "DEBUG", "false").lower() in ('true', '1', 't')
            self.metrics = environ.get(
                "METRICS", "false").lower() in ('true', '1', 't')
            self.metrics_port = int(environ.get("METRICS_PORT", 8000))
            self.disable_tests = environ.get(
                "DISABLE_TESTS", "false").lower() in ('true', '1', 't')
            self.tgtg = {
                "username": environ.get("TGTG_USERNAME"),
                "access_token": environ.get("TGTG_ACCESS_TOKEN", None),
                "refresh_token": environ.get("TGTG_REFRESH_TOKEN", None),
                "user_id": environ.get("TGTG_USER_ID", None),
                "timeout": int(environ.get("TGTG_TIMEOUT", 60)),
                "access_token_lifetime": int(environ.get("TGTG_ACCESS_TOKEN_LIFETIME", 3600 * 4)),
                "max_polling_tries": int(environ.get("TGTG_MAX_POLLING_TRIES", 24)),
                "polling_wait_time": int(environ.get("TGTG_POLLING_WAIT_TIME", 5))
            }
            self.push_safer = {
                "enabled": environ.get("PUSH_SAFER", "false").lower() in ('true', '1', 't'),
                "key": environ.get("PUSH_SAFER_KEY", None),
                "deviceId": environ.get("PUSH_SAFER_DEVICE_ID", None),
                "cron": environ.get("PUSH_SAFER_CRON", '* * * * *')
            }
            self.smtp = {
                "enabled": environ.get("SMTP", "false").lower() in ('true', '1', 't'),
                "host": environ.get("SMTP_HOST", None),
                "port": int(environ.get("SMTP_PORT", 25)),
                "tls": environ.get("SMTP_TLS", "false").lower() in ('true', '1', 't'),
                "username": environ.get("SMTP_USERNAME", ""),
                "password": environ.get("SMTP_PASSWORD", ""),
                "sender": environ.get("SMTP_SENDER", None),
                "recipient": environ.get("SMTP_RECIPIENT", None),
                "cron": environ.get("SMTP_CRON", '* * * * *'),
                "subject": environ.get("SMTP_SUBJECT", "New Magic Bags"),
                "body": environ.get("SMTP_BODY", "<b>${{display_name}}</b> </br>New Amount: ${{items_available}}")
            }
            self.ifttt = {
                "enabled": environ.get("IFTTT", "false").lower() in ('true', '1', 't'),
                "event": environ.get("IFTTT_EVENT", "tgtg_notification"),
                "key": environ.get("IFTTT_KEY", None),
                "body": environ.get("IFTTT_BODY", None),
                "cron": environ.get("IFTTT_CRON", '* * * * *')
            }
            self.webhook = {
                "enabled": environ.get("WEBHOOK", "false").lower() in ('true', '1', 't'),
                "url": environ.get("WEBHOOK_URL", ""),
                "method": environ.get("WEBHOOK_METHOD", "GET"),
                "body": environ.get("WEBHOOK_BODY", ""),
                "type": environ.get("WEBHOOK_TYPE", "text/plain"),
                "timeout": int(environ.get("WEBHOOK_TIMEOUT", 60)),
                "cron": environ.get("WEBHOOK_CRON", '* * * * *')
            }
            self.telegram = {
                "enabled": environ.get("TELEGRAM", "false").lower() in ('true', '1', 't'),
                "token": environ.get("TELEGRAM_TOKEN", None),
                "chat_ids": environ.get("TELEGRAM_CHAT_IDS", None),
                "timeout": int(environ.get("TELEGRAM_TIMEOUT", 60)),
                "cron": environ.get("TELEGRAM_CRON", '* * * * *'),
                "body": environ.get("TELEGRAM_BODY", "*${{display_name}}*\n*Available*: ${{items_available}}\n*Price*: ${{price}} ${{currency}}\n*Pickup*: ${{pickupdate}}").replace('\\n', '\n')
            }
            #only for backwards compability
            if not self.telegram["chat_ids"] and environ.get("TELEGRAM_CHAT_ID", None):
                self.telegram["chat_ids"] = environ.get("TELEGRAM_CHAT_ID", None)
        except ValueError as err:
            raise ConfigurationError(err) from err

    def set(self, section: str, option: str, value: str) -> bool:
        """
        Sets an option in config.ini if provided.
        """
        if self.file:
            try:
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(self.file)
                config.set(section, option, value)
                with open(self.file, 'w', encoding='utf-8') as configfile:
                    config.write(configfile)
                return True
            except EnvironmentError as err:
                log.error("error writing config.ini! - %s", err)
        return False

    def save_tokens(self, access_token, refresh_token, user_id):
        """
        Saves TGTG Access Tokens to config.ini if provided or as files to token_path.
        """
        if self.file:
            try:
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(self.file)
                config.set("TGTG", "AccessToken", access_token)
                config.set("TGTG", "RefreshToken", refresh_token)
                config.set("TGTG", "UserId", user_id)
                with open(self.file, 'w', encoding='utf-8') as configfile:
                    config.write(configfile)
            except EnvironmentError as err:
                log.error("error saving credentials to config.ini! - %s", err)
        if self.token_path:
            try:
                with open(path.join(self.token_path, 'accessToken'), 'w', encoding='utf-8') as file:
                    file.write(access_token)
                with open(path.join(self.token_path, 'refreshToken'), 'w', encoding='utf-8') as file:
                    file.write(refresh_token)
                with open(path.join(self.token_path, 'userID'), 'w', encoding='utf-8') as file:
                    file.write(user_id)
            except EnvironmentError as err:
                log.error("error saving credentials! - %s", err)
