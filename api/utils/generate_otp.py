import pyotp
from apps.user.models import UserOTP


def generate_otp_secret(user):
    """Generates and saves a TOTP secret for the specified user."""
    otp_secret = pyotp.random_base32()  # Generate a random OTP secret
    UserOTP.objects.update_or_create(user=user, defaults={'otp_secret': otp_secret})
    return otp_secret


def generate_numeric_otp(user, interval_in_mins: int):
    """Generates a 6-digit numeric OTP for the specified user with a custom interval."""
    try:
        user_otp = UserOTP.objects.get(user=user)
        totp = pyotp.TOTP(user_otp.otp_secret, interval=interval_in_mins*60)  # Set custom interval
        return totp.now()  # Generates a new OTP based on the secret
    except UserOTP.DoesNotExist:
        return None


def verify_numeric_otp(user, otp_code, interval_in_mins: int):
    """Verifies the numeric OTP code against the user's stored secret."""
    try:
        user_otp = UserOTP.objects.get(user=user)
        totp = pyotp.TOTP(user_otp.otp_secret, interval=interval_in_mins*60)
        return totp.verify(otp_code)  # Check if the OTP matches
    except UserOTP.DoesNotExist:
        print('No OTP Code Exists!')
        return False

