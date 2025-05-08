import asyncio
from django.core.management.base import BaseCommand, CommandError

from meter_app.external_api.karWater import KaragandaWater
from meter_app.external_api.parser import parse_meters_info, parse_readings_su

class Command(BaseCommand):
    help = "Импорт данных MetersInfo и Readings_SU из провайдера KaragandaWater"

    def handle(self, *args, **options):
        self.stdout.write("Запуск импорта из KaragandaWater…")
        prov = KaragandaWater()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            raw_info = loop.run_until_complete(prov.fetch_meters_info())
            parse_meters_info(raw_info)
            self.stdout.write(self.style.SUCCESS("  • MetersInfo импортированы."))

            raw_su = loop.run_until_complete(prov.fetch_readings_su())
            parse_readings_su(raw_su)
            self.stdout.write(self.style.SUCCESS("  • Readings_SU импортированы."))

        except Exception as e:
            raise CommandError(f"Ошибка импорта: {e}")
        finally:
            loop.close()
