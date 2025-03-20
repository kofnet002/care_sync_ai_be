from django.urls import path
from api.views.doctor import (
    DoctorListView, MyPatientsView,
    CreateNoteView, PatientNotesView, ListPatientNotesView,
    ActionPlanView, ActionPlanDetailView, ReminderView,
)
from api.views.patient import (
    ReminderCheckInView, AssignDoctorView
)
from api.views.user import (
    UserRegistrationView, SuperUserRegistrationView, LoginView, TokenRefreshView, LogoutView, EmailVerificationConfirmAPIView, EmailVerificationRequestAPIView,
    UpdatePasswordTokenRequest, UpdatePasswordVerifyAccessToken, UpdatePasswordCompleteUpdate, ForgetPasswordTokenRequest, ForgetPasswordVerifyAccessToken, ForgetPasswordCompleteReset
)

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/superuser/register/', SuperUserRegistrationView.as_view(), name='superuser-register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Email Verification endpoints
    path('auth/email/verification/request/', EmailVerificationRequestAPIView.as_view(), name='email_ver_request'),
    path('auth/email/verification/confirm/', EmailVerificationConfirmAPIView.as_view(), name='email_ver_confirm'),

    # Password Update endpoints
    path('auth/password/update/request/', UpdatePasswordTokenRequest.as_view(), name='password_update_code_request'),
    path('auth/password/update/verify/', UpdatePasswordVerifyAccessToken.as_view(), name='password_update_verify_code'),
    path('auth/password/update/complete/', UpdatePasswordCompleteUpdate.as_view(), name='password_update_complete'),  
    
    # Password Forgot Reset endpoints
    path('auth/password/forgot/reset/request/', ForgetPasswordTokenRequest.as_view(), name='forget_password_code_request'),
    path('auth/password/forgot/reset/verify/', ForgetPasswordVerifyAccessToken.as_view(), name='forget_password_verify_code'),
    path('auth/password/forgot/reset/complete/', ForgetPasswordCompleteReset.as_view(), name='forget_password_complette'),

    # Doctor-Patient endpoints
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('doctors/assign/', AssignDoctorView.as_view(), name='assign-doctor'),
    path('doctors/my-patients/', MyPatientsView.as_view(), name='my-patients'),

    # Doctor Notes endpoints
    path('notes/create/', CreateNoteView.as_view(), name='create-note'),
    path('notes/patient/<int:patient_id>/', PatientNotesView.as_view(), name='patient-note'),
    path('patient-notes/', ListPatientNotesView.as_view(), name='patient-notes'),

    # Action Plans endpoints
    path('action-plans/', ActionPlanView.as_view(), name='create-action-plans'),
    path('action-plans/<int:pk>/', ActionPlanDetailView.as_view(), name='action-plan-detail'),

    # Reminders endpoints
    path('reminders/', ReminderView.as_view(), name='reminders'),
    path('reminders/<int:reminder_id>/checkin/', ReminderCheckInView.as_view(), name='reminder-checkin'),
]   