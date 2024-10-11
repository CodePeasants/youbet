import random
import re
import hashlib
import secrets
import uuid
import binascii


def reset_password(user, db):
    new_password = generate_password()
    encrypted_password = hash_password(new_password)

    try:
        user.password = encrypted_password
        db.session.commit()
    except Exception as e:
        print(e)
        return False

    # TODO
    # success = send_password_reset_email(user.email, new_password)
    # if not success:
    #     return False
    return True

# FIXME - google no longer allows using username & password credentials
#  to login. We will have to use the google cloud APi to send this.
# def send_password_reset_email(email, new_password):
#     """Send an email to a user with their new password.

#     Args:
#         email (str): The email of the user to send the password to.
#         new_password (str): The new password to send to the user.

#     Returns:
#         bool: True on success, False on failure.
#     """
#     port = config["password_reset_sender_port"]
#     smtp_server = config["password_reset_sender_server"]
#     sender_email = config["password_reset_sender_email"]
#     sender_password = config["password_reset_sender_password"]

#     context = ssl.create_default_context()
#     with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
#         server.login(sender_email, sender_password)
#         subject = "YouBet - Password Reset"
#         body = f"Your new password is: {new_password}"
#         message = f"Subject: {subject}\n\n{body}"
#         server.sendmail(sender_email, email, message)
#     return True


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
    return amount * ratio


def coerce_str_to_bool(value):
    if value and value.lower() in {"true", "yes", "on", "1", "y"}:
        return True
    return False
