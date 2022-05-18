import re

from .custom_errors import BadRequest


def email_validation(email):
    # checks whether the email address is in correct format
    match = re.search(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', email, re.I)
    try:
        match.group()
    except:
        raise BadRequest('Please give a valid email address.')
    return True
