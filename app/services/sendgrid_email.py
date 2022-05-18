from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .custom_errors import UnProcessable
from config import Config_is


def send_email(**kwargs):
    try:
        message = Mail(from_email=Config_is.SENDGRID_EMAIL_ADDRESS, to_emails=kwargs.get("to_email"),
                       subject=kwargs.get("subject"), html_content=kwargs.get("html_content"))
        sg = SendGridAPIClient(Config_is.SENDGRID_API_KEY)
        return sg.send(message)
    except Exception as e:
        print(e)
        raise UnProcessable(e)
