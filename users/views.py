from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, DoctorPatient, DoctorNote, ChecklistItem, ActionPlan, Reminder
from .serializers import (
    ActionPlanSerializer,
    ChecklistItemSerializer,
    ReminderSerializer,
    UserRegistrationSerializer, 
    DoctorListSerializer,
    DoctorPatientSerializer,
    DoctorNoteSerializer,
    NoteResponseSerializer,
)
from .services import LLMService, ReminderScheduler
from drf_spectacular.utils import extend_schema, OpenApiResponse

# Create your views here.
class UserRegistrationView(APIView):
    @extend_schema(
        request={'multipart/form-data': UserRegistrationSerializer},
        responses={
            201: UserRegistrationSerializer,
            400: OpenApiResponse(description='Invalid data provided')
        },
        description="Register a new user (Patient or Doctor)",
        tags=["Authentication"],
        operation_id='auth_register'
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(BaseTokenObtainPairView):
    @extend_schema(
        tags=['Authentication'],
        description='Login with email and password to obtain JWT tokens',
        request={'multipart/form-data': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string'},
                'password': {'type': 'string'}
            },
            'required': ['email', 'password']
        }},
        responses={
            200: OpenApiResponse(description='Login successful, returns access and refresh tokens'),
            401: OpenApiResponse(description='Invalid credentials')
        },
        operation_id='auth_login'
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class TokenRefreshView(BaseTokenRefreshView):
    @extend_schema(
        tags=['Authentication'],
        description='Refresh access token using refresh token',
        request={'multipart/form-data': {
            'type': 'object',
            'properties': {
                'refresh_token': {'type': 'string'}
            },
            'required': ['refresh_token']
        }},
        responses={
            200: OpenApiResponse(description='Token refresh successful, returns new access token'),
            401: OpenApiResponse(description='Invalid refresh token')
        },
        operation_id='auth_refresh'
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=['Authentication'],
        description='Logout by blacklisting the refresh token',
        request={'multipart/form-data': {
            'type': 'object',
            'properties': {
                'refresh_token': {'type': 'string'}
            },
            'required': ['refresh_token']
        }},
        responses={
            200: OpenApiResponse(description='Successfully logged out'),
            401: OpenApiResponse(description='Invalid token or unauthorized')
        },
        operation_id='auth_logout'
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_400_BAD_REQUEST)

class DoctorListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Doctor-Patient'],
        description='List all available doctors',
        responses={200: DoctorListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        doctors = User.objects.filter(user_type=User.UserType.DOCTOR)
        serializer = DoctorListSerializer(doctors, many=True)
        return Response(serializer.data)

class AssignDoctorView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Doctor-Patient'],
        description='Patient select a doctor',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'doctor': {
                        'type': 'integer',
                        'description': 'ID of the doctor to assign'
                    }
                },
                'required': ['doctor']
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
        
        serializer = DoctorPatientSerializer(data={
            'doctor': request.data.get('doctor'),
            'patient': request.user.id
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MyPatientsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Doctor-Patient'],
        description='List all patients assigned to the current doctor',
        responses={200: DoctorPatientSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        if request.user.user_type != User.UserType.DOCTOR:
            return Response([])
        doctor_patients = DoctorPatient.objects.filter(doctor=request.user)
        serializer = DoctorPatientSerializer(doctor_patients, many=True)
        return Response(serializer.data)

class CreateNoteView(APIView):
    permission_classes = [IsAuthenticated]
    llm_service = LLMService()

    @extend_schema(
        tags=['Doctor Notes'],
        description='Create a note for a patient with AI-generated actionable items',
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'doctor_patient_id': {
                        'type': 'integer',
                        'description': 'ID of the doctor-patient relationship'
                    },
                    'content': {
                        'type': 'string',
                        'description': 'Content of the note'
                    }
                },
                'required': ['doctor_patient_id', 'content']
            }
        },
        responses={
            201: NoteResponseSerializer,
            400: OpenApiResponse(description='Invalid data provided'),
            403: OpenApiResponse(description='Not authorized to create notes for this patient')
        }
    )
    def post(self, request):
        if request.user.user_type != User.UserType.DOCTOR:
            return Response(
                {"detail": "Only doctors can create notes"},
                status=status.HTTP_403_FORBIDDEN
            )

        doctor_patient = get_object_or_404(
            DoctorPatient, 
            id=request.data.get('doctor_patient_id'),
            doctor=request.user
        )

        # Create the note
        note = DoctorNote.objects.create(
            doctor_patient=doctor_patient,
            content=request.data.get('content')
        )

        # Process with LLM
        llm_response = self.llm_service.process_doctor_note(note.content)

        # Create checklist items
        checklist_items = [
            ChecklistItem.objects.create(note=note, **item)
            for item in llm_response.get('checklist_items', [])
        ]

        # Create action plans
        action_plans = [
            ActionPlan.objects.create(note=note, **plan)
            for plan in llm_response.get('action_plans', [])
        ]

        response_data = {
            'note': DoctorNoteSerializer(note).data,
            'checklist_items': [ChecklistItemSerializer(item).data for item in checklist_items],
            'action_plans': [ActionPlanSerializer(plan).data for plan in action_plans]
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

class ListPatientNotesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Doctor Notes'],
        description='List all notes for a specific patient',
        responses={200: DoctorNoteSerializer(many=True)}
    )
    def get(self, request, patient_id):
        if request.user.user_type == User.UserType.DOCTOR:
            notes = DoctorNote.objects.filter(
                doctor_patient__doctor=request.user,
                doctor_patient__patient_id=patient_id
            )
        else:
            notes = DoctorNote.objects.filter(
                doctor_patient__patient=request.user
            )

        serializer = DoctorNoteSerializer(notes, many=True)
        return Response(serializer.data)

class ActionPlanView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Action Plans'],
        description='Create an action plan',
        request={'multipart/form-data': ActionPlanSerializer},
        responses={201: ActionPlanSerializer}
    )
    def post(self, request):
        serializer = ActionPlanSerializer(data=request.data)
        if serializer.is_valid():
            action_plan = serializer.save()
            ReminderScheduler.schedule_plan_reminders(action_plan)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=['Action Plans'], 
        description='List action plans',
        responses={200: ActionPlanSerializer(many=True)}
    )
    def get(self, request):
        action_plans = ActionPlan.objects.all()
        serializer = ActionPlanSerializer(action_plans, many=True)
        return Response(serializer.data)

class ActionPlanDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Action Plans'],
        description='Get details of an action plan',
        request={'application/json': {'type': 'object', 'properties': {
            'action_plan_id': {
                'type': 'integer',
                'description': 'ID of the action plan to get details for'
            }
        }}},
        responses={200: ActionPlanSerializer}
    )   
    def get(self, request, pk):
        action_plan = get_object_or_404(ActionPlan, id=pk)
        serializer = ActionPlanSerializer(action_plan)
        return Response(serializer.data)

class ReminderView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Reminders'],
        description='List reminders',
        responses={200: ReminderSerializer(many=True)}
    )
    def get(self, request):
        user = request.user
        if user.user_type == User.UserType.DOCTOR:
            reminders = Reminder.objects.filter(action_plan__doctor=user)
        else:
            reminders = Reminder.objects.filter(patient=user)
        serializer = ReminderSerializer(reminders, many=True)
        return Response(serializer.data)

class ReminderCheckInView(APIView):
    permission_classes = [IsAuthenticated]

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
        
        if reminder.patient != request.user:
            return Response(
                {"detail": "Not authorized"},
                status=status.HTTP_403_FORBIDDEN
            )

        if ReminderScheduler.handle_checkin(reminder):
            return Response({"detail": "Successfully checked in"})
        return Response(
            {"detail": "Already completed"},
            status=status.HTTP_400_BAD_REQUEST
        )
