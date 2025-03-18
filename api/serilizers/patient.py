from apps.patient.models import ActionPlan, Reminder
from rest_framework import serializers
from apps.user.models import User


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email']

class ActionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionPlan
        fields = ['id', 'action', 'frequency', 'start_date', 'end_date', 
                 'custom_schedule', 'is_active', 'created_at']
        read_only_fields = ['created_at']   

class ReminderSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    action_plan = ActionPlanSerializer(read_only=True)
    class Meta:
        model = Reminder
        fields = "__all__"
        depth = 1