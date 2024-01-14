import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPException, SMTPServerDisconnected
from typing import Union

from tgtg_scanner.errors import MaskConfigurationError, SMTPConfigurationError
from tgtg_scanner.models import Config, Favorites, Item, Reservations
from tgtg_scanner.models.reservations import Reservation
from tgtg_scanner.notifiers.base import Notifier

log = logging.getLogger("tgtg")


class SMTP(Notifier):
    """Notifier for SMTP"""

    def __init__(self, config: Config, reservations: Reservations, favorites: Favorites):
        super().__init__(config, reservations, favorites)
        self.server: Union[smtplib.SMTP, None] = None
        self.debug = config.debug
        self.enabled = config.smtp.enabled
        self.host = config.smtp.host
        self.port = config.smtp.port
        self.use_tls = config.smtp.use_tls
        self.use_ssl = config.smtp.use_ssl
        self.username = config.smtp.username
        self.password = config.smtp.password
        self.sender = config.smtp.sender
        self.recipients = config.smtp.recipients
        self.recipients_per_item = config.smtp.recipients_per_item
        self.subject = config.smtp.subject
        self.body = config.smtp.body
        self.cron = config.smtp.cron
        if self.enabled:
            if self.host is None or self.port is None or self.recipients is None:
                raise SMTPConfigurationError()
            try:
                Item.check_mask(self.subject)
                Item.check_mask(self.body)
            except MaskConfigurationError as exc:
                raise SMTPConfigurationError(exc.message) from exc
            try:
                self._connect()
            except Exception as exc:
                raise SMTPConfigurationError(exc) from exc
            if config.smtp.recipients_per_item is not None:
                item_recipients = None
                try:
                    item_recipients = json.loads(config.smtp.recipients_per_item)
                    if not isinstance(item_recipients, dict) or any(
                        not isinstance(value, (list, str)) for value in item_recipients.values()
                    ):
                        raise SMTPConfigurationError()
                # Catches both json.decoder.JSONDecodeError at json.loads()
                # and SMTPConfigurationError during key-value validation of item-recipients pairs inside
                except Exception:
                    raise SMTPConfigurationError("Recipients per Item is not a valid dictionary")
                self.item_recipients = item_recipients
            else:
                self.item_recipients = {}

    def __del__(self):
        """Closes SMTP connection when shutdown"""
        if self.server:
            try:
                self.server.quit()
            except Exception as exc:
                log.warning(exc)

    def _connect(self) -> None:
        """Connect to SMTP Server"""
        if self.host is None or self.port is None:
            raise SMTPConfigurationError()
        if self.use_ssl:
            self.server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            self.server = smtplib.SMTP(self.host, self.port)
        self.server.set_debuglevel(self.debug)
        if self.use_tls:
            self.server.starttls()
        self.server.ehlo()
        if self.username is not None and self.password is not None:
            self.server.login(self.username, self.password)

    def _stay_connected(self) -> None:
        """Refresh server connection if connection is lost"""
        status = -1
        if self.server is not None:
            try:
                status = self.server.noop()[0]
            except SMTPServerDisconnected:
                pass
        if status != 250:
            self._connect()

    def _send_mail(self, subject: str, html: str, item_id: int) -> None:
        """Sends mail with html body"""
        if self.server is None:
            self._connect()
        if self.sender is None or self.recipients is None or self.server is None:
            raise SMTPConfigurationError()
        message = MIMEMultipart("alternative")
        message["From"] = self.sender

        # Contains either the main recipient(s) or recipient(s) that should be
        # notified for the specific item. First, initalize with main recipient(s)
        recipients = self.recipients

        # Determine recipient(s) based on item_id
        if self.item_recipients:
            item = str(item_id)
            if item in self.item_recipients:
                # Find addresses based on item to be notified
                recipients = []
                recipients_for_item = self.item_recipients[item]
                if isinstance(recipients_for_item, list):
                    for address in recipients_for_item:
                        recipients.append(address)
                else:
                    address = recipients_for_item
                    recipients.append(address)

        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.attach(MIMEText(html, "html", "utf-8"))
        body = message.as_string()
        self._stay_connected()
        try:
            self.server.sendmail(self.sender, recipients, body)
        except SMTPException:
            self._connect()
            self.server.sendmail(self.sender, recipients, body)

    def _send(self, item: Union[Item, Reservation]) -> None:
        """Sends item information via Mail."""
        if isinstance(item, Item):
            self._send_mail(item.unmask(self.subject), item.unmask(self.body), item.item_id)

    def __repr__(self) -> str:
        return f"SMTP: {self.recipients}"
