from django.test import TestCase
from django.core.management import call_command
from rest_framework.test import APIClient
from django.urls import reverse

from meter_app.models import (
    ErcData, ReadingsSU,
    EnergoDevice, EnergoDeviceData,
    IotMeter, IotMeterData,
)

class ImportMeterAppTest(TestCase):
    databases = ['meter',]

    def test_import_karagandawater(self):
        self.assertEqual(ErcData.objects.using('meter').count(), 0)
        self.assertEqual(ReadingsSU.objects.using('meter').count(), 0)
        call_command('import_karagandawater')
        self.assertGreater(ErcData.objects.using('meter').count(), 0)
        self.assertGreater(ReadingsSU.objects.using('meter').count(), 0)

    def test_import_energo(self):
        self.assertEqual(EnergoDevice.objects.using('meter').count(), 0)
        self.assertEqual(EnergoDeviceData.objects.using('meter').count(), 0)
        call_command('import_energo')
        self.assertGreater(EnergoDevice.objects.using('meter').count(), 0)
        self.assertGreater(EnergoDeviceData.objects.using('meter').count(), 0)

    def test_import_iot(self):
        self.assertEqual(IotMeter.objects.using('meter').count(), 0)
        self.assertEqual(IotMeterData.objects.using('meter').count(), 0)
        call_command('import_iot')
        self.assertGreater(IotMeter.objects.using('meter').count(), 0)
        self.assertGreater(IotMeterData.objects.using('meter').count(), 0)


class ApiMeterAppTest(TestCase):
    databases = ['meter',]

    def setUp(self):
        # наполняем тестовую БД данными
        call_command('import_karagandawater')
        call_command('import_energo')
        call_command('import_iot')
        self.client = APIClient()

    def test_erc_data_list(self):
        url = reverse('erc-data-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)

    def test_readings_su_list(self):
        url = reverse('readings-su-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()) > 0)

    def test_energo_devices_list(self):
        url = reverse('energo-devices-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()) > 0)

    def test_energo_data_list(self):
        url = reverse('energo-data-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()) > 0)

    def test_iot_meters_list(self):
        url = reverse('iot-meters-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()) > 0)

    def test_iot_data_list(self):
        url = reverse('iot-data-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()) > 0)