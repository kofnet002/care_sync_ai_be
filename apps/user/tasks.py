from celery import shared_task
from django.utils import timezone
from apps.patient.models import Reminder
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_reminder_email(reminder_id):    
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        if not reminder.completed:
            print(f"Sending reminder email for reminder: {reminder}")
            subject = f"Reminder: {reminder.title} - Day {reminder.sequence_number}"
            message = f"""
            Hello {reminder.patient.email},
            
            This is a reminder for your action plan: {reminder.description}
            Day {reminder.sequence_number}
            Please check-in once completed.
            """
            
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [reminder.patient.email],
                fail_silently=False,
            )
            
            # If not checked in by scheduled time, reschedule for next hour
            next_reminder = timezone.now() + timedelta(hours=1)
            send_reminder_email.apply_async(
                args=[reminder.id],
                eta=next_reminder
            )
            
    except Reminder.DoesNotExist:
        pass


@shared_task
def check_and_send_due_reminders():
    """
    Periodic task that runs every 5 minutes to check and send due reminders
    """
    now = timezone.now()
    due_reminders = Reminder.objects.filter(
        completed=False,
        scheduled_for__lte=now
    ).select_related('patient', 'action_plan')

    for reminder in due_reminders:
        send_reminder_email.delay(reminder.id)