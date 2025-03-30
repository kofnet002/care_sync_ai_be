from django.db import models
from django.utils import timezone
from apps.user.models import User  # Import the User model


class VideoConsultation(models.Model):
    PENDING = 'pending'
    ONGOING = 'ongoing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ONGOING, 'Ongoing'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]

    doctor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='doctor_video_consultations',
        limit_choices_to={'user_type': User.UserType.DOCTOR}  # Restrict to doctors
    )
    patient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='patient_video_consultations',
        limit_choices_to={'user_type': User.UserType.PATIENT}  # Restrict to patients
    )
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    room_name = models.CharField(max_length=255, unique=True)
    twilio_room_sid = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    duration = models.IntegerField(help_text='Duration in minutes', default=30)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-scheduled_time']

    def __str__(self):
        return f"Consultation: {self.doctor.get_username()} - {self.patient.get_username()} ({self.scheduled_time})"

    def is_active(self):
        return self.status == self.ONGOING

    def can_join(self):
        """Check if the consultation can be joined (15 minutes before scheduled time)"""
        now = timezone.now()
        time_before = self.scheduled_time - timezone.timedelta(minutes=15)
        time_after = self.scheduled_time + timezone.timedelta(minutes=self.duration)
        return time_before <= now <= time_after and self.status in [self.PENDING, self.ONGOING]
