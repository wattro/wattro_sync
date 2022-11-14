import logging

import sendgrid
from sendgrid.helpers import mail

from wattro_sync.config_reader.types import MailCfg


class MailApi:
    def __init__(self, mail_cfg: MailCfg | None):
        if mail_cfg is None:
            self.dummy = True
            self.cfg = MailCfg("", "")
            return
        self.dummy = False
        self.cfg = mail_cfg
        self.sg = sendgrid.SendGridAPIClient(mail_cfg.api_key)

    def send_registered(self) -> bool:
        """returns True if mail was sent successfully."""
        msg = "E-Mail Logging für das Wattro Synchronisations Script wurde aktiviert."
        res = self._send(self._msg("Aktivierung erfolgreich.", msg))
        return res is not None

    def _msg(self, subject: str, html_content: str) -> mail.Mail:
        return mail.Mail(
            from_email=self.cfg.form_email,
            to_emails=self.cfg.to_emails,
            subject=subject,
            html_content=html_content,
        )

    def _send(self, message: mail.Mail) -> None | str:
        """try to send a mail, return None on fail"""
        if self.dummy:
            return None
        try:
            res = self.sg.send(message)
            return res.body.decode("utf-8")
        except Exception as err:
            logging.error(
                f"Sending of {message} failed: {err} | {getattr(err, 'message', '')}"
            )
            return None

    def send(self, log_lvl: int, msg: str) -> None:
        if self.dummy or log_lvl < self.cfg.log_level:
            logging.log(log_lvl, f"(sending mail skipped), {msg}")
            return
        self._send(
            self._msg(
                subject=f"Wattro Sync: {logging.getLevelName(log_lvl)}",
                html_content=msg,
            )
        )
