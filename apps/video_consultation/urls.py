from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoConsultationViewSet, video_test

router = DefaultRouter()
router.register(r'consultations', VideoConsultationViewSet, basename='video-consultation')

urlpatterns = [
    path('', include(router.urls)),
    path('video-test/', video_test, name='video_test'),
] 