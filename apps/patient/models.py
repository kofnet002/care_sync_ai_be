from django.db import models
from apps.doctor.models import DoctorNote
from apps.user.models import User

# Create your models here.
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
    patient = models.ForeignKey(
        User,
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
    duration_days = models.IntegerField(default=0, blank=True)
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
    completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sequence_number = models.PositiveIntegerField()  # Track order of reminders
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sequence_number', 'scheduled_for']

    def __str__(self):
        return f"{self.title} - Day {self.sequence_number}"