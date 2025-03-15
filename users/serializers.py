from rest_framework import serializers
from .models import User, DoctorPatient, DoctorNote, ChecklistItem, ActionPlan, Reminder

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'user_type']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.username = validated_data['email']  # Using email as username
        user.save()
        return user 

class DoctorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']
        read_only_fields = fields

class DoctorPatientSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)

    class Meta:
        model = DoctorPatient
        fields = ['id', 'doctor', 'patient', 'doctor_name', 'patient_name', 'created_at']
        read_only_fields = ['created_at']

class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ['id', 'task', 'is_completed', 'created_at']
        read_only_fields = ['created_at']

class ActionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionPlan
        fields = ['id', 'action', 'frequency', 'start_date', 'end_date', 
                 'custom_schedule', 'is_active', 'created_at']
        read_only_fields = ['created_at']

class DoctorNoteSerializer(serializers.ModelSerializer):
    checklist_items = ChecklistItemSerializer(many=True, read_only=True)
    action_plans = ActionPlanSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='doctor_patient.patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor_patient.doctor.full_name', read_only=True)

    class Meta:
        model = DoctorNote
        fields = ['id', 'doctor_patient', 'content', 'created_at', 'updated_at',
                 'checklist_items', 'action_plans', 'patient_name', 'doctor_name']
        read_only_fields = ['created_at', 'updated_at']

class NoteResponseSerializer(serializers.Serializer):
    note = DoctorNoteSerializer()
    checklist_items = ChecklistItemSerializer(many=True)
    action_plans = ActionPlanSerializer(many=True) 
    
class ReminderSerializer(serializers.Serializer):
    class Meta:
        model = Reminder
        fields = "__all__"
        read_only_fields = fields