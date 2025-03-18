from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from apps.user.models import User
from apps.doctor.models import DoctorPatient, DoctorNote, ChecklistItem
from apps.patient.models import Reminder, ActionPlan

class CustomUserAdmin(UserAdmin):
    list_display = ('id','email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('date_joined', 'last_login')
    filter_horizontal = ('groups', 'user_permissions',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'user_type')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type', 'first_name', 'last_name'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('email',)
        return self.readonly_fields

class DoctorPatientAdmin(admin.ModelAdmin):
    list_display = ('id','doctor', 'patient', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('doctor__email', 'patient__email')
    raw_id_fields = ('doctor', 'patient')
    date_hierarchy = 'created_at'


class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'task', 'is_completed')
    list_filter = ('is_completed',)
    search_fields = ('task', 'note__content')
    raw_id_fields = ('note',)


class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'action', 'frequency', 'start_date', 'end_date', 'is_active')
    list_filter = ('frequency', 'is_active')
    search_fields = ('action', 'note__content')
    raw_id_fields = ('note',)
    date_hierarchy = 'start_date'


class DoctorNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'doctor_patient', 'created_at', 'get_doctor', 'get_patient')
    list_filter = ('created_at',)
    search_fields = ('content', 'doctor_patient__doctor__email', 'doctor_patient__patient__email')
    raw_id_fields = ('doctor_patient',)
    date_hierarchy = 'created_at'

    def get_doctor(self, obj):
        return obj.doctor_patient.doctor.email
    get_doctor.short_description = 'Doctor'
    get_doctor.admin_order_field = 'doctor_patient__doctor__email'

    def get_patient(self, obj):
        return obj.doctor_patient.patient.email
    get_patient.short_description = 'Patient'
    get_patient.admin_order_field = 'doctor_patient__patient__email'


class ReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'action_plan', 'patient', 'title', 'scheduled_for', 'completed')
    list_filter = ('completed',)
    search_fields = ('title', 'action_plan__note__content', 'patient__email')
    raw_id_fields = ('action_plan', 'patient')
    date_hierarchy = 'scheduled_for'

admin.site.register(User, CustomUserAdmin)
admin.site.register(DoctorPatient, DoctorPatientAdmin)
admin.site.register(DoctorNote, DoctorNoteAdmin)
admin.site.register(ChecklistItem, ChecklistItemAdmin)
admin.site.register(ActionPlan, ActionPlanAdmin)
admin.site.register(Reminder, ReminderAdmin)