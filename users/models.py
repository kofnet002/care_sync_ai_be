from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.

class User(AbstractUser):
    class UserType(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        DOCTOR = 'DOCTOR', 'Doctor'
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.PATIENT
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class DoctorPatient(models.Model):
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_patients',
        limit_choices_to={'user_type': User.UserType.DOCTOR}
    )
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='patient_doctors',
        limit_choices_to={'user_type': User.UserType.PATIENT}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('doctor', 'patient')
        ordering = ['-created_at']

    def __str__(self):
        return f"Dr. {self.doctor.full_name} - {self.patient.full_name}"

class DoctorNote(models.Model):
    doctor_patient = models.ForeignKey(
        DoctorPatient,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.doctor_patient.doctor != self.doctor_patient.doctor:
            raise ValidationError("Doctor can only add notes for their patients")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.doctor_patient.patient.full_name} by Dr. {self.doctor_patient.doctor.full_name}"

class ChecklistItem(models.Model):
    note = models.ForeignKey(
        DoctorNote,
        on_delete=models.CASCADE,
        related_name='checklist_items'
    )
    task = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.task

class ActionPlan(models.Model):
    class Frequency(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'
        CUSTOM = 'CUSTOM', 'Custom'

    note = models.ForeignKey(
        DoctorNote,
        on_delete=models.CASCADE,
        related_name='action_plans'
    )
    action = models.CharField(max_length=255)
    frequency = models.CharField(
        max_length=10,
        choices=Frequency.choices,
        default=Frequency.DAILY
    )
    start_date = models.DateField()
    end_date = models.DateField()
    custom_schedule = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date', 'created_at']

    def __str__(self):
        return f"{self.action} ({self.frequency})"

class Reminder(models.Model):
    action_plan = models.ForeignKey(
        'ActionPlan',
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_for = models.DateTimeField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_for']

    def __str__(self):
        return f"{self.title} - {self.scheduled_for}"