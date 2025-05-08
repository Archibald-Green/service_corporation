# bots_app/management/commands/bot_utils.py

import datetime
from django.utils import timezone
from meter_app.models import Reading, MeterUser, Seal

def get_last_record(telegram_id: int, account: str) -> Reading | None:
    try:
        mu = MeterUser.objects.using('meter').get(number=account)
    except MeterUser.DoesNotExist:
        return None

    return (
        Reading.objects
        .using('meter')
        .filter(user_id=mu.id, punumber=account)
        .order_by('-createdate')
        .first()
    )

def save_or_update_reading(
    telegram_id: int,
    account: str,
    new_value: float,
    water_type: str,
    when: datetime.datetime
) -> Reading:
    now = timezone.now()
    # создание/поиск MeterUser
    defaults_mu = {
        'isactual': False, 'joined': now, 'last_logged_in': now,
        'type': '', 'intent': '', 'intententity': '', 'intentmeter': '',
        'intentmetercode': '', 'intentseal': '', 'name': '',
        'isadmin': False, 'username': '', 'phone': '',
        'lang': '', 'return_menu': '',
    }
    mu, _ = MeterUser.objects.using('meter').get_or_create(
        number=account, defaults=defaults_mu
    )
    last = get_last_record(telegram_id, account)
    if last:
        prev_val = last.readings if water_type == 'cold' else last.reading2
        if new_value < prev_val:
            raise ValueError(f"Новое показание {new_value} < предыдущее {prev_val}")
        if now - last.createdate > datetime.timedelta(hours=24):
            raise ValueError("Прошло больше 24 часов — править нельзя")

    ym = when.strftime("%Y%m")
    defaults_rd = {
        'entity': last.entity if last else '',
        'code': last.code if last else '',
        'disabled': last.disabled if last else False,
        'meterid': last.meterid if last else 0,
        'disconnected': last.disconnected if last else False,
        'corrected': last.corrected if last else False,
        'isactual': last.isactual if last else False,
        'sourcecode': last.sourcecode if last else '',
        'restricted': last.restricted if last else False,
        'consumption': last.consumption if last else 0,
        'operator_id': last.operator_id if last else 0,
        'erc_meter_id': last.erc_meter_id if last else 0,
        # ставим нужное поле readings или reading2
        'readings': new_value if water_type == 'cold' else (last.readings if last else 0.0),
        'reading2': new_value if water_type == 'hot' else (last.reading2 if last else 0.0),
        'createdate': when,
    }
    reading, created = Reading.objects.using('meter').get_or_create(
        user_id=mu.id, punumber=account, yearmonth=ym, defaults=defaults_rd
    )
    if not created:
        if water_type == 'cold':
            reading.readings = new_value
            fields = ['readings', 'createdate']
        else:
            reading.reading2 = new_value
            fields = ['reading2', 'createdate']
        reading.createdate = when
        reading.save(update_fields=fields)
    return reading

def save_seal_request(
    telegram_id: int,
    account: str,
    reason: str,
    date: datetime.date,
    timeslot: str,
    water_type: str = None   # <-- новый параметр
) -> Seal:
    """
    Сохраняет заявку на опломбирование с scheduledate=date,
    слотом timeslot ('morning' или 'afternoon') и опциональным
    water_type ('hot'/'cold' или русск. 'Горячая'/'Холодная').
    """
    now = timezone.now()

    # 0) Найти или создать MeterUser
    defaults_mu = {
        'isactual': False,
        'joined': now,
        'last_logged_in': now,
        'type': '',
        'intent': '',
        'intententity': '',
        'intentmeter': '',
        'intentmetercode': '',
        'intentseal': '',
        'name': '',
        'isadmin': False,
        'username': '',
        'phone': '',
        'lang': '',
        'return_menu': '',
    }
    mu, _ = MeterUser.objects.using('meter').get_or_create(
        number=account,
        defaults=defaults_mu
    )

    # Определяем, холодная или горячая
    kind = (water_type or '').lower()
    ishot = kind in ('hot', 'горячая')
    iscold = kind in ('cold', 'холодная')

    # 1) Создать саму Seal-заявку, заполняя все NOT NULL-поля:
    return Seal.objects.using('meter').create(
        user_id         = mu.id,
        txt             = reason,
        createdate      = now,
        type            = timeslot,
        entity          = '',       # если нужно, можно сюда вписать account
        phone           = '',
        status          = 'new',
        ishot           = ishot,
        iscold          = iscold,
        iselect         = False,
        operatorid      = 0,
        verificationcode= '',
        verificationphone='',
        aktnumber       = '',
        scheduledate    = date,
        # answer и answer_date nullable — можно опустить
    )
