from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from apps.user.models import User, UserOTP
from apps.doctor.models import DoctorPatient, DoctorNote, ChecklistItem
from apps.patient.models import Reminder, ActionPlan

class CustomUserAdmin(UserAdmin):
    list_display = ('email','full_name', 'user_type','email_verified', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined')
    list_display_links = ('email', 'full_name')
    readonly_fields = ('date_joined', 'last_login', 'public_key', 'private_key')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups')
    search_fields = ('email', 'full_name')
    ordering = ('date_joined',)
    filter_horizontal = ('groups', 'user_permissions',)


    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name','username', 'user_type')}),
        (_('Permissions'), {
            'fields': ('email_verified','is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Keys'), {'fields': ('public_key', 'private_key')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type', 'username'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('email',)
        return self.readonly_fields

class UserOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_secret')
    list_display_links = ('user',)
    list_filter = ('user',)
    search_fields = ('user__email',)
    raw_id_fields = ('user',)
    ordering = ('id',)
class DoctorPatientAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'created_at')
    list_display_links = ('doctor', 'patient')
    list_filter = ('created_at',)
    search_fields = ('doctor__email', 'patient__email')
    raw_id_fields = ('doctor', 'patient')
    date_hierarchy = 'created_at'
    ordering = ('id',)

class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'task', 'is_completed')
    list_display_links = ('note', 'task')
    list_filter = ('is_completed',)
    search_fields = ('task', 'note__content')
    raw_id_fields = ('note',)
    ordering = ('id',)


class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'action', 'frequency', 'start_date', 'end_date', 'is_active')
    list_display_links = ('note', 'action')
    list_filter = ('frequency', 'is_active')
    search_fields = ('action', 'note__content')
    raw_id_fields = ('note',)
    date_hierarchy = 'start_date'
    ordering = ('id',)


class DoctorNoteAdmin(admin.ModelAdmin):
    list_display = ('doctor_patient', 'created_at', 'get_doctor', 'get_patient')
    list_display_links = ('doctor_patient',)
    list_filter = ('created_at',)
    search_fields = ('content', 'doctor_patient__doctor__email', 'doctor_patient__patient__email')
    raw_id_fields = ('doctor_patient',)
    date_hierarchy = 'created_at'
    readonly_fields = ('content',)
    ordering = ('id',)

    def get_doctor(self, obj):
        return obj.doctor_patient.doctor.email
    get_doctor.short_description = 'Doctor'
    get_doctor.admin_order_field = 'doctor_patient__doctor__email'

    def get_patient(self, obj):
        return obj.doctor_patient.patient.email
    get_patient.short_description = 'Patient'
    get_patient.admin_order_field = 'doctor_patient__patient__email'

class ReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'action_plan', 'get_patient', 'title', 'scheduled_for', 'completed', 'is_active')
    list_display_links = ('action_plan',)
    list_filter = ('completed', 'is_active')
    search_fields = ('title', 'action_plan__note__content', 'patient__email')
    raw_id_fields = ('action_plan', 'patient')
    date_hierarchy = 'scheduled_for'
    ordering = ('id',)

    def get_patient(self, obj):
        return obj.patient.email
    get_patient.short_description = 'Patient'
    get_patient.admin_order_field = 'patient__email'

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserOTP, UserOTPAdmin)
admin.site.register(DoctorPatient, DoctorPatientAdmin)
admin.site.register(DoctorNote, DoctorNoteAdmin)
admin.site.register(ChecklistItem, ChecklistItemAdmin)
admin.site.register(ActionPlan, ActionPlanAdmin)
admin.site.register(Reminder, ReminderAdmin)