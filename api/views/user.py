from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from api.serilizers.user import (
    UserRegistrationSerializer, 
)
from drf_spectacular.utils import extend_schema, OpenApiResponse
from api.utils.renderers import LoginRenderer
from rest_framework.permissions import AllowAny
from django.utils import timezone
from api.serilizers.user import UserLoginSerializer


# Create your views here.
class UserRegistrationView(APIView):
    @extend_schema(
        request={'multipart/form-data': UserRegistrationSerializer, 'required': ['email', 'password', 'user_type']},
        responses={
            201: UserRegistrationSerializer,
            400: OpenApiResponse(description='Invalid data provided')
        },
        description="Register a new user (Patient or Doctor)",
        tags=["Authentication"],
        operation_id='auth_register',
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@extend_schema(
    tags=['Authentication'],
    description='Login with email and password to obtain JWT tokens',
    request={'multipart/form-data': {
        'type': 'object',
        'properties': {
            'email': {'type': 'string'},
            'password': {'type': 'string'}
        },
        'required': ['email', 'password']
    }},
    responses={
        200: OpenApiResponse(description='Login successful, returns access and refresh tokens'),
        401: OpenApiResponse(description='Invalid credentials')
    },
    operation_id='auth_login'
)

class LoginView(BaseTokenObtainPairView):
    serializer_class = UserLoginSerializer
    renderer_classes = [LoginRenderer]
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # If login was successful, update last_login
        if response.status_code == 200:
            # The user will be available in the serializer
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            
            # Update last_login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
        
        return response
class TokenRefreshView(BaseTokenRefreshView):
    @extend_schema(
        tags=['Authentication'],
        description='Refresh access token using refresh token',
        request={'multipart/form-data': {
            'type': 'object',
            'properties': {
                'refresh_token': {'type': 'string'}
            },
            'required': ['refresh_token']
        }},
        responses={
            200: OpenApiResponse(description='Token refresh successful, returns new access token'),
            401: OpenApiResponse(description='Invalid refresh token')
        },
        operation_id='auth_refresh'
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['Authentication'],
        description='Logout by blacklisting the refresh token',
        request={'multipart/form-data': {
            'type': 'object',
            'properties': {
                'refresh_token': {'type': 'string'}
            },
            'required': ['refresh_token']
        }},
        responses={
            200: OpenApiResponse(description='Successfully logged out'),
            401: OpenApiResponse(description='Invalid token or unauthorized')
        },
        operation_id='auth_logout'
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)
