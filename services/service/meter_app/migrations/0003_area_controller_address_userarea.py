# Generated by Django 4.2.5 on 2025-05-04 08:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('meter_app', '0002_whatsappsession'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Код района')),
                ('name', models.CharField(max_length=255, verbose_name='Название района')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
            ],
            options={
                'verbose_name': 'Район',
                'verbose_name_plural': 'Районы',
                'db_table': '"public"."areas"',
            },
        ),
        migrations.CreateModel(
            name='Controller',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=150, unique=True, verbose_name='Логин')),
                ('password', models.CharField(max_length=255, verbose_name='Пароль (хеш)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('area', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='controllers', to='meter_app.area', verbose_name='Район')),
            ],
            options={
                'verbose_name': 'Контроллёр',
                'verbose_name_plural': 'Контроллёры',
                'db_table': '"public"."controllers"',
            },
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street', models.CharField(max_length=255, verbose_name='Улица')),
                ('building', models.CharField(max_length=50, verbose_name='Дом / корпус')),
                ('apartment', models.CharField(blank=True, max_length=50, verbose_name='Кв./офис')),
                ('postal_code', models.CharField(blank=True, max_length=20, verbose_name='Почтовый индекс')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='address', to='meter_app.meteruser', verbose_name='Абонент (MeterUser)')),
            ],
            options={
                'verbose_name': 'Адрес ЛС',
                'verbose_name_plural': 'Адреса ЛС',
                'db_table': '"public"."addresses"',
            },
        ),
        migrations.CreateModel(
            name='UserArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата привязки')),
                ('area', models.ForeignKey(db_column='area_id', on_delete=django.db.models.deletion.CASCADE, related_name='user_links', to='meter_app.area', verbose_name='Район')),
                ('user', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, related_name='area_links', to='meter_app.meteruser', verbose_name='Абонент')),
            ],
            options={
                'verbose_name': 'Привязка абонента к району',
                'verbose_name_plural': 'Привязки абонентов к районам',
                'db_table': '"public"."user_areas"',
                'unique_together': {('user', 'area')},
            },
        ),
    ]
