import os
from .base import BaseProvider

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "iot")

class IotProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "iot"

    async def fetch_meters_info(self) -> str:
        return open(os.path.join(FIXTURES, "iot_meters.csv"), encoding="utf-8").read()

    async def fetch_readings_su(self) -> str:
        return open(os.path.join(FIXTURES, "iot_meter_data.csv"), encoding="utf-8").read()