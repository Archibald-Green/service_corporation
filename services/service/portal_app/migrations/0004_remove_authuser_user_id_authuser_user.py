# Generated by Django 4.2.5 on 2025-03-11 14:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portal_app', '0003_authuser_alter_user_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authuser',
            name='user_id',
        ),
        migrations.AddField(
            model_name='authuser',
            name='user',
            field=models.ForeignKey(blank=True, db_column='user_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='portal_app.user'),
        ),
    ]
