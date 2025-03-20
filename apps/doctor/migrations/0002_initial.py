# Generated by Django 5.1.7 on 2025-03-20 16:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('doctor', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='doctorpatient',
            name='doctor',
            field=models.ForeignKey(limit_choices_to={'user_type': 'DOCTOR'}, on_delete=django.db.models.deletion.CASCADE, related_name='doctor_patients', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='doctorpatient',
            name='patient',
            field=models.ForeignKey(limit_choices_to={'user_type': 'PATIENT'}, on_delete=django.db.models.deletion.CASCADE, related_name='patient_doctors', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='doctornote',
            name='doctor_patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='doctor.doctorpatient'),
        ),
        migrations.AlterUniqueTogether(
            name='doctorpatient',
            unique_together={('doctor', 'patient')},
        ),
    ]
