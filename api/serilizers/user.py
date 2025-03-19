from rest_framework import serializers
from apps.user.models import User
from rest_framework_simplejwt.serializers import PasswordField, TokenObtainPairSerializer

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'username', 'user_type']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.username = validated_data['email']  # Using email as username
        user.save()
        return user 

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
