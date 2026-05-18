import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.services.notification.mail.base import BaseMail


class SMTPMailBackend(BaseMail):
    """
    A concrete email backend that uses SMTP to send emails via a configured server.
    """
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, use_tls: bool = True):
        """
        Initialize the SMTP backend with server settings and credentials.
        """
        super().__init__(from_email=username)
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    def send(self, to_email: str):
        """
        Sends the prepared email to the given recipient via SMTP.
        """
        msg = MIMEMultipart()
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = self.subject

        msg.attach(MIMEText(self.body, "plain"))

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.from_email, to_email, msg.as_string())
