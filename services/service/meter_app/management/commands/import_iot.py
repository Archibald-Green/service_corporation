from django.core.management.base import BaseCommand
import asyncio

from meter_app.external_api.iot import IotProvider
from meter_app.external_api.parser import parse_iot_meters, parse_iot_meter_data

class Command(BaseCommand):
    help = "Импорт из IotProvider"

    def handle(self, *args, **opts):
        prov = IotProvider()
        loop = asyncio.new_event_loop()
        try:
            raw1 = loop.run_until_complete(prov.fetch_meters_info())
            parse_iot_meters(raw1)
            raw2 = loop.run_until_complete(prov.fetch_readings_su())
            parse_iot_meter_data(raw2)
            self.stdout.write(self.style.SUCCESS("IOT импортированы."))
        finally:
            loop.close()