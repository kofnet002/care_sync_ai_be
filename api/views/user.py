from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from api.serilizers.user import (
    UserRegistrationSerializer, 
)
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from api.utils.renderers import LoginRenderer
from django.utils import timezone
from api.serilizers.user import UserLoginSerializer
from api.utils.generate_otp import verify_numeric_otp
from core import settings
from apps.user.models import User
from api.serilizers.user import OtpCodeSerializer, UserSerializer, EmailSerializer, PasswordResetSerializer, ResetPasswordUpdateSerializer
from apps.user.tasks import send_otp_code_email, verify_account_email, reset_password_email
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from api.utils.permissions import IsEmailVerified
from api.serilizers.user import PasswordUpdateSerializer
from api.utils.tokens import FlexibleTokenGenerator
from django.utils.http import urlsafe_base64_decode
from core.celery import app 




# Create your views here.
@extend_schema_view(post=extend_schema(
    summary      = 'Register Superuser',
    description  = 'Register superuser.',
    methods      = ['post'],
    operation_id = 'superUserRegister',
    tags         = ["Authentication"],
))
class SuperUserRegistrationView(APIView):
    serializer_class = UserRegistrationSerializer
    user_serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        ser = self.serializer_class(data=request.data)
        
        if ser.is_valid(raise_exception= True):
            user = ser.save()
            password = request.data["password"]

            user.set_password(password)
            user.is_active = True
            user.is_superuser = True
            user.is_staff = True
            user.user_type = User.UserType.DOCTOR
            user.email_verified = True
            user.save()
            
            data = {}
            refresh = RefreshToken.for_user(user)
            
            refresh['username'] = user.username
            refresh['email'] = user.email
            refresh['email_verified'] = user.email_verified

            data['user'] = self.user_serializer_class(user).data
            data['credentials'] = {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
            return Response(data, status=status.HTTP_201_CREATED)
        return Response({'detail': 'invalid_data'}, status=status.HTTP_400_BAD_REQUEST)
    
@extend_schema_view(post=extend_schema(
    summary      = 'Register User',
    description  = 'Register user.',
    methods      = ['post'],
    operation_id = 'userRegister',
    tags         = ["Authentication"],
))
class UserRegistrationView(APIView):
    # TODO: Add rate limiting
    
    serializer_class = UserRegistrationSerializer
    user_serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        ser = self.serializer_class(data=request.data)
        
        if ser.is_valid(raise_exception= True):
            user = ser.save()
            password = request.data["password"]

            user.set_password(password)
            user.is_active = True
            user.save()

            interval = settings.EMAIL_TOKEN_EXPIRATION_MINUTES
            
            # Queue Verification Mail
            result = app.send_task(
                    'verify_account_email',
                    args=[{'pk': user.pk}],
                )
            print(f"Successfully scheduled reminder: {result}")
            # verify_account_email.delay({'pk': user.pk})

            data = {}
            refresh = RefreshToken.for_user(user)
            
            refresh['username'] = user.username
            refresh['email'] = user.email
            refresh['email_verified'] = user.email_verified

            data['user'] = self.user_serializer_class(user).data
            data['credentials'] = {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
            data['otp_eta_in_minutes'] = int(interval)
            return Response(data, status=status.HTTP_201_CREATED)
        return Response({'detail': 'invalid_data'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(post=extend_schema(
    summary      = 'User Sign In',
    description  = 'User sign in.',
    methods      = ['post'],
    operation_id = 'authLogin',
    tags         = ["Authentication"],
))
class LoginView(BaseTokenObtainPairView):
    # TODO: Add rate limiting
    
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

@extend_schema_view(post=extend_schema(
    summary      = 'Token Refresh',
    description  = 'Get a new Access Token using a Refresh Token.',
    methods      = ['post'],
    operation_id = 'authTokenRefresh',
    tags         = ["Authentication"],
))
class TokenRefreshView(BaseTokenRefreshView):
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

@extend_schema_view(post=extend_schema(
    summary      = 'Logout',
    description  = 'Logout by blacklisting the refresh token.',
    methods      = ['post'],
    operation_id = 'authLogout',
    tags         = ["Authentication"],
))
class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
              # Blacklist all refresh tokens for the user
            refresh_tokens = OutstandingToken.objects.filter(user=request.user, blacklistedtoken__isnull=True)

            for token in refresh_tokens:
                BlacklistedToken.objects.create(token=token)
                
            # refresh_token = request.data["refresh_token"]
            # token = RefreshToken(refresh_token)
            # token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(post=extend_schema(
    summary      = 'Email Verification - Complete Verification',
    description  = 'Set user email verified status to true.',
    methods      = ['post'],
    operation_id = 'emailVerificationConfirm',
    tags         = ["Authentication"],
))
class EmailVerificationConfirmAPIView(APIView):
    serializer_class = OtpCodeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            otp = request.data.get('otp_code')
            ser = self.serializer_class(data=request.data)

            if request.user.email_verified:
                return Response({'detail': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)

            # Verify that user exists
            if ser.is_valid(raise_exception=True):
                user = request.user
                interval = settings.EMAIL_TOKEN_EXPIRATION_MINUTES

                if verify_numeric_otp(user, otp_code=otp, interval_in_mins=interval):
                    user.email_verified = True
                    user.save()
                    
                    serializer = UserSerializer(user)

                    data = {}
                    refresh = RefreshToken.for_user(user)
                    
                    # Add extra fields to the refresh token
                    refresh['username'] = user.username
                    refresh['email'] = user.email
                    refresh['email_verified'] = user.email_verified

                    data['user'] = serializer.data
                    data['credentials'] = {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {'detail': 'OTP returned is invalid or has expired'}, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response({'detail': 'Please provide an email address'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, KeyError, User.DoesNotExist):
            return Response({'detail': 'Invalid Details'}, status=status.HTTP_400_BAD_REQUEST)
        
@extend_schema_view(post=extend_schema(
    summary      = 'Email Verification - Request Verification',
    description  = 'Sends a one-time 6 digits code to the email of logged in user if email not verified',
    methods      = ['post'],
    operation_id = 'emailVerificationRequest',
    tags         = ["Authentication"],
))
class EmailVerificationRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            if user.email_verified:
                return Response({'detail': 'Email already verified'}, status=status.HTTP_400_BAD_REQUEST)
            
            interval = settings.EMAIL_TOKEN_EXPIRATION_MINUTES

            # Queue Send OTP Mail
            app.send_task(
                    'send_otp_code_email',
                    args=[{'pk': user.pk}],
                )
            # send_otp_code_email.delay({'pk': user.pk})
            
            data = {'token_eta_in_minutes': int(interval)}

            return Response(data, status=status.HTTP_201_CREATED)
        except (ValueError, KeyError, User.DoesNotExist):
            return Response({'detail': 'Invalid Details'}, status=status.HTTP_400_BAD_REQUEST)
        
@extend_schema_view(post=extend_schema(
    summary      = 'Update Password - Token Request',
    description  = 'Create a one-time 6 digits access token and send to the authenticated member’s email address.',
    methods      = ['post'],
    operation_id = 'updatePasswordTokenRequest',
    tags         = ["Authentication"],
))
class UpdatePasswordTokenRequest(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user

            interval = settings.PASSWORD_TOKEN_EXPIRATION_MINUTES

            # Send OTP code Email
            send_otp_code_email.delay({
                'pk':user.id,
                'interval': interval
            })

            return Response({'token_expiration_in_minutes': int(interval)}, status=status.HTTP_200_OK)
        except (ValueError, KeyError):
            return Response({'detail': 'You need to be logged in to perform this action'}, status=status.HTTP_400_BAD_REQUEST)
        
@extend_schema_view(post=extend_schema(
    summary      = 'Update Password - Verify Access Token',
    description  = 'Verify the validity of the submitted token.',
    methods      = ['post'],
    operation_id = 'updatePasswordVerifyToken',
    tags         = ["Authentication"],
))
class UpdatePasswordVerifyAccessToken(APIView):
    serializer_class = OtpCodeSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request, *args, **kwargs):
        otp = request.data.get('otp_code')
        
        ser = self.serializer_class(data=request.data)

        if ser.is_valid(raise_exception=True):
            user = self.request.user
            interval = settings.PASSWORD_TOKEN_EXPIRATION_MINUTES

            if verify_numeric_otp(user, otp_code=otp, interval_in_mins=interval):
                return Response({},status=status.HTTP_200_OK,)
            else:
                return Response(
                    {'detail': 'OTP returned is invalid or has expired'}, status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response({'detail': 'Please Provide the otp code'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(post=extend_schema(
    summary      = 'Update Password - Complete Update',
    description  = "Update user's password to the incoming one.",
    methods      = ['post'],
    operation_id = 'updatePasswordComplete',
    tags         = ["Authentication"],
))
class UpdatePasswordCompleteUpdate(APIView):
    serializer_class = PasswordUpdateSerializer
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request, *args, **kwargs):
        otp      = request.data.get('token')
        email    = request.data.get('email')
        password = request.data.get('new_password')

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = request.user

            user_by_email = User.objects.filter(email=email).first()

            if not user_by_email:
                return Response({'detail': 'Invalid Details'}, status=status.HTTP_400_BAD_REQUEST)

            if user != user_by_email:
                return Response({'detail': 'Please provide your own email address'}, status=status.HTTP_400_BAD_REQUEST)

            interval = settings.PASSWORD_TOKEN_EXPIRATION_MINUTES

            if verify_numeric_otp(user, otp_code=otp, interval_in_mins=interval):
                user.set_password(password)
                user.save()

                serializer = UserSerializer(user)
                data = {
                    'user':serializer.data
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'detail': 'OTP returned is invalid or has expired'}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response({'detail': 'Please provide a password'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(post=extend_schema(
    summary      = 'Forget Password - Token Request',
    description  = "Create a one-time verification token link and send to email address.",
    methods      = ['post'],
    operation_id = 'forgetPasswordTokenRequest',
    tags         = ["Authentication"],
))
class ForgetPasswordTokenRequest(APIView):
    serializer_class = EmailSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            email = request.data['email']
            
            ser = self.serializer_class(data=request.data)

            if ser.is_valid(raise_exception=True):
                user = User.objects.filter(email=email).first()
                if not user:
                    return Response({'detail': 'Invalid Details'}, status=status.HTTP_400_BAD_REQUEST)

                interval = settings.EMAIL_TOKEN_EXPIRATION_MINUTES

                # RESET PASSWORD EMAIL
                app.send_task(
                    'reset_password_email',
                    args=[{'pk': user.pk}],
                )
                # reset_password_email.delay({'pk': user.pk})

                return Response({'token_expiration_in_minutes': int(interval)}, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Please provide an email address'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, KeyError):
            return Response({'detail': 'Please provide an Email Address'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(post=extend_schema(
    summary      = 'Forget Password - Verify Token',
    description  = "Verify the one-time token sent to user's email address.",
    methods      = ['post'],
    operation_id = 'forgetPasswordVerifyToken',
    tags         = ["Authentication"],
))
class ForgetPasswordVerifyAccessToken(APIView):
    serializer_class = PasswordResetSerializer
    permission_classes = [AllowAny]


    def post(self, request, *args, **kwargs):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        eid = request.data.get('eid')
        
        ser = self.serializer_class(data=request.data)

        if ser.is_valid(raise_exception=True):
            try:
                uid = urlsafe_base64_decode(uidb64).decode()
                user = User._default_manager.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
                user = None

            token_generator = FlexibleTokenGenerator.for_password_reset()

            if user is not None and token_generator.check_token(user, token):
                try:
                    email = urlsafe_base64_decode(eid).decode()
                except Exception as e:
                    email= None
                    return Response({'detail': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)

                if user.email != email:
                    return Response({'detail': 'Wrong email provided for token'}, status=status.HTTP_400_BAD_REQUEST)
                return Response({},status=status.HTTP_200_OK,)
            else:
                return Response({'detail': 'Token is invalid or has expired'}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'detail': 'Invalid Data'}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema_view(post=extend_schema(
    summary      = 'Forget Password - Complete Reset',
    description  = "Reset user's password to the incoming one.",
    methods      = ['post'],
    operation_id = 'forgetPasswordComplete',
    tags         = ["Authentication"],
))
class ForgetPasswordCompleteReset(APIView):
    serializer_class = ResetPasswordUpdateSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        token    = request.data.get('token')
        eid      = request.data.get('eid')
        password = request.data.get('new_password')

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                email = urlsafe_base64_decode(eid).decode()
            except Exception as e:
                email= None
                return Response({'detail': 'Invalid email'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()

            if user is None:
                return Response(
                    {'detail': 'Email not found'}, status=status.HTTP_400_BAD_REQUEST
                )
            token_generator = FlexibleTokenGenerator.for_password_reset()

            if token_generator.check_token(user, token):                
                user.set_password(password)
                user.save()
                return Response({}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'detail': 'Token is invalid or has expired'}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response({'detail': 'Please provide a password'}, status=status.HTTP_400_BAD_REQUEST)



