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
    UserRegistrationView, LoginView, TokenRefreshView, LogoutView
)

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Doctor-Patient endpoints
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('doctors/assign/', AssignDoctorView.as_view(), name='assign-doctor'),
    path('doctors/my-patients/', MyPatientsView.as_view(), name='my-patients'),

    # Doctor Notes endpoints
    path('notes/create/', CreateNoteView.as_view(), name='create-note'),
    path('notes/patient/<int:patient_id>/', PatientNotesView.as_view(), name='patient-notes'),

    # Patient notes
    path('patient-notes/', ListPatientNotesView.as_view(), name='patient-notes'),

    # Action Plans endpoints
    path('action-plans/', ActionPlanView.as_view(), name='create-action-plans'),
    path('action-plans/<int:pk>/', ActionPlanDetailView.as_view(), name='action-plan-detail'),

    # Reminders endpoints
    path('reminders/', ReminderView.as_view(), name='reminders'),
    path('reminders/checkin/<int:reminder_id>/', ReminderCheckInView.as_view(), name='reminder-checkin'),
]   