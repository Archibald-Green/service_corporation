import os
from .base import BaseProvider

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "karwater")

class KaragandaWater(BaseProvider):
    @property
    def name(self) -> str:
        return "karagandawater"

    async def fetch_meters_info(self) -> str:
        return open(os.path.join(FIXTURES, "MetersInfo.txt"), encoding="utf-8").read()

    async def fetch_readings_su(self) -> str:
        return open(os.path.join(FIXTURES, "Readings_SU.csv"), encoding="utf-8").read()