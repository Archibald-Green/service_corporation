# Generated by Django 4.2.5 on 2025-04-19 10:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('portal_app', '0006_department_folder_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='authuser',
            options={'managed': False},
        ),
        migrations.AlterModelOptions(
            name='department',
            options={'managed': False},
        ),
        migrations.AlterModelOptions(
            name='userdepartmentmapping',
            options={'managed': False},
        ),
        migrations.AlterModelTable(
            name='linked',
            table='portal.linked',
        ),
        migrations.AlterModelTable(
            name='user',
            table='portal.users',
        ),
    ]
