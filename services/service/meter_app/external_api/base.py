from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """
    Базовый интерфейс для всех провайдеров внешних данных.
    Каждый провайдер должен быть в состоянии:
      - получить актуальный файл с описанием счётчиков (MetersInfo)
      - получить файл с показаниями (Readings_SU)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Уникальное имя провайдера (например, "karagandawater").
        Полезно для логирования и динамической регистрации провайдеров.
        """
        ...

    @abstractmethod
    async def fetch_meters_info(self) -> str:
        """
        Асинхронно забирает и возвращает содержимое файла MetersInfo.txt (текст с табами).
        """
        ...

    @abstractmethod
    async def fetch_readings_su(self) -> str:
        """
        Асинхронно забирает и возвращает содержимое файла Readings_SU.csv (текст с точкой‑запятой).
        """
        ...
