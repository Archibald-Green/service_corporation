import os
from .base import BaseProvider

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "energo")

class EnergoProvider(BaseProvider):
    @property
    def name(self) -> str:
        return "energo"

    async def fetch_meters_info(self) -> str:
        return open(os.path.join(FIXTURES, "energo_devices.csv"), encoding="utf-8").read()

    async def fetch_readings_su(self) -> str:
        return open(os.path.join(FIXTURES, "energo_device_data.csv"), encoding="utf-8").read()