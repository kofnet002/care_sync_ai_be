from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager, PermissionsMixin
from api.utils.encryption import NoteEncryption
from django.utils import timezone

# Create your models here.
class CustomUserManager(BaseUserManager):
    """Custom user manager for handling user creation and management"""
    use_in_migration = True

    def _create_user(self, email, password, **extra_fields):
        """
        Base method to create and save a User with email and password.
        """
        if not email:
            raise ValueError('Email is required')

        # Set username to email if not provided
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        
        email = self.normalize_email(str(email).strip())
        
        user_type = extra_fields.pop('user_type', User.UserType.DOCTOR)
        extra_fields.setdefault('is_active', True)
        
        user = self.model(
            email=email, 
            user_type=user_type,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.update({
            'is_active': True,
            'is_admin': True, 
            'is_staff': True,
            'user_type': User.UserType.DOCTOR,
            'email_verified': True,
            'is_superuser': True
        })

        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser, PermissionsMixin):
    class UserType(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        DOCTOR = 'DOCTOR', 'Doctor'

    public_key = models.BinaryField(null=True)
    private_key = models.BinaryField(null=True)
    
    email = models.EmailField(_('Email'), null=False, blank=False, max_length=120, unique=True)
    user_type = models.CharField(_('User Type'), max_length=150, choices=UserType.choices, default=UserType.PATIENT)
    username = models.CharField(_('Username'), max_length=150, null=True, blank=True)
    email_verified  = models.BooleanField(_('Email Verified'), default=False)
    
    otp = models.CharField(max_length=6, blank=True, null=True, editable=False)
    otp_created_at  = models.DateTimeField(null=True, blank=True, editable=False)
    
    is_active = models.BooleanField(_('Active'), default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.")
    is_admin = models.BooleanField(_('Employee'),default=False, help_text="Designates whether the user should be treated as an employee.")
    is_staff = models.BooleanField(_('Backend Access'), default=False, help_text="Designates whether the user can log into this admin site.")
    is_superuser = models.BooleanField(_('Superuser'), default=False, help_text="Designates that this user has all permissions without explicitly assigning themodels.")
    last_login = models.DateTimeField(_('last_login'), auto_now=True)
    date_joined = models.DateTimeField(auto_now_add=True, null=True)

    objects         = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username'
    ]

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        
    def set_otp(self, otp):
        self.otp = otp
        self.otp_created_at = timezone.now()  # Use timezone-aware datetime
        self.save()
    
    @property
    def get_name_from_email(self):
        """Extract name from email address before the @ symbol"""
        if self.email:
            return self.email.split('@')[0].replace('.', ' ').title()
        return self.username

    @property 
    def full_name(self):
        if not self.first_name and not self.last_name:
            return self.get_name_from_email
        return f"{self.first_name} {self.last_name}".strip().title()
    
    def generate_encryption_keys(self):
        """Generate and store encryption keys for the user"""
        if not self.public_key or not self.private_key:
            private_pem, public_pem = NoteEncryption.generate_key_pair()
            self.private_key = private_pem
            self.public_key = public_pem
            self.save()
        return self.public_key, self.private_key
    
    
class UserOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_secret = models.CharField(max_length=64, unique=True, editable=False)

    def __str__(self):
        return f"{self.user.username}'s OTP"

    class Meta:
        verbose_name = _("User OTP")
        verbose_name_plural = _("Users OTP")