from rest_framework import serializers
from meter_app.models import ErcData, ReadingsSU, EnergoDevice , EnergoDeviceData , IotMeter , IotMeterData

class ErcDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErcData
        fields = '__all__'

class ReadingsSuSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingsSU
        fields = '__all__'
        
class EnergoDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergoDevice
        fields = "__all__"

class EnergoDeviceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnergoDeviceData
        fields = "__all__"

class IotMeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = IotMeter
        fields = "__all__"

class IotMeterDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = IotMeterData
        fields = "__all__"