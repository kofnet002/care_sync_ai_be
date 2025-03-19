from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager, PermissionsMixin


# Create your models here.
class CustomUserManager(BaseUserManager):
    """custom user manager class"""
    use_in_migration = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The email is required.')
        
        email =  str(email).strip()
        username = str(email).split('@')[0]
        email = self.normalize_email(email)
        user_type = extra_fields.pop('user_type', User.UserType.DOCTOR)
        user = self.model(username=username, email=email, user_type=user_type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        username =  str(username).strip()
        return self._create_user(username, email, password, **extra_fields)

class User(AbstractUser, PermissionsMixin):
    class UserType(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        DOCTOR = 'DOCTOR', 'Doctor'

      
    email           = models.EmailField(_('Email'), null=False, blank=False, max_length=120, unique=True)
    user_type       = models.CharField(_('User Type'), max_length=150, choices=UserType.choices, default=UserType.PATIENT)
    username       = models.CharField(_('Username'), max_length=150, null=True, blank=True)
    is_active       = models.BooleanField(_('Active'), default=False, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.")
    is_admin        = models.BooleanField(_('Employee'),default=False, help_text="Designates whether the user should be treated as an employee.")
    is_staff        = models.BooleanField(_('Backend Access'), default=False, help_text="Designates whether the user can log into this admin site.")
    is_superuser    = models.BooleanField(_('Superuser'), default=False, help_text="Designates that this user has all permissions without explicitly assigning themodels.")
    last_login      = models.DateTimeField(_('last_login'), auto_now=True)
    date_joined     = models.DateTimeField(auto_now_add=True, null=True)

    objects         = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username'
    ]

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
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
        