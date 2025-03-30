from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from twilio.rest import Client
import uuid
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from apps.user.models import User

from .models import VideoConsultation
from .serializers import VideoConsultationSerializer

@extend_schema_view(post=extend_schema(
    summary      = 'Video consultation',
    description  = 'Video consultation',
    methods      = ['post'],
    operation_id = 'video_consultation_id',
    tags         = ["Video consultation"],
))
class VideoConsultationViewSet(viewsets.ModelViewSet):
    queryset = VideoConsultation.objects.all()
    serializer_class = VideoConsultationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == User.UserType.DOCTOR:
            return VideoConsultation.objects.filter(doctor=user)
        elif user.user_type == User.UserType.PATIENT:
            return VideoConsultation.objects.filter(patient=user)
        return VideoConsultation.objects.none()


    def perform_create(self, serializer):
        room_name = f"consultation-{uuid.uuid4()}"
        serializer.save(room_name=room_name)

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        consultation = self.get_object()
        
        if not consultation.can_join():
            return Response(
                {"error": "Cannot join consultation at this time"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        account_sid = settings.TWILIO_ACCOUNT_SID  # Must start with "AC..."
        api_key = settings.TWILIO_API_KEY  # Must start with "SK..."
        api_secret = settings.TWILIO_API_SECRET  # Your API secret

        # Initialize Twilio client
        client = Client(account_sid, settings.TWILIO_AUTH_TOKEN)

        # Create or get Twilio room
        if not consultation.twilio_room_sid:
            try:
                room = client.video.v1.rooms.create(
                    unique_name=consultation.room_name,
                    type='group',
                    max_participants=2
                )
                consultation.twilio_room_sid = room.sid
                consultation.status = VideoConsultation.ONGOING
                consultation.save()
            except Exception as e:
                return Response(
                    {"error": f"Failed to create Twilio room: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Generate access token
        token = AccessToken(
            account_sid,
            api_key,
            api_secret,
            identity=str(request.user.id),
            ttl=3600 # 1 hour expiration
        )

        # Create Video grant
        video_grant = VideoGrant(room=consultation.room_name)
        token.add_grant(video_grant)

        return Response({
            "token": token.to_jwt(),
            "room_name": consultation.room_name
        })

    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        consultation = self.get_object()
        
        if consultation.status != VideoConsultation.ONGOING:
            return Response(
                {"error": "Consultation is not ongoing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # End Twilio room
        if consultation.twilio_room_sid:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            try:
                room = client.video.v1.rooms(consultation.twilio_room_sid).update(
                    status='completed'
                )
            except Exception as e:
                return Response(
                    {"error": f"Failed to end Twilio room: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        consultation.status = VideoConsultation.COMPLETED
        consultation.save()

        return Response({"status": "Consultation ended successfully"})

def video_test(request):
    return render(request, 'video_test.html')
