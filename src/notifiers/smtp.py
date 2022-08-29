import logging
import smtplib
from smtplib import SMTPServerDisconnected, SMTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from models import Item, Config
from models.errors import SMTPConfigurationError, MaskConfigurationError

log = logging.getLogger('tgtg')


class SMTP():
    """
    Notifier for SMTP.
    """
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
        self.subject = config.smtp["subject"]
        self.body = config.smtp["body"]
        if self.enabled and (not self.host or not self.port):
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
                raise SMTPConfigurationError() from exc

    def __del__(self):
        """Closes SMTP connection when shutdown"""
        if self.server:
            try:
                self.server.quit()
            except Exception as exc:
                log.warning(exc)

    def _connect(self) -> None:
        """Connect to SMTP Server"""
        if self.tls:
            self.server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            self.server = smtplib.SMTP(self.host, self.port)
        self.server.set_debuglevel(self.debug)
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
        message['To'] = self.recipient
        message['Subject'] = subject
        message.attach(MIMEText(html, 'html'))
        body = message.as_string()
        self._stay_connected()
        try:
            self.server.sendmail(self.sender, self.recipient, body)
        except SMTPException:
            self._connect()
            self.server.sendmail(self.sender, self.recipient, body)

    def send(self, item: Item) -> None:
        """Sends item information via Mail."""
        if self.enabled:
            log.debug("Sending Mail Notification")
            self._send_mail(
                item.unmask(self.subject),
                item.unmask(self.body)
            )
