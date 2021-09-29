from os import environ
import configparser
import logging as log


class Config():
    def __init__(self, file=None):
        self.item_ids = []
        self.sleep_time = 20
        self.debug = False
        self.tgtg = {}
        self.pushSafer = {}
        self.smtp = {}
        self.ifttt = {}
        self.webhook = {}
        if file:
            self._ini_reader(file)
            log.info("Loaded config from config.ini")
        else:
            self._env_reader()
            log.info("Loaded config from environment variables")

    def _ini_reader(self, file):
        config = configparser.ConfigParser()
        config.read(file)
        self.debug = config["MAIN"]["Debug"].lower() in ('true', '1', 't')
        self.item_ids = config["MAIN"]["ItemIDs"].split(
            ',') if "ItemIDs" in config["MAIN"] else []
        self.sleep_time = int(config["MAIN"]["SleepTime"])
        self.tgtg = {
            "username": config["TGTG"]["Username"],
            "password": config["TGTG"]["Password"]
        }
        self.pushSafer = {
            "enabled": config["PUSHSAFER"]["enabled"].lower() in ('true', '1', 't'),
            "key": config["PUSHSAFER"]["Key"],
            "deviceId": config["PUSHSAFER"]["DeviceID"]
        }
        self.smtp = {
            "enabled": config["SMTP"]["enabled"].lower() in ('true', '1', 't'),
            "host": config["SMTP"]["Host"],
            "port": config["SMTP"]["Port"],
            "tls": config["SMTP"]["TLS"].lower() in ('true', '1', 't'),
            "username": config["SMTP"]["Username"],
            "password": config["SMTP"]["Password"],
            "sender": config["SMTP"]["Sender"],
            "recipient": config["SMTP"]["Recipient"]
        }
        self.ifttt = {
            "enabled": config["IFTTT"]["enabled"].lower() in ('true', '1', 't'),
            "event": config["IFTTT"]["Event"],
            "key": config["IFTTT"]["Key"]
        }

    def _env_reader(self):
        self.item_ids = environ.get("ITEM_IDS").split(
            ",") if environ.get("ITEM_IDS") else []
        self.sleep_time = int(environ.get("SLEEP_TIME", 20))
        self.debug = True if environ.get(
            "DEBUG", "").lower() in ('true', '1', 't') else False
        self.tgtg = {
            "username": environ.get("TGTG_USERNAME"),
            "password": environ.get("TGTG_PASSWORD")
        }
        self.pushSafer = {
            "enabled": environ.get("PUSH_SAFER", "").lower() in ('true', '1', 't'),
            "key": environ.get("PUSH_SAFER_KEY"),
            "deviceId": environ.get("PUSH_SAFER_DEVICE_ID")
        }
        self.smtp = {
            "enabled": environ.get("SMTP", "").lower() in ('true', '1', 't'),
            "host": environ.get("SMTP_HOST"),
            "port": environ.get("SMTP_PORT", 25),
            "tls": environ.get("SMTP_TLS", "").lower() in ('true', '1', 't'),
            "username": environ.get("SMTP_USERNAME", ""),
            "password": environ.get("SMTP_PASSWORD", ""),
            "sender": environ.get("SMTP_SENDER"),
            "recipient": environ.get("SMTP_RECIPIENT")
        }
        self.ifttt = {
            "enabled": environ.get("IFTTT", "").lower() in ('true', '1', 't'),
            "event": environ.get("IFTTT_EVENT", "tgtg_notification"),
            "key": environ.get("IFTTT_KEY")
        }

        # ToDo: create notifier for any WebHook
        self.webhook = {
            "enabled": False
        }
