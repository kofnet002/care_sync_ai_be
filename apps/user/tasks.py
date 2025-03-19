from celery import shared_task
from django.utils import timezone
from apps.patient.models import Reminder
from datetime import timedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from celery.utils.log import get_task_logger
from core.celery import app

logger = get_task_logger(__name__)

@app.task(name='send_reminder_email', serializer='json', queue="Reminder")
def send_reminder_email(reminder_id):    
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        if not reminder.completed:
            mail_subject = f"Reminder: {reminder.title} - Day {reminder.sequence_number}"
            message = render_to_string('reminder_copy/reminder_template.html', {
                'reminder': reminder,
                'app_url': settings.APP_URL
            })
            to_email = reminder.patient.email
            send_email  = EmailMultiAlternatives(mail_subject, message, settings.EMAIL_HOST_USER, [to_email])
            send_email.content_subtype = "html"

        try:
            print('Attempting to Send Mail')
            send_email.send()
            print('Email Sent')
            
            # If not checked in by scheduled time, reschedule for next hour
            next_reminder = timezone.now() + timedelta(hours=1)
            send_reminder_email.apply_async(
                args=[reminder.id],
                eta=next_reminder
            )
        except Exception as e:
            print(e)
            return{'message':'failed to send mail'}
    except Reminder.DoesNotExist:
        pass


@app.task(name='check_and_send_due_reminders', serializer='json', queue="Reminder")
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