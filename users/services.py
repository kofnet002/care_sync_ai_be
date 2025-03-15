import google.generativeai as genai
from datetime import datetime, timedelta
from django.conf import settings
import json
from django.utils import timezone
from .models import Reminder, ActionPlan
from .tasks import send_reminder_email

class LLMService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

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
            # Clean up the response to get only the JSON part
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            json_str = result[start_idx:end_idx]
            
            # Parse the JSON response
            parsed = json.loads(json_str)
            
            # Add dates to action plans
            today = datetime.now().date()
            for plan in parsed.get('action_plans', []):
                duration = plan.pop('duration_days', 7)  # Default to 7 days if not specified
                plan['start_date'] = today.isoformat()
                plan['end_date'] = (today + timedelta(days=duration)).isoformat()
            
            return parsed
        except Exception as e:
            # Log the error and return a default structure
            print(f"Error processing LLM response: {e}")
            return {
                'checklist_items': [],
                'action_plans': []
            } 

class ReminderScheduler:
    @staticmethod
    def schedule_plan_reminders(action_plan):
        # Cancel existing active reminders for the patient
        action_plan.patient.reminders.filter(completed=False).delete()
        
        # Create new reminders based on action plan
        start_date = timezone.now()
        for _ in range(action_plan.duration_days):
            reminder = Reminder.objects.create(
                action_plan=action_plan,
                patient=action_plan.patient,
                title=action_plan.title,
                description=action_plan.description,
                scheduled_for=start_date
            )
            # Schedule email reminder
            send_reminder_email.apply_async(
                args=[reminder.id],
                eta=start_date
            )
            start_date += timedelta(days=1)

    @staticmethod
    def handle_checkin(reminder):
        if not reminder.completed:
            reminder.completed = True
            reminder.save()
            
            # Find next uncompleted reminder
            next_reminder = Reminder.objects.filter(
                action_plan=reminder.action_plan,
                completed=False
            ).first()
            
            if next_reminder:
                # Schedule next reminder email
                send_reminder_email.apply_async(
                    args=[next_reminder.id],
                    eta=timezone.now() + timedelta(days=1)
                )
            
            return True
        return False 