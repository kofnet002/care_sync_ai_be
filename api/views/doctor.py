from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.user.models import User
from api.serilizers.doctor import DoctorListSerializer
from drf_spectacular.utils import extend_schema
from rest_framework import status
from apps.doctor.models import DoctorPatient
from api.serilizers.doctor import DoctorPatientSerializer
from drf_spectacular.utils import OpenApiResponse
from django.shortcuts import get_object_or_404
from apps.doctor.models import DoctorNote, ChecklistItem
from api.serilizers.doctor import DoctorNoteSerializer, NoteResponseSerializer
from api.external.services import LLMService
from api.serilizers.patient import ActionPlanSerializer, ReminderSerializer
from apps.patient.models import Reminder, ActionPlan
from api.external.services import ReminderService

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

class MyPatientsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Doctor-Patient'],
        description='List all patients assigned to the current doctor',
        responses={200: DoctorPatientSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        if request.user.user_type != User.UserType.DOCTOR:
            return Response({
                "success": False,
                "detail": "Only doctors can view their patients"
            }, status=status.HTTP_403_FORBIDDEN)

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

        # Create action plans and schedule reminders
        action_plans = [
            ActionPlan.objects.create(note=note, **plan)
            for plan in llm_response.get('action_plans', [])
        ]
        
        # Schedule reminders    
        for action_plan in action_plans:
            ReminderService.create_schedule_plan_reminders(action_plan)
            
        
        response_data = {
            'note': DoctorNoteSerializer(note).data,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

class PatientNotesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Doctor Notes'],
        description='Detailed notes for a specific patient',
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

class ListPatientNotesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Doctor Notes'],
        description='List all notes for a specific patient',
        responses={200: DoctorNoteSerializer(many=True)}
    )
    def get(self, request):
        if request.user.user_type == User.UserType.DOCTOR:
            notes = DoctorNote.objects.filter(
                doctor_patient__doctor=request.user
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
            ReminderService.create_schedule_plan_reminders(action_plan)
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
            reminders = Reminder.objects.filter(action_plan__note__doctor_patient__doctor=user)
        else:
            reminders = Reminder.objects.filter(patient=user)
            
        serializer = ReminderSerializer(reminders, many=True)
        return Response(serializer.data)