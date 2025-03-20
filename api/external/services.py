import google.generativeai as genai
from datetime import datetime, timedelta
from django.conf import settings
import json
from django.utils import timezone
from apps.user.tasks import send_reminder_email
from celery.exceptions import OperationalError
from core.celery import app 
from apps.patient.models import Reminder, ActionPlan
import traceback


class LLMService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def process_doctor_note(self, note_content):
        prompt = f"""
        Based on the following doctor's note, extract two types of information:
        1. Immediate one-time tasks (checklist items)
        2. Scheduled actions with timing (action plan)

        Doctor's Note:
        {note_content}

        Please format your response in JSON with the following structure:
        {{
            "checklist_items": [
                {{"task": "task description"}}
            ],
            "action_plans": [
                {{
                    "action": "action description",
                    "frequency": "DAILY/WEEKLY/MONTHLY",
                    "duration_days": number_of_days
                }}
            ]
        }}
        """

        response = self.model.generate_content(prompt)
        try:
            result = response.text
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            json_str = result[start_idx:end_idx]
            
            parsed = json.loads(json_str)
                        
            today = datetime.now().date()
            for plan in parsed.get('action_plans', []):
                # Ensure duration_days is an integer (default to 7 if None)
                duration = plan.get('duration_days', 7)
                if duration is None or not isinstance(duration, int):
                    duration = 7  # Default duration
                
                # plan.pop('duration_days', None)  # Remove from final response
                plan['start_date'] = today.isoformat()
                plan['end_date'] = (today + timedelta(days=duration)).isoformat()
                
            return parsed
        except Exception as e:
            print(f"Error processing LLM response: {e}")
            return {
                'checklist_items': [],
                'action_plans': []
            } 


class ReminderService:
    @staticmethod
    def create_schedule_plan_reminders(action_plan):
        print(f"Creating schedule reminder for action plan: {action_plan}")
        
        try:
            """New patient notes cancel any previously scheduled actionable steps."""
            # Cancel existing active reminders & action plans for the patient
            patient = action_plan.note.doctor_patient.patient
            patient.reminders.filter(completed=False).update(is_active=False)
            patient.action_plans.filter(is_active=True).update(is_active=False)
            
            start_date = timezone.make_aware(datetime.combine(datetime.strptime(action_plan.start_date, '%Y-%m-%d').date(), timezone.now().time()))
            
            if action_plan.frequency == ActionPlan.Frequency.DAILY:
                delta = timedelta(days=1)
            elif action_plan.frequency == ActionPlan.Frequency.WEEKLY:
                delta = timedelta(weeks=1)
            elif action_plan.frequency == ActionPlan.Frequency.MONTHLY:
                delta = timedelta(days=30)
            elif action_plan.frequency == ActionPlan.Frequency.CUSTOM and action_plan.custom_schedule:
                return
                        
            current_date = start_date
            sequence = 1
            created_reminders = []
            
            for _ in range(action_plan.duration_days):
                reminder = Reminder.objects.create(
                    action_plan=action_plan,
                    patient=patient,
                    title=action_plan.action,
                    scheduled_for=current_date,
                    description=action_plan.action,
                    is_active=True,
                    sequence_number=sequence
                )
                created_reminders.append(reminder)
                current_date += delta
                sequence += 1
            
            # set the current action plan to be active
            action_plan.is_active = True
            action_plan.save()
            
            # Schedule first reminder
            first_reminder = action_plan.reminders.first()
            print(f"Attempting to schedule first reminder: {first_reminder}")
            
            if first_reminder:
                try:                   
                    # Print task info for debugging
                    print(f"Task registered: {send_reminder_email.name}")
            
                    # Schedule the reminder
                    # result = send_reminder_email.apply_async(
                    #     args=[first_reminder.id],
                    #     eta=first_reminder.scheduled_for
                    # )
                    
                    result = app.send_task(
                        'send_reminder_email',
                        args=[first_reminder.id],
                        eta=first_reminder.scheduled_for
                    )
                    print(f"Successfully scheduled reminder: {result}")
                    
                except (OperationalError, ConnectionRefusedError) as e:
                    print(f"Celery/Redis connection error: {e}")
                    print(f"Detailed error: {traceback.format_exc()}")
                    print("Please ensure Redis is running and Celery worker is started")
                else:
                    print("No reminders were created!")
                
            return created_reminders
                    
        except Exception as e:
            print(f"Error creating reminders: {e}")
            raise

    @staticmethod
    def handle_checkin(reminder):
        if reminder.completed and reminder.is_active:
            return False

        current_time = timezone.now()
        action_plan = reminder.action_plan
        
        # Mark current reminder as completed
        reminder.completed = True
        reminder.completed_at = current_time
        reminder.save()
        
        """if the patient has to take a drug, a day, for 7 days and misses one day only (doesn't check-in once), 
        this means the reminder runs for 8 days."""
        # If checked in after scheduled date, create a new day at the end
        if current_time.date() > reminder.scheduled_for.date():
            # Get the last reminder in sequence
            last_reminder = Reminder.objects.filter(
                action_plan=action_plan
            ).order_by('-sequence_number').first()

            # Create a new reminder for the missed day
            new_last_date = last_reminder.scheduled_for + timedelta(days=1)
            Reminder.objects.create(
                action_plan=action_plan,
                patient=reminder.patient,
                title=reminder.title,
                description=reminder.description,
                scheduled_for=new_last_date,
                sequence_number=last_reminder.sequence_number + 1,
                is_active=True
            )

        # Find the next uncompleted reminder in sequence
        next_reminder = Reminder.objects.filter(
            action_plan=action_plan,
            completed=False,
            is_active=True,
            sequence_number__gt=reminder.sequence_number
        ).order_by('sequence_number').first()

        if next_reminder:
            # If check-in was late, adjust the next reminder's schedule
            if current_time > reminder.scheduled_for:
                # Calculate how late the check-in was
                time_difference = current_time - reminder.scheduled_for
                
                # Schedule next reminder for tomorrow at the same time as original schedule
                next_day = current_time + timedelta(days=1)
                original_time = reminder.scheduled_for.time()
                next_reminder.scheduled_for = datetime.combine(next_day.date(), original_time)
                next_reminder.save()
                
                # next_reminder.scheduled_for = current_time + timedelta(days=1)
                # next_reminder.save()

                # Adjust all subsequent reminders
                subsequent_reminders = Reminder.objects.filter(
                    action_plan=action_plan,
                    completed=False,
                    sequence_number__gt=next_reminder.sequence_number,
                    is_active=True
                )
                
                # Shift all remaining reminders
                for subsequent in subsequent_reminders:
                    subsequent.scheduled_for += time_difference
                    subsequent.save()
                    
            try:
                app.send_task(
                    'send_reminder_email',
                    args=[next_reminder.id],
                    eta=next_reminder.scheduled_for
                )
                print(f"Scheduled next reminder for: {next_reminder.scheduled_for}")
            except Exception as e:
                print(f"Error scheduling next reminder: {e}")

        return True 