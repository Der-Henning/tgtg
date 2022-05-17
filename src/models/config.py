import sys
from os import environ, path
import configparser
import logging

log = logging.getLogger('tgtg')


class Config():
    def __init__(self, file=None):
        self.file = file
        self.item_ids = []
        self.sleep_time = 60
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

    def _load_tokens(self):
        if self.token_path:
            try:
                self.tgtg["access_token"] = open(
                    path.join(self.token_path, 'accessToken'), 'r').read()
                self.tgtg["refresh_token"] = open(
                    path.join(self.token_path, 'refreshToken'), 'r').read()
                self.tgtg["user_id"] = open(
                    path.join(self.token_path, 'userID'), 'r').read()
            except Exception:
                pass

    def _ini_reader(self, file):
        config = configparser.ConfigParser()
        config.read(file)
        self.debug = config["MAIN"].getboolean("Debug", False)
        self.item_ids = config["MAIN"].get("ItemIDs").split(
            ',') if "ItemIDs" in config["MAIN"] else []
        self.sleep_time = config["MAIN"].getint("SleepTime")
        self.metrics = config["MAIN"].getboolean("Metrics", False)
        self.metrics_port = config["MAIN"].getint("MetricsPort", 8000)
        self.tgtg = {
            "username": config["TGTG"].get("Username"),
            "access_token": config["TGTG"].get("AccessToken"),
            "refresh_token": config["TGTG"].get("RefreshToken"),
            "user_id": config["TGTG"].get("UserId"),
            "timeout": config["TGTG"].getint("Timeout", 60),
            "access_token_lifetime": config["TGTG"].get("AccessTokenLifetime", 3600 * 4),
            "max_polling_tries": config["TGTG"].get("MaxPollingTries", 24),
            "polling_wait_time": config["TGTG"].get("PollingWaitTime", 5)
        }
        self.push_safer = {
            "enabled": config["PUSHSAFER"].getboolean("enabled", False),
            "key": config["PUSHSAFER"].get("Key"),
            "deviceId": config["PUSHSAFER"].get("DeviceID")
        }
        self.smtp = {
            "enabled": config["SMTP"].getboolean("enabled", False),
            "host": config["SMTP"].get("Host"),
            "port": config["SMTP"].getint("Port"),
            "tls": config["SMTP"].getboolean("TLS"),
            "username": config["SMTP"].get("Username"),
            "password": config["SMTP"].get("Password"),
            "sender": config["SMTP"].get("Sender"),
            "recipient": config["SMTP"].get("Recipient")
        }
        self.ifttt = {
            "enabled": config["IFTTT"].getboolean("enabled", False),
            "event": config["IFTTT"].get("Event"),
            "key": config["IFTTT"].get("Key")
        }
        self.webhook = {
            "enabled": config["WEBHOOK"].getboolean("enabled", False),
            "url": config["WEBHOOK"].get("URL"),
            "method": config["WEBHOOK"].get("Method", "GET"),
            "body": config["WEBHOOK"].get("body", None),
            "type": config["WEBHOOK"].get("type", "text/plain"),
            "timeout": config["WEBHOOK"].getint("timeout", 60)
        }
        self.telegram = {
            "enabled": config["TELEGRAM"].getboolean("enabled", False),
            "token": config["TELEGRAM"].get("token"),
            "chat_ids": config["TELEGRAM"].get("chat_id"), #only for backwards compability
            "chat_ids": config["TELEGRAM"].get("chat_ids"),
            "body": config["TELEGRAM"].get("body", "*${{display_name}}*\n*Available*: ${{items_available}}\n*Price*: ${{price}} ${{currency}}\n*Pickup*: ${{pickupdate}}").replace('\\n', '\n')
        }

    def _env_reader(self):
        self.item_ids = environ.get("ITEM_IDS").split(
            ",") if environ.get("ITEM_IDS") else []
        self.sleep_time = int(environ.get("SLEEP_TIME", 20))
        self.debug = environ.get(
            "DEBUG", "false").lower() in ('true', '1', 't')
        self.metrics = environ.get(
            "METRICS", "false").lower() in ('true', '1', 't')
        self.metrics_port = environ.get("METRICS_PORT", 8000)
        self.disable_tests = environ.get(
            "DISABLE_TESTS", "false").lower() in ('true', '1', 't')
        self.tgtg = {
            "username": environ.get("TGTG_USERNAME"),
            "access_token": environ.get("TGTG_ACCESS_TOKEN", None),
            "refresh_token": environ.get("TGTG_REFRESH_TOKEN", None),
            "user_id": environ.get("TGTG_USER_ID", None),
            "timeout": environ.get("TGTG_TIMEOUT", 60),
            "access_token_lifetime": environ.get("TGTG_ACCESS_TOKEN_LIFETIME", 3600 * 4),
            "max_polling_tries": environ.get("TGTG_MAX_POLLING_TRIES", 24),
            "polling_wait_time": environ.get("TGTG_POLLING_WAIT_TIME", 5)
        }
        self.push_safer = {
            "enabled": environ.get("PUSH_SAFER", "false").lower() in ('true', '1', 't'),
            "key": environ.get("PUSH_SAFER_KEY", None),
            "deviceId": environ.get("PUSH_SAFER_DEVICE_ID", None)
        }
        self.smtp = {
            "enabled": environ.get("SMTP", "false").lower() in ('true', '1', 't'),
            "host": environ.get("SMTP_HOST", None),
            "port": environ.get("SMTP_PORT", 25),
            "tls": environ.get("SMTP_TLS", "false").lower() in ('true', '1', 't'),
            "username": environ.get("SMTP_USERNAME", ""),
            "password": environ.get("SMTP_PASSWORD", ""),
            "sender": environ.get("SMTP_SENDER", None),
            "recipient": environ.get("SMTP_RECIPIENT", None)
        }
        self.ifttt = {
            "enabled": environ.get("IFTTT", "false").lower() in ('true', '1', 't'),
            "event": environ.get("IFTTT_EVENT", "tgtg_notification"),
            "key": environ.get("IFTTT_KEY", None)
        }
        self.webhook = {
            "enabled": environ.get("WEBHOOK", "false").lower() in ('true', '1', 't'),
            "url": environ.get("WEBHOOK_URL", ""),
            "method": environ.get("WEBHOOK_METHOD", "GET"),
            "body": environ.get("WEBHOOK_BODY", ""),
            "type": environ.get("WEBHOOK_TYPE", "text/plain"),
            "timeout": int(environ.get("WEBHOOK_TIMEOUT", 60))
        }
        self.telegram = {
            "enabled": environ.get("TELEGRAM", "false").lower() in ('true', '1', 't'),
            "token": environ.get("TELEGRAM_TOKEN", None),
            "chat_ids": environ.get("TELEGRAM_CHAT_ID", None), #only for backwards compability
            "chat_ids": environ.get("TELEGRAM_CHAT_IDS", None),
            "body": environ.get("TELEGRAM_BODY", "*${{display_name}}*\n*Available*: ${{items_available}}\n*Price*: ${{price}} ${{currency}}\n*Pickup*: ${{pickupdate}}").replace('\\n', '\n')
        }

    def set(self, section, option, value):
        if self.file:
            try:
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(self.file)
                config.set(section, option, value)
                with open(self.file, 'w') as configfile:
                    config.write(configfile)
                return True
            except Exception:
                log.error("error writing config.ini! - %s", sys.exc_info())
        return False

    def save_tokens(self, access_token, refresh_token, user_id):
        if self.file:
            try:
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(self.file)
                config.set("TGTG", "AccessToken", access_token)
                config.set("TGTG", "RefreshToken", refresh_token)
                config.set("TGTG", "UserId", user_id)
                with open(self.file, 'w') as configfile:
                    config.write(configfile)
            except Exception:
                log.error(
                    "error saving credentials to config.ini! - %s", sys.exc_info())
        if self.token_path:
            try:
                open(path.join(self.token_path, 'accessToken'),
                     'w').write(access_token)
                open(path.join(self.token_path, 'refreshToken'),
                     'w').write(refresh_token)
                open(path.join(self.token_path, 'userID'),
                     'w').write(user_id)
            except Exception:
                log.error("error saving credentials! - %s", sys.exc_info())
