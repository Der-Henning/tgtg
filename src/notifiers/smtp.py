from models import Item, Config
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging as log


class SMTP():
    def __init__(self, config: Config):
        self.server = None
        self.debug = 1 if config.debug else 0
        self.host = config.smtp["host"]
        self.port = config.smtp["port"]
        self.tls = config.smtp["tls"]
        self.username = config.smtp["username"]
        self.password = config.smtp["password"]
        self.sender = config.smtp["sender"]
        self.recipient = config.smtp["recipient"]
        self.enabled = config.smtp["enabled"]
        if self.enabled:
            self._connect()
            self._test()

    def __del__(self):
        if self.server:
            self.server.quit()

    def _connect(self):
        if self.tls:
            self.server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            self.server = smtplib.SMTP(self.host, self.port)
        self.server.set_debuglevel(self.debug)
        self.server.ehlo()
        if self.username and self.password:
            self.server.login(self.username, self.password)

    def _stay_connected(self):
        try:
            status = self.server.noop()[0]
        except:
            self._connect()

    def _send_mail(self, subject, text):
        message = MIMEMultipart('alternative')
        message['From'] = self.sender
        message['To'] = self.recipient
        message['Subject'] = subject
        message.attach(MIMEText(text, 'plain'))
        body = message.as_string()
        self._stay_connected()
        self.server.sendmail(self.sender, self.recipient, body)

    def _test(self):
        if self.enabled:
            log.info("Sending Test Mail")
            self._send_mail("TGTG Test Notification",
                            "This is a self test on startup. If you reveive this message you will recive notifications for your magic bags.")

    def send(self, item: Item):
        if self.enabled:
            log.info("Sending Mail Notification")
            self._send_mail(
                "New Magic Bags", f"{item.display_name} - New Amount: {item.items_available}")
