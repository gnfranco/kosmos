import secrets
import string

from django.core.mail import send_mail
from django.utils.translation import gettext as _


def generate_verification_code():
    """Generate a random 6-digit verification code."""
    return "".join(secrets.choice(string.digits) for _ in range(6))


def send_verification_email(user, code):
    """Send verification code to user's email."""
    send_mail(
        subject=_("Your Login Verification Code"),
        message=_("Your verification code is: %(code)s\n\nThis code expires in 5 minutes.") % {"code": code},
        from_email=None,  # Uses DEFAULT_FROM_EMAIL
        recipient_list=[user.email],
    )
