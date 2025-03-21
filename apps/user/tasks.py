from celery import shared_task
from django.utils import timezone
from apps.patient.models import Reminder
from datetime import timedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from celery.utils.log import get_task_logger
from core.celery import app
from api.utils.generate_otp import generate_otp_secret, generate_numeric_otp
from django.shortcuts import get_object_or_404
from apps.user.models import User
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from api.utils.tokens import FlexibleTokenGenerator

logger = get_task_logger(__name__)

@app.task(name='verify_account_email', serializer='json', queue="Mail")
def verify_account_email(data):
    pk = data.get('pk')
    user  = get_object_or_404(User, pk=pk)

    # USER ACTIVATION
    name = user.full_name

    interval = settings.EMAIL_TOKEN_EXPIRATION_MINUTES

    generate_otp_secret(user)  # Call the utility function to generate secret
    otp_code = generate_numeric_otp(user, interval_in_mins=interval)

    mail_subject = "Activate Your CareSync AI Account"
    message = render_to_string('mail_copies/otp_code.html', {
        'name'  : name,
        'otp_code': otp_code,
        'interval': int(interval),
        'UI_DOMAIN': str(settings.UI_DOMAIN)
    })
    to_email = user.email
    send_email  = EmailMultiAlternatives(mail_subject, message,settings.EMAIL_HOST_USER, to=[to_email])
    send_email.content_subtype = "html"

    try:
        print('Attempting to Send Mail')
        send_email.send()
        print('Email Sent')
    except Exception as e:
        print(e)
        return{'message':'failed to send mail'}

    return{'message':'mail sent successfully'}


@app.task(name='send_reminder_email', serializer='json', queue="Reminder")
def send_reminder_email(reminder_id):    
    try:
        reminder = Reminder.objects.get(id=reminder_id)
        if not reminder.completed and reminder.is_active:
            mail_subject = f"Reminder: {reminder.title} - Day {reminder.sequence_number}"
            message = render_to_string('reminder_copy/reminder_template.html', {
                'reminder': reminder,
                'ui_domain': settings.UI_DOMAIN
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


@app.task(name='send_otp_code_email', serializer='json', queue="Mail")
def send_otp_code_email(data):
    pk          = data.get('pk')
    interval    = data.get('interval', None)

    user  = get_object_or_404(User, pk=pk)

    # USER ACTIVATION
    name = user.username

    if interval is None:
        interval = settings.EMAIL_TOKEN_EXPIRATION_MINUTES
    
    generate_otp_secret(user)  # Call the utility function to generate secret
    otp_code = generate_numeric_otp(user, interval_in_mins=interval)

    mail_subject = "CareSync AI OTP Request"
    message = render_to_string('mail_copies/otp_code.html', {
        'name'  : name,
        'otp_code': otp_code,
        'interval': int(interval),
        'UI_DOMAIN': str(settings.UI_DOMAIN)
    })
    to_email = user.email
    send_email  = EmailMultiAlternatives(mail_subject, message, to=[to_email])
    send_email.content_subtype = "html"
    
    try:
        send_email.send()
    except Exception as e:
        return{'message':'failed to send mail'}

    return{'message':'mail sent successfully'}

@app.task(name='reset_password_email', serializer='json', queue="Mail")
def reset_password_email(data):
    pk = data.get('pk')
    user  = get_object_or_404(User, pk=pk)
    
    name = user.username

    interval = settings.PASSWORD_TOKEN_EXPIRATION_MINUTES
    
    token_generator = FlexibleTokenGenerator.for_password_reset()
        
    # RESET PASSWORD EMAIL
    mail_subject = "Reset Your Jampolls Password"
    message = render_to_string('mail_copies/reset_password_template.html', {
        'name'  : name,
        'uid'   : urlsafe_base64_encode(force_bytes(user.pk)),
        'eid'   : urlsafe_base64_encode(force_bytes(user.email)),
        'token' : token_generator.make_token(user),
        'interval': int(interval),
        'UI_DOMAIN': str(settings.UI_DOMAIN)
    })

    to_email = user.email
    send_email  = EmailMultiAlternatives(mail_subject, message, to=[to_email])
    send_email.content_subtype = "html"

    try:
        send_email.send()
    except Exception as e:
        print(e)
        return{'message':'failed to send mail'}
    
    return{'message':'mail sent successfully'}

