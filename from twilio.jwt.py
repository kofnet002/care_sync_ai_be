from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from django.conf import settings

def generate_twilio_token(identity, room_name):
    # Ensure correct values are used
    account_sid = settings.TWILIO_ACCOUNT_SID  # Must start with "AC..."
    api_key = settings.TWILIO_API_KEY  # Must start with "SK..."
    api_secret = settings.TWILIO_API_SECRET  # Your API secret

    if not (account_sid and api_key and api_secret):
        raise ValueError("Missing Twilio credentials in settings")

    token = AccessToken(account_sid, api_key, api_secret, identity=identity)
    video_grant = VideoGrant(room=room_name)
    token.add_grant(video_grant)

    return token.to_jwt()

generate_twilio_token(1, 'consultation-20a92b1d-e577-49c4-9623-1280ec8f365a')