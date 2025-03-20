from django.db import models
from django.core.exceptions import ValidationError
from apps.user.models import User
from api.utils.encryption import NoteEncryption
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
    content =  models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.doctor_patient.doctor != self.doctor_patient.doctor:
            raise ValidationError("Doctor can only add notes for their patients")

    def encrypt_note(self, raw_content: str):
        """Encrypt note content for both doctor and patient"""
        doctor = self.doctor_patient.doctor
        patient = self.doctor_patient.patient
                
        # Ensure both users have encryption keys
        doctor.generate_encryption_keys()
        patient.generate_encryption_keys()
        
        # Encrypt for doctor
        doctor_encrypted = NoteEncryption.encrypt_note(
            raw_content, 
            doctor.public_key
        )
        
        # Encrypt for patient
        patient_encrypted = NoteEncryption.encrypt_note(
            raw_content, 
            patient.public_key
        )
        
        self.content = {
            'doctor': doctor_encrypted,
            'patient': patient_encrypted
        }
        self.save()
    
    def decrypt_note(self, user: User) -> str:
        """Decrypt note content for authorized user"""
        if user not in [self.doctor_patient.doctor, self.doctor_patient.patient]:
            raise PermissionError("Unauthorized access to note")

        user_type = 'doctor' if user.user_type == User.UserType.DOCTOR else 'patient'
        
        try:
            encrypted_data = self.content.get(user_type)
            if not encrypted_data:
                raise ValueError(f"No encrypted data found for {user_type}")
                
            return NoteEncryption.decrypt_note(encrypted_data, user.private_key)
        except Exception as e:
            print(f"Decryption error: {str(e)}")
            raise
    
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