from django.shortcuts import render

from rest_framework import viewsets
from meter_app.api.serializers import ErcDataSerializer, ReadingsSuSerializer
from meter_app.models import ErcData, ReadingsSU

class ErcDataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Только чтение ERC‑данных
    """
    # если вы пишете в отдельную БД alias='meter', то:
    queryset = ErcData.objects.using('meter').all()
    serializer_class = ErcDataSerializer

class ReadingsSuViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Только чтение показаний SU
    """
    queryset = ReadingsSU.objects.using('meter').all()
    serializer_class = ReadingsSuSerializer