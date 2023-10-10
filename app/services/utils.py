import re

from .custom_errors import BadRequest


def email_validation(email: str) -> bool:
    # checks whether the email formats are in proper format or not
    match = re.search(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', email, re.I)
    if match:
        return True
    raise BadRequest("Please give a valid email address.")
