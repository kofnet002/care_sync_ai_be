from rest_framework import serializers
from .models import VideoConsultation

class VideoConsultationSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()

    class Meta:
        model = VideoConsultation
        fields = [
            'id', 'doctor', 'patient', 'doctor_name', 'patient_name',
            'scheduled_time', 'status', 'room_name', 'duration',
            'notes', 'created_at', 'updated_at', 'can_join'
        ]
        read_only_fields = ['room_name', 'created_at', 'updated_at']

    def get_doctor_name(self, obj):
        return obj.doctor.username if obj.doctor else None

    def get_patient_name(self, obj):
        return obj.patient.username if obj.patient else None

    def get_can_join(self, obj):
        return obj.can_join() if hasattr(obj, 'can_join') else False
