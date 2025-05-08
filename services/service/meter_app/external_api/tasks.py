# meter_app/external_api/tasks.py
from celery import shared_task
import asyncio
from .karWater import KaragandaWater
from .parser import parse_meters_info, parse_readings_su

# @shared_task
# def import_from_karagandawater():
#     prov = KaragandaWater()
#     loop = asyncio.get_event_loop()

#     raw_info = loop.run_until_complete(prov.fetch_meters_info())
#     parse_meters_info(raw_info)

#     raw_su   = loop.run_until_complete(prov.fetch_readings_su())
#     parse_readings_su(raw_su)

@shared_task
def import_from_karagandawater():
    loop = asyncio.new_event_loop()
    prov = KaragandaWater()
    raw_info = loop.run_until_complete(prov.fetch_meters_info())
    parse_meters_info(raw_info)
    raw_su = loop.run_until_complete(prov.fetch_readings_su())
    parse_readings_su(raw_su)
    return f"Imported from {prov.name}"