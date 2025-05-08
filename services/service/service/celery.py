import os
from celery import Celery
from celery.schedules import crontab
from django.core.management import call_command

# 1) Устанавливаем переменную окружения для Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service.settings")

app = Celery("service")

# 2) Загружаем конфиг Django (и все настройки CELERY_*)
app.config_from_object("django.conf:settings", namespace="CELERY")

# 3) Автоматически находим задачи в каждом app/tasks.py
app.autodiscover_tasks()

# 4) Добавляем ваше расписание
app.conf.beat_schedule = {
    # пример: импорт из KaragandaWater с 1 по 5 число в 02:00
    "karagandawater-monthly": {
        "task": "meter_app.external_api.tasks.import_from_karagandawater",
        "schedule": crontab(day_of_month="1-5", hour=2, minute=0),
    },
    # сюда можно добавить другие провайдеры
}

# (опционально) дефолтный queue
app.conf.task_default_queue = "default"

def import_from_karagandawater():
    # здесь вызываем вашу команду
    call_command("import_karagandawater", database="meter")
    

app.conf.beat_schedule = {
    "karagandawater-monthly": {
        "task": "meter_app.tasks.import_from_karagandawater",
        "schedule": crontab(day_of_month="1-5", hour=2, minute=0),
    },
    # можно добавить другие провайдеры:
    # "another-provider": { ... }
}