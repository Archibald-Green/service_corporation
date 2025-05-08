from rest_framework.routers import DefaultRouter
from .views import ErcDataViewSet, ReadingsSuViewSet ,EnergoDeviceViewSet ,EnergoDeviceDataViewSet ,IotMeterViewSet ,IotMeterDataViewSet

router = DefaultRouter()
router.register(r'erc-data',       ErcDataViewSet,            basename='erc-data')
router.register(r'readings-su',    ReadingsSuViewSet,         basename='readings-su')
router.register(r'energo-devices', EnergoDeviceViewSet,       basename='energo-devices')
router.register(r'energo-data',    EnergoDeviceDataViewSet,   basename='energo-data')
router.register(r'iot-meters',     IotMeterViewSet,           basename='iot-meters')
router.register(r'iot-data',       IotMeterDataViewSet,       basename='iot-data')

urlpatterns = router.urls