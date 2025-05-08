import csv
from io import StringIO
from decimal import Decimal
from django.db import transaction
from meter_app.models import ErcData, ReadingsSU, Incorrect, IotMeter, IotMeterData, EnergoDevice , EnergoDeviceData
from datetime import datetime

import json 

def _parse_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default

def _parse_bool(value: str) -> bool:
    """
    True/False, 1/0, yes/no — любые «истинные» значения возвращают True.
    """
    v = (value or "").strip().lower()
    return v in ("1", "true", "yes", "y")

def parse_meters_info(raw: str):
    """
    Парсит таб-делимитед файл MetersInfo.txt по регламенту
    и сохраняет в модель ErcData.
    """
    reader = csv.DictReader(StringIO(raw), delimiter="\t")
    objs = []
    for row in reader:
        objs.append(ErcData(
            abonent           = row.get("Абонент", "").strip(),
            entity            = row.get("ЛС", "").strip(),
            surname           = row.get("Фамилия", "").strip(),
            given_name        = row.get("Имя", "").strip(),
            fathers_name      = row.get("Отчество", "").strip(),
            entity_gar_su     = row.get("Л.с.", "").strip(),
            entity_type       = row.get("Тип ЛС", "").strip(),
            sector            = row.get("Бригада", "").strip(),
            team              = row.get("Участок", "").strip(),
            city              = row.get("Город", "").strip(),
            street_group      = row.get("Группа улиц", "").strip(),
            street_prefix     = row.get("Тип улицы", "").strip(),
            street            = row.get("Улица", "").strip(),
            house_prefix      = row.get("Префикс", "").strip(),
            house_type        = row.get("Тип строения", "").strip(),
            house_number      = row.get("Номер", "").strip(),
            litera            = row.get("Литера", "").strip(),
            flat              = row.get("Кв", "").strip(),
            flat_test         = row.get("Литера помещения", "").strip(),
            flat_type         = row.get("Тип помещения", "").strip(),
            object            = row.get("Объект", "").strip(),
            registered_amount = row.get("Жильцы", "").strip(),
            floor             = row.get("Этаж", "").strip(),
            phone_number1     = row.get("Телефон 1", "").strip(),
            phone_number2     = row.get("Телефон 2", "").strip(),
            iin               = row.get("ИИН", "").strip(),
            whaelthy_code     = row.get("Код благ.", "").strip(),
            tarif_type        = row.get("Тип тарифа", "").strip(),
            tarif_water       = row.get("Тариф,вода", "").strip(),
            tarif_saverage    = row.get("Тариф,кан.", "").strip(),
            tu                = row.get("т/у", "").strip(),
            meter_type        = row.get("Тип водомера", "").strip(),
            meter_subtype     = row.get("Подтип водомера", "").strip(),
            meter_number      = row.get("Номер водомера", "").strip(),
            verification_date = row.get("Дата поверки", "").strip(),
            readings_date     = row.get("Дата показания", "").strip(),
            readings          = row.get("Показание", "").strip(),
            norma             = row.get("Тип тарифа", "").strip(),  # нормативный тариф
            test1             = row.get("Тариф,вода", "").strip(), # норматив вода
            test2             = row.get("Тариф,кан.", "").strip(), # норматив кан.
            area              = row.get("Площадь полива", "").strip(),
            area_type         = row.get("Жильцы/площадь полива", "").strip(),
            seal_date         = row.get("Дата пломбы", "").strip(),
            seal_number       = row.get("Пломба", "").strip(),
            source            = row.get("Источник", "").strip() if row.get("Источник") else "",
            poliv             = row.get("Полив", "").strip(),
            tu_saverage       = row.get("т/у кан.", "").strip(),
            saverage_type     = row.get("Тип кан.", "").strip(),
            start_date        = row.get("Дата нач.", "").strip(),
            meter_id          = row.get("Код ИПУ", "").strip(),
            blank_number      = row.get("Номер бланка", "").strip(),
            tur               = row.get("Тур", "").strip(),
            bit_depth         = row.get("Разрядность", "").strip(),
            reagings_date     = row.get("Дата показания", "").strip(),
        ))
    # Сохраняем всё пакетом
    with transaction.atomic(using='meter'):
        ErcData.objects.using('meter').bulk_create(objs)


def parse_readings_su(raw: str):
    """
    Парсим Readings_SU.csv: удачные — в ReadingsSU,
    невалидные — в Incorrect.
    """
    reader = csv.DictReader(StringIO(raw), delimiter=";")
    good, bad = [], []
    for row in reader:
        try:
            val = row.get("RValue", "").strip()
            acct = row.get("AccountId", "").strip()
            # проверяем регламент: RValue должно быть > 0 и <= 30
            if not val or float(val) <= 0 or float(val) > 30:
                raise ValueError("Не по регламенту")
            good.append(ReadingsSU(
                abonent_id = row.get("AbonentId", "").strip(),
                account_id = acct,
                point_num  = row.get("PointNum", "").strip(),
                rdate      = row.get("RDate", "").strip(),
                rvalue     = val,
                meter_id   = row.get("MeterId", "").strip(),
            ))
        except Exception as e:
            bad.append(Incorrect(
                abonent_id   = row.get("AbonentId", "").strip(),
                account_id   = row.get("AccountId", "").strip(),
                point_num    = row.get("PointNum", "").strip(),
                rdate        = row.get("RDate", "").strip(),
                rvalue       = row.get("RValue", "").strip(),
                meter_id     = row.get("MeterId", "").strip(),
                error_reason = str(e),
            ))

    with transaction.atomic(using='meter'):
        if good:
            ReadingsSU.objects.using('meter').bulk_create(good)
        if bad:
            Incorrect.objects.using('meter').bulk_create(bad)


