import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPException, SMTPServerDisconnected

from models import Config, Item
from models.errors import MaskConfigurationError, SMTPConfigurationError
from notifiers.base import Notifier

log = logging.getLogger('tgtg')


class SMTP(Notifier):
    """
    Notifier for SMTP.
    """

    def __init__(self, config: Config):
        self.server = None
        self.debug = config.debug
        self.enabled = config.smtp.get("enabled", False)
        self.host = config.smtp.get("host")
        self.port = config.smtp.get("port", 25)
        self.tls = config.smtp.get("tls", False)
        self.ssl = config.smtp.get("ssl", False)
        self.username = config.smtp.get("username")
        self.password = config.smtp.get("password")
        self.sender = config.smtp.get("sender")
        self.recipient = config.smtp.get("recipient")
        self.subject = config.smtp.get("subject")
        self.body = config.smtp.get("body")
        self.cron = config.smtp.get("cron")
        if self.enabled and (not self.host or
                             not self.port or
                             not self.recipient):
            raise SMTPConfigurationError()
        if self.enabled:
            try:
                Item.check_mask(self.subject)
                Item.check_mask(self.body)
            except MaskConfigurationError as exc:
                raise SMTPConfigurationError(exc.message) from exc
            try:
                self._connect()
            except Exception as exc:
                raise SMTPConfigurationError(exc) from exc

    def __del__(self):
        """Closes SMTP connection when shutdown"""
        if self.server:
            try:
                self.server.quit()
            except Exception as exc:
                log.warning(exc)

    def _connect(self) -> None:
        """Connect to SMTP Server"""
        if self.ssl:
            self.server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            self.server = smtplib.SMTP(self.host, self.port)
        self.server.set_debuglevel(self.debug)
        if self.tls:
            self.server.starttls()
        self.server.ehlo()
        if self.username and self.password:
            self.server.login(self.username, self.password)

    def _stay_connected(self) -> None:
        """Refresh server connection if connection is lost"""
        try:
            status = self.server.noop()[0]
        except SMTPServerDisconnected:
            status = -1
        if status != 250:
            self._connect()

    def _send_mail(self, subject: str, html: str) -> None:
        """Sends mail with html body"""
        message = MIMEMultipart('alternative')
        message['From'] = self.sender
        message['To'] = ", ".join(self.recipient)
        message['Subject'] = subject
        message.attach(MIMEText(html, 'html'))
        body = message.as_string()
        self._stay_connected()
        try:
            self.server.sendmail(self.sender, self.recipient, body)
        except SMTPException:
            self._connect()
            self.server.sendmail(self.sender, self.recipient, body)

    def _send(self, item: Item) -> None:
        """Sends item information via Mail."""
        self._send_mail(
            item.unmask(self.subject),
            item.unmask(self.body)
        )

    def __repr__(self) -> str:
        return f"SMTP: {self.recipient}"
