from rest_framework import serializers
from apps.user.models import User
from rest_framework_simplejwt.serializers import PasswordField, TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=255, required=True, style={"input_type": "password"}, write_only=True)    
    class Meta:
        model = User
        fields = ['email', 'password', 'username', 'user_type']
    
    def validate(self, attrs):
        """Validation for password."""
        try:
            validate_password(attrs["password"])
        except ValidationError as e:
            raise serializers.ValidationError({'detail': str(e)})
        return attrs
    
    def create(self, validated_data):
        # Set username from the email
        validated_data['username'] = validated_data['email'].split('@')[0]
        return super().create(validated_data)

class UserLoginSerializer(TokenObtainPairSerializer):
    """Login serializer for user"""

    def __init__(self, *args, **kwargs):
        """Overriding to change the error messages."""
        super(UserLoginSerializer, self).__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField(
            error_messages={"blank": "Looks like you submitted wrong data. Please check and try again"}
        )
        self.fields['password'] = PasswordField(
            error_messages={"blank": "Looks like you submitted wrong data. Please check and try again"}
        )

    def validate(self, attrs):
        """Overriding to add user to responses"""
        token_data = super().validate(attrs)

        data = {}
        data['tokens'] = {
            **token_data
        }
        return data

    # @classmethod
    # def get_token(cls, user):
    #     token = super().get_token(user)
    #     # Add custom claims to the token
    #     token['username'] = user.username
    #     token['email'] = user.email
    #     # Add more fields as needed
    #     return token

class OtpCodeSerializer(serializers.Serializer):
    otp_code = serializers.CharField(required=True)
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username','full_name', 'user_type', 'is_active', 'email_verified']

class EmailSerializer(serializers.Serializer):
    email   = serializers.EmailField(required=True)
    
class TokenSerializer(serializers.Serializer):
    token   = serializers.CharField(required=True)
    
class PasswordUpdateSerializer(EmailSerializer, TokenSerializer):
    new_password = serializers.CharField(required=True, max_length=128, min_length=8)

class EmailSerializer(serializers.Serializer):
    email   = serializers.EmailField(required=True)

class HashedEmailIDSerializer(serializers.Serializer):
    eid = serializers.CharField(required=True)
    
class PasswordResetSerializer(HashedEmailIDSerializer,TokenSerializer):
    uid = serializers.CharField(required=True)

class ResetPasswordUpdateSerializer(HashedEmailIDSerializer, TokenSerializer):
    new_password = serializers.CharField(required=True, max_length=128, min_length=8)