def parse_energo_devices(raw: str):
    """
    Разбирает CSV energo_devices.csv и сохраняет в модель EnergoDevice.
    Ожидается заголовок, соответствующий полям из БД.
    """
    reader = csv.DictReader(StringIO(raw))
    objs = []
    for d in reader:
        objs.append(EnergoDevice(
            ctime            = datetime.fromisoformat(d.get("ctime")),
            dmodel_id        = _parse_int(d.get("dmodel_id")),
            dmodel_sensor    = d.get("dmodel_sensor", "").strip(),
            serial_num       = d.get("serial_num", "").strip(),
            device_id        = _parse_int(d.get("device_id")),
            folder_id        = _parse_int(d.get("folder_id")),
            location         = d.get("location", "").strip(),
            physical_person  = _parse_bool(d.get("physical_person")),
            owner_name       = d.get("owner_name", "").strip(),
            beg_value        = Decimal(d.get("beg_value") or 0),
            phones           = d.get("phones", "").strip(),
            sector_id        = _parse_int(d.get("sector_id")),
            mount_id         = _parse_int(d.get("mount_id")),
            mount            = d.get("mount", "").strip(),
            archives         = _parse_int(d.get("archives")),
            alias            = d.get("alias", "").strip(),
            enable           = _parse_bool(d.get("enable")),
            resource_id      = _parse_int(d.get("resource_id")),
            resource_inx     = _parse_int(d.get("resource_inx")),
            scheme_id        = _parse_int(d.get("scheme_id")),
            dscan            = d.get("dscan", "").strip(),
            calc             = d.get("calc", "").strip(),
            account          = d.get("account", "").strip(),
            date_next        = None,  # если нет даты в CSV, иначе парсить через datetime.strptime
            date_verification= None,  # то же самое
            created_at       = datetime.now(),  # или из CSV, если есть
        ))
    EnergoDevice.objects.using('meter').bulk_create(objs)

def parse_energo_device_data(raw: str):
    """
    Разбирает CSV energo_device_data.csv и сохраняет в модель EnergoDeviceData.
    """
    reader = csv.DictReader(StringIO(raw))
    objs = []
    for d in reader:
        objs.append(EnergoDeviceData(
            value        = Decimal(d.get("value") or 0),
            value_error  = Decimal(d.get("value_error") or 0),
            rvalue_id    = _parse_int(d.get("rvalue_id")),
            c            = _parse_int(d.get("c")),
            ctime        = datetime.fromisoformat(d.get("ctime")),
            datetime     = datetime.fromisoformat(d.get("datetime")),
            type_arch_orig = _parse_int(d.get("type_arch_orig")),
            type_arch    = _parse_int(d.get("type_arch")),
            success      = _parse_bool(d.get("success")),
            error_arch   = d.get("error_arch", "").strip(),
            created_at   = datetime.now(),
            device_id    = _parse_int(d.get("device_id")),
        ))
    EnergoDeviceData.objects.using('meter').bulk_create(objs)
    
    
def parse_iot_meters(raw: str):
    """
    Разбираем CSV iot_meters.csv → создаём IotMeter
    """
    reader = csv.DictReader(StringIO(raw))
    objs = []
    for d in reader:
        objs.append(IotMeter(
            modem_id      = _parse_int(d.get("modem_id")),
            port          = _parse_int(d.get("port")),
            serial_number = d.get("serial_number", "").strip(),
            consumer      = d.get("consumer", "").strip(),
            account_id    = d.get("account_id", "").strip(),
            last_reading  = Decimal(d.get("last_reading") or 0),
            created_at    = datetime.fromisoformat(d.get("created_at")),
        ))
    IotMeter.objects.using('meter').bulk_create(objs)

def parse_iot_meter_data(raw: str):
    """
    Разбираем CSV iot_meter_data.csv → создаём IotMeterData
    """
    reader = csv.DictReader(StringIO(raw))
    objs = []
    for d in reader:
        objs.append(IotMeterData(
            dt            = datetime.fromisoformat(d.get("dt")),
            type_of_data  = d.get("type_of_data", "").strip(),
            rssi          = _parse_int(d.get("rssi")),
            snr           = Decimal(d.get("snr") or 0),
            num_of_pulse  = _parse_int(d.get("num_of_pulse")),
            reading       = Decimal(d.get("reading") or 0),
            data          = d.get("data") and json.loads(d.get("data")),
            battery_level = Decimal(d.get("battery_level") or 0),
            start_reading = Decimal(d.get("start_reading") or 0),
            diff_reading  = Decimal(d.get("diff_reading") or 0),
            created_at    = datetime.fromisoformat(d.get("created_at")),
            meter_id      = _parse_int(d.get("meter_id")),
        ))
    IotMeterData.objects.using('meter').bulk_create(objs)