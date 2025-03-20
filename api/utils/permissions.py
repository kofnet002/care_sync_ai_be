from rest_framework import permissions
from apps.user.models import User
from apps.doctor.models import DoctorPatient

class IsEmailVerified(permissions.BasePermission):
    message = "Email verification is required to access this resource."

    def has_permission(self, request, view):
        # Check if the user is authenticated and their email is verified.
        return request.user.is_authenticated and request.user.email_verified
    
class IsDoctor(permissions.BasePermission):
    message = "Only doctors can view this resource."

    def has_permission(self, request, view):
        # Check if user is authenticated first
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Superuser has access to all permissions
        if request.user.is_superuser:
            return True
            
        # Check if the user is a doctor
        return request.user.user_type == User.UserType.DOCTOR

class IsPatient(permissions.BasePermission):
    message = "Only patients can view this resource."

    def has_permission(self, request, view):
        # Check if user is authenticated first
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Superuser has access to all permissions
        if request.user.is_superuser:
            return True
            
        # Check if the user is a patient
        return request.user.user_type == User.UserType.PATIENT

class IsAuthenticated(permissions.BasePermission):
    message = "You must be authenticated to view this resource."

    def has_permission(self, request, view):
        # Superuser has access to all permissions
        if request.user.is_superuser:
            return True
        # Check if the user is authenticated.
        return request.user.is_authenticated

class DoctorPatientPermission(permissions.BasePermission):
    message = "You do not have permission to view this patient's details."

    def has_permission(self, request, view):
        # Superuser has access to all permissions
        if request.user.is_superuser:
            return True
        # Check if the user is a doctor.
        if request.user.user_type != User.UserType.DOCTOR:
            return False

        # Check if the doctor has permission to view the patient's details.
        patient_id = view.kwargs.get('patient_id')
        if not patient_id:
            return False

        return DoctorPatient.objects.filter(doctor=request.user, patient_id=patient_id).exists()
