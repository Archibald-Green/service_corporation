from django.core.management.base import BaseCommand, CommandError
import asyncio
from meter_app.external_api.energo import EnergoProvider
from meter_app.external_api.parser import parse_energo_devices, parse_energo_device_data

class Command(BaseCommand):
    help = "Импорт из EnergoProvider"

    def handle(self, *args, **opts):
        prov = EnergoProvider()
        loop = asyncio.new_event_loop()
        raw1 = loop.run_until_complete(prov.fetch_meters_info())
        parse_energo_devices(raw1)
        raw2 = loop.run_until_complete(prov.fetch_readings_su())
        parse_energo_device_data(raw2)
        self.stdout.write(self.style.SUCCESS("Energo импортированы."))