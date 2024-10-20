import random
import re
import hashlib
import secrets
import binascii

from flask import request, url_for

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from youbet import settings


def reset_password(user, db):
    verification_code = generate_reset_code()
    
    try:
        user.password_reset_code = int(verification_code)
        user.password_reset_tries += 1
        db.session.commit()
    except Exception as e:
        print(e)
        return False

    response = send_email(
        from_address=settings.RESET_PASSWORD_SENDER_ADDRESS,
        to_addresses=user.email,
        subject="YouBet Password Reset",
        html_content=f"<a>Your verification code is:</a><br><h1>{verification_code}</h1>"
    )
    if not response:
        return False
    return True


def send_email(from_address, to_addresses, subject, body=None, html_content=None):
    message = Mail(
        from_email=from_address,
        to_emails=to_addresses,
        subject=subject,
        plain_text_content=body,
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        return response
    except Exception as e:
        print(e)


def generate_reset_code():
    return "".join([str(random.randint(0, 9)) for _ in range(6)])


def generate_password(length=5):
    """Generate a random password of 5 characters"""
    result = ""
    options = list(range(48, 58)) + list(range(65, 91)) + list(range(97, 123))
    for i in range(length):
        result += chr(random.choice(options))
    return result


def generate_salt():
    """Generate a random salt."""
    return binascii.hexlify(secrets.token_bytes(16))


def hash_password(password, salt=None, as_str=False):
    """Hash a password for storing."""
    if salt is None:
        salt = generate_salt()
    else:
        salt = coerce_to_bytes(salt)
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    if as_str:
        pwdhash = coerce_to_str(pwdhash)
        salt = coerce_to_str(salt)
    return pwdhash, salt


def validate_password(password):
    """Check if a password is valid."""
    valid_range = set(range(48, 123))
    if any([ord(x) not in valid_range for x in password]):
        return False
    return True


def verify_password(stored_password, salt, provided_password):
    """Verify a stored password against one provided by user"""
    pwdhash, salt = hash_password(provided_password, str_to_bytes(salt))
    return pwdhash == str_to_bytes(stored_password)


def bytes_to_str(data):
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError as e:
        raise Exception(f"Could not decode {data} of type: {type(data)} from bytes to str. Originall error: {e}")


def str_to_bytes(data):
    return data.encode('utf-8')


def coerce_to_bytes(data):
    if isinstance(data, str):
        return str_to_bytes(data)
    return data


def coerce_to_str(data):
    if isinstance(data, bytes):
        return bytes_to_str(data)
    return data


def validate_odds(odds):
    if not isinstance(odds, str):
        return False
    if not re.match(r"^\d+(\.\d+)?:\d+(\.\d+)?$", odds):
        return False 
    return True


def solve_odds(odds, amount, reverse_odds=False):
    tokens = odds.split(":")
    if reverse_odds:
        tokens.reverse()
    ratio = float(tokens[0]) / float(tokens[1])
    return round(amount * ratio, 2)


def coerce_str_to_bool(value):
    if value and value.lower() in {"true", "yes", "on", "1", "y"}:
        return True
    return False


def get_redirect_url(default="main"):
    return request.args.get("next") or \
        request.form.get("referrer") or \
        request.referrer or \
        url_for(default)