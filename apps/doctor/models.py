from django.db import models
from django.core.exceptions import ValidationError
from apps.user.models import User

# Create your models here.
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