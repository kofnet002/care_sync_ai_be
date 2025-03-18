import json
import base64
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from django.contrib.auth.tokens import default_token_generator



class FlexibleTokenGenerator:
    # Define default expiry times in seconds
    DEFAULT_EXPIRY_TIMES = {
        'password_reset': timedelta(minutes=settings.PASSWORD_TOKEN_EXPIRATION_MINUTES),
        'email_verification': timedelta(minutes=settings.EMAIL_TOKEN_EXPIRATION_MINUTES),
        'api_access': timedelta(days=30),
        'invitation': timedelta(days=14),
        'temporary_access': timedelta(hours=1),
        'mobile_verification': timedelta(minutes=15),
    }

    def __init__(self, token_type=None, custom_expiry=None):
        self.token_generator = default_token_generator
        self.token_type = token_type
        self.custom_expiry = custom_expiry

    def get_expiry_time(self):
        """Get expiry time based on token type or custom duration"""
        now = timezone.now()
        
        if self.custom_expiry and isinstance(self.custom_expiry, timedelta):
            return now + self.custom_expiry
        elif self.token_type and self.token_type in self.DEFAULT_EXPIRY_TIMES:
            return now + self.DEFAULT_EXPIRY_TIMES[self.token_type]
        else:
            # Default fallback: 24 hours
            return now + timedelta(hours=24)

    def _encode_data(self, data):
        """Encode data dictionary to base64"""
        json_str = json.dumps(data, default=str)  # Handle datetime serialization
        return base64.urlsafe_b64encode(json_str.encode()).decode()

    def _decode_data(self, encoded_data):
        """Decode base64 data to dictionary"""
        try:
            json_str = base64.urlsafe_b64decode(encoded_data.encode()).decode()
            return json.loads(json_str)
        except Exception:
            return None

    def make_token(self, user, **extra_data):
        """Generate a token with metadata including expiry time and token type"""
        # Generate expiry timestamp
        expiry_time = self.get_expiry_time()
        
        # Generate the base token
        base_token = self.token_generator.make_token(user)
        
        # Prepare token metadata
        token_data = {
            'exp': expiry_time.isoformat(),
            'type': self.token_type,
            **extra_data
        }
        
        # Encode metadata
        encoded_data = self._encode_data(token_data)
        
        return f"{base_token}.{encoded_data}"

    def check_token(self, user, token, verify_type=True):
        """Check if the token is valid, not expired, and matches the expected type"""
        try:
            # Split token into base token and metadata
            base_token, encoded_data = token.split('.')
            
            # Decode metadata
            token_data = self._decode_data(encoded_data)
            if not token_data:
                return False
            
            # Check expiry
            expiry_time = datetime.fromisoformat(token_data['exp'])
            if timezone.now() > expiry_time:
                return False
            
            # Verify token type if requested
            if verify_type and token_data.get('type') != self.token_type:
                return False
            
            # Verify the base token
            return self.token_generator.check_token(user, base_token)
        except Exception as e:
            print(f"Token verification error: {str(e)}")  # For debugging
            return False

    @classmethod
    def for_password_reset(cls):
        return cls(token_type='password_reset')

    @classmethod
    def for_email_verification(cls):
        return cls(token_type='email_verification')

    @classmethod
    def for_api_access(cls):
        return cls(token_type='api_access')

    @classmethod
    def for_invitation(cls):
        return cls(token_type='invitation')

    @classmethod
    def for_mobile_verification(cls):
        return cls(token_type='mobile_verification')

    @classmethod
    def with_custom_expiry(cls, expiry_delta):
        if not isinstance(expiry_delta, timedelta):
            raise ValueError("expiry_delta must be a timedelta object")
        return cls(custom_expiry=expiry_delta)