from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

@shared_task
def send_reminder_email(reminder_id):
    from .models import Reminder  # Import here to avoid circular imports
    
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        if not reminder.completed:
            subject = f"Reminder: {reminder.title}"
            message = f"""
            Hello {reminder.patient.full_name},
            
            This is a reminder for your action plan: {reminder.description}
            
            Please check-in once completed.
            """
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [reminder.patient.email],
                fail_silently=False,
            )
            
    except Reminder.DoesNotExist:
        pass
