from rest_framework.views import APIView
from rest_framework.response import Response
from apps.user.models import User
from api.utils.permissions import IsAuthenticated, IsEmailVerified
from api.serilizers.doctor import DoctorPatientSerializer
from drf_spectacular.utils import extend_schema
from rest_framework import status
from apps.doctor.models import DoctorPatient
from drf_spectacular.utils import OpenApiResponse
from django.shortcuts import get_object_or_404
from apps.patient.models import Reminder
from api.external.services import ReminderService
from api.pagination import BasicPagination
from api.utils.permissions import IsPatient

class AssignDoctorView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]
    pagination_class = BasicPagination
    
    @extend_schema(
        tags=['Doctor-Patient'],
        description='Patient selects a doctor',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'doctor_id': {
                        'type': 'integer',
                        'description': 'ID of the doctor to assign'
                    }
                },
                'required': ['doctor_id']
            }
        },
        responses={
            201: DoctorPatientSerializer,
            400: OpenApiResponse(description='Invalid data or already assigned to this doctor')
        }
    )
    def post(self, request, *args, **kwargs):
        if request.user.user_type != User.UserType.PATIENT:
            return Response(
                {"detail": "Only patients can select doctors"},
                status=status.HTTP_403_FORBIDDEN
            )

        doctor_id = request.data.get('doctor_id')

        # Ensure doctor exists and is actually a doctor
        try:
            doctor = User.objects.get(id=doctor_id, user_type=User.UserType.DOCTOR)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid doctor ID or user is not a doctor"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the patient is already assigned to this doctor
        if DoctorPatient.objects.filter(doctor=doctor, patient=request.user).exists():
            return Response(
                {"detail": "You are already assigned to this doctor"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the doctor-patient relationship
        doctor_patient = DoctorPatient.objects.create(doctor=doctor, patient=request.user)

        return Response(DoctorPatientSerializer(doctor_patient).data, status=status.HTTP_201_CREATED)

class ReminderCheckInView(APIView):
    permission_classes = [IsPatient,IsEmailVerified]

    @extend_schema(
        tags=['Reminders'],
        description='Check-in for a reminder',
        request={'multipart/form-data': {'type': 'object', 'properties': {
            'reminder_id': {
                'type': 'integer',
                'description': 'ID of the reminder to check-in'
            }
        }}},
        responses={
            200: OpenApiResponse(description='Successfully checked in'),
            400: OpenApiResponse(description='Invalid check-in or already completed')
        }
    )
    def post(self, request, reminder_id):
        reminder = get_object_or_404(Reminder, id=reminder_id)
        if ReminderService.handle_checkin(reminder):
            return Response({"detail": "Successfully checked in"})
        return Response(
            {"detail": "Already completed"},
            status=status.HTTP_400_BAD_REQUEST
        )