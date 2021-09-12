from os import environ


class Config():
    def __init__(self):
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

        ## ToDo: create notifier for any WebHook
        self.webhook = {
            "enabled": False
        }
