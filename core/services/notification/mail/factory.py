from core.services.notification.mail.smtp import SMTPMailBackend
from flask import current_app


def get_default_email_backend() -> SMTPMailBackend:
    """
    Creates a default SMTPMailBackend instance using Flask app configuration.
    """
    return SMTPMailBackend(
        smtp_server=current_app.config["EMAIL_HOST"],
        smtp_port=current_app.config["EMAIL_PORT"],
        username=current_app.config["EMAIL_USER"],
        password=current_app.config["EMAIL_PASS"],
    )
