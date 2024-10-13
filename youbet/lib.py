import random
import hashlib
import secrets
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


def generate_password():
    """Generate a random password of 5 characters"""
    result = ""
    options = list(range(48, 58)) + list(range(65, 91)) + list(range(97, 123))
    for i in range(5):
        result += chr(random.choice(options))
    return result


def generate_salt():
    """Generate a random salt."""
    return secrets.token_bytes(16)


def hash_password(password, salt=None):
    """Hash a password for storing."""
    if salt is None:
        salt = generate_salt()
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash, salt


def verify_password(stored_password, salt, provided_password):
    """Verify a stored password against one provided by user"""
    pwdhash = hash_password(provided_password, salt)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password
