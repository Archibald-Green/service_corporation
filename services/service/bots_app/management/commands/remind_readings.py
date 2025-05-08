# bots_ap/management/commands/remind_readings.py
import os, django
from django.core.management.base import BaseCommand
from aiogram import Bot
from portal_app.models import User
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service.settings")
django.setup()

class Command(BaseCommand):
    help = "Напомнить пользователям дать показания"

    def handle(self, *args, **options):
        bot = Bot(token=os.getenv("TG_TOKEN"))
        for u in User.objects.exclude(telegram_id__isnull=True):
            bot.send_message(u.telegram_id,
                "⏰ Напоминаем: пожалуйста, дайте показания за месяц.")
