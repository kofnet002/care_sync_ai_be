from rest_framework.views import APIView
from rest_framework.response import Response
from apps.user.models import User
from api.serilizers.doctor import DoctorListSerializer
from drf_spectacular.utils import extend_schema
from rest_framework import status
from apps.doctor.models import DoctorPatient
from api.serilizers.doctor import DoctorPatientSerializer
from drf_spectacular.utils import OpenApiResponse
from django.shortcuts import get_object_or_404
from apps.doctor.models import DoctorNote, ChecklistItem
from api.serilizers.doctor import DoctorNoteSerializer, NoteResponseSerializer, ChecklistItemSerializer
from api.external.services import LLMService
from api.serilizers.patient import ActionPlanSerializer, ReminderSerializer
from apps.patient.models import Reminder, ActionPlan
from api.external.services import ReminderService
from api.utils.permissions import IsDoctor, DoctorPatientPermission, IsEmailVerified
from api.pagination import BasicPagination
from rest_framework import generics
from api.utils.permissions import IsAuthenticated

class DoctorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]
    pagination_class = BasicPagination
    
    @extend_schema(
        tags=['Doctor-Patient'],
        description='List all available doctors',
        responses={200: DoctorListSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        doctors = User.objects.filter(user_type=User.UserType.DOCTOR)
          # Get paginator instance
        paginator = self.pagination_class()
        
        # Paginate the queryset
        paginated_doctors = paginator.paginate_queryset(doctors, request)
        
        # Serialize the paginated data
        serializer = DoctorListSerializer(paginated_doctors, many=True)

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)

class MyPatientsView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor, IsEmailVerified]
    pagination_class = BasicPagination
    
    @extend_schema(
        tags=['Doctor-Patient'],
        description='List all patients assigned to the current doctor',
        responses={200: DoctorPatientSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        doctor_patients = DoctorPatient.objects.filter(doctor=request.user)
        # Get paginator instance
        paginator = self.pagination_class()
        
        # Paginate the queryset
        paginated_doctor_patients = paginator.paginate_queryset(doctor_patients, request)
        
        # Serialize the paginated data
        serializer = DoctorPatientSerializer(paginated_doctor_patients, many=True)
        return paginator.get_paginated_response(serializer.data)


class CreateNoteView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor, IsEmailVerified]
    llm_service = LLMService()

    @extend_schema(
        tags=['Doctor Notes'],
        description='Create an encrypted note for a patient with AI-generated actionable items',
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
        responses={201: NoteResponseSerializer}
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

        try:
            """New patient notes cancel any previously scheduled actionable steps."""
            # # Cancel previous action plans and their reminders
            # previous_notes = DoctorNote.objects.filter(doctor_patient=doctor_patient)
            # for note in previous_notes:
            #     # Deactivate previous action plans
            #     ActionPlan.objects.filter(note=note, is_active=True).update(is_active=False)
            #     # Cancel associated reminders
            #     Reminder.objects.filter(
            #         action_plan__note=note,
            #         completed=False
            #     ).update(is_active=False)
                
            # Get the raw content first
            raw_content = request.data.get('content')
            if not raw_content:
                return Response(
                    {"detail": "Content is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Process with LLM before encryption
            llm_response = self.llm_service.process_doctor_note(raw_content)

            # Create and encrypt the note
            note = DoctorNote.objects.create(doctor_patient=doctor_patient)
            note.encrypt_note(raw_content)

            # Create checklist items
            checklist_items = [
                ChecklistItem.objects.create(note=note, **item)
                for item in llm_response.get('checklist_items', [])
            ]

            # Create action plans and schedule reminders
            action_plans = [
                ActionPlan.objects.create(note=note, patient=doctor_patient.patient, is_active=True, **plan)
                for plan in llm_response.get('action_plans', [])
            ]
            
            # Schedule reminders    
            for action_plan in action_plans:
                ReminderService.create_schedule_plan_reminders(action_plan)
            
            response_data = {
                'note': DoctorNoteSerializer(note).data,
            }

            return Response(response_data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PatientNotesView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor, DoctorPatientPermission, IsEmailVerified]
    
    @extend_schema(
        tags=['Doctor Notes'],
        description='Detailed notes for a specific patient',
        responses={200: DoctorNoteSerializer(many=True)}
    )
    def get(self, request, patient_id):
        try:
            notes = DoctorNote.objects.filter(
                doctor_patient__doctor=request.user,
                doctor_patient__patient_id=patient_id
            )
            decrypted_notes = []
            for note in notes:
                try:
                    decrypted_content = note.decrypt_note(request.user)
                    note_data = {
                        'id': note.id,
                        'content': decrypted_content,
                        'created_at': note.created_at,
                    }
                    decrypted_notes.append(note_data)
                except Exception as e:
                    print(f"Decryption error: {str(e)}")
                    continue
            return Response({"notes": decrypted_notes}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ListPatientNotesView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor, DoctorPatientPermission, IsEmailVerified]
    pagination_class = BasicPagination

    @extend_schema(
        tags=['Doctor Notes'],
        description='List all notes for a specific patient',
        responses={200: DoctorNoteSerializer(many=True)}
    )
    def get(self, request):
        try:
            if request.user.user_type == User.UserType.DOCTOR:
                notes = DoctorNote.objects.filter(
                    doctor_patient__doctor=request.user
                ).select_related('doctor_patient__doctor', 'doctor_patient__patient')
            else:
                notes = DoctorNote.objects.filter(
                    doctor_patient__patient=request.user
                ).select_related('doctor_patient__doctor', 'doctor_patient__patient')

            decrypted_notes = []
            for note in notes:
                try:
                    decrypted_content = note.decrypt_note(request.user)
                    note_data = {
                        'id': note.id,
                        'content': decrypted_content,
                        'created_at': note.created_at,
                        'doctor': note.doctor_patient.doctor.full_name,
                        'patient': note.doctor_patient.patient.full_name
                    }
                    decrypted_notes.append(note_data)
                except Exception as e:
                    print(f"Decryption error for note {note.id}: {str(e)}")
                    continue

            paginator = self.pagination_class()
            paginated_notes = paginator.paginate_queryset(decrypted_notes, request)
            
            return paginator.get_paginated_response(paginated_notes)

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ActionPlanView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor, DoctorPatientPermission, IsEmailVerified]
    pagination_class = BasicPagination
    
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
        # Get paginator instance
        paginator = self.pagination_class()
        
        # Paginate the queryset
        paginated_action_plans = paginator.paginate_queryset(action_plans, request)
        
        # Serialize the paginated data
        serializer = ActionPlanSerializer(paginated_action_plans, many=True)
        return paginator.get_paginated_response(serializer.data)

class ActionPlanDetailView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor, DoctorPatientPermission, IsEmailVerified]
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
        return Response(serializer.data, status=status.HTTP_200_OK  )

class ReminderView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor, DoctorPatientPermission, IsEmailVerified]
    pagination_class = BasicPagination
    
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
            
        # Get paginator instance
        paginator = self.pagination_class()
        
        # Paginate the queryset
        paginated_reminders = paginator.paginate_queryset(reminders, request)
        
        serializer = ReminderSerializer(paginated_reminders, many=True)
        return paginator.get_paginated_response(serializer.data)