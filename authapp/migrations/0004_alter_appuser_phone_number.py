# Generated by Django 5.1.1 on 2025-03-19 10:45

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authapp', '0003_alter_appuser_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appuser',
            name='phone_number',
            field=models.CharField(default='+911234567890', max_length=15, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')]),
        ),
    ]
