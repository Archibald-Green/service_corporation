from rest_framework import viewsets
from meter_app.models import ErcData, ReadingsSU , EnergoDevice ,EnergoDeviceData ,IotMeter ,IotMeterData
from meter_app.api.serializers import ErcDataSerializer, ReadingsSuSerializer ,EnergoDeviceSerializer ,EnergoDeviceDataSerializer ,IotMeterSerializer ,IotMeterDataSerializer

class ErcDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ErcData.objects.using('meter').all()
    serializer_class = ErcDataSerializer

class ReadingsSuViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReadingsSU.objects.using('meter').all()
    serializer_class = ReadingsSuSerializer
    
    
class EnergoDeviceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EnergoDevice.objects.using("meter").all()
    serializer_class = EnergoDeviceSerializer

class EnergoDeviceDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EnergoDeviceData.objects.using("meter").all()
    serializer_class = EnergoDeviceDataSerializer

class IotMeterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IotMeter.objects.using("meter").all()
    serializer_class = IotMeterSerializer

class IotMeterDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IotMeterData.objects.using("meter").all()
    serializer_class = IotMeterDataSerializer