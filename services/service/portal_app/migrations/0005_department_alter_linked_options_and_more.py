
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portal_app', '0004_remove_authuser_user_id_authuser_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Название отдела', max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text='Описание отдела (необязательно)', null=True)),
            ],
            options={
                'db_table': 'departments',
            },
        ),
        migrations.AlterModelOptions(
            name='linked',
            options={'managed': False},
        ),
        migrations.CreateModel(
            name='UserDepartmentMapping',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='department_mapping', serialize=False, to='portal_app.user')),
                ('department', models.ForeignKey(blank=True, help_text='Отдел, в котором работает пользователь', null=True, on_delete=django.db.models.deletion.SET_NULL, to='portal_app.department')),
            ],
            options={
                'db_table': 'user_department_mappings',
            },
        ),
    ]
