from rest_framework import serializers
from apps.user.models import User
from apps.doctor.models import DoctorPatient, DoctorNote, ChecklistItem
from api.serilizers.patient import PatientSerializer, ActionPlanSerializer


class DoctorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = fields

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class DoctorPatientSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    class Meta:
        model = DoctorPatient
        fields = ['id', 'doctor', 'patient', 'created_at']
        read_only_fields = ['created_at']
        
class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['id', 'task', 'is_completed', 'created_at']
        read_only_fields = ['created_at']

class DoctorNoteSerializer(serializers.ModelSerializer):
    checklist_items = ChecklistItemSerializer(many=True, read_only=True)
    action_plans = ActionPlanSerializer(many=True, read_only=True)
    doctor = DoctorSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    class Meta:
        model = DoctorNote
        fields = ['id', 'doctor_patient', 'content', 'created_at', 'updated_at',
                 'checklist_items', 'action_plans', 'doctor', 'patient']
        read_only_fields = ['created_at', 'updated_at']

class NoteResponseSerializer(serializers.Serializer):
    note = DoctorNoteSerializer()
    checklist_items = ChecklistItemSerializer(many=True)
    action_plans = ActionPlanSerializer(many=True) 