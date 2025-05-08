from django.contrib import admin

from .models import ErcData, ReadingsSU, Incorrect
from django.apps import apps

# Получаем конфиг вашего приложения
app_config = apps.get_app_config('meter_app')

# Регистрируем каждую модель в админке
for model in app_config.get_models():
    admin.site.register(model)