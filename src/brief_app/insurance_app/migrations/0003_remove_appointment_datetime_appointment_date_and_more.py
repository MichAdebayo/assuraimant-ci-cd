# Generated by Django 5.1.5 on 2025-01-30 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("insurance_app", "0002_appointment"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="appointment",
            name="datetime",
        ),
        migrations.AddField(
            model_name="appointment",
            name="date",
            field=models.DateField(default="2025-02-03"),
        ),
        migrations.AddField(
            model_name="appointment",
            name="time",
            field=models.CharField(default=2, max_length=10),
            preserve_default=False,
        ),
    ]
