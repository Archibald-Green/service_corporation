# bots_app/views.py

import os
import django
from datetime import date, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from twilio.twiml.messaging_response import MessagingResponse
from django.utils import timezone

# ——— Django setup ———
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service.settings")
django.setup()

from meter_app.models import WhatsAppSession, MeterUser, Meter, Seal
from bots_app.management.commands.bot_utils import (
    save_seal_request,
    save_or_update_reading,
    get_last_record
)

TECH_PHONE = "+7 701 123 45 67"

# все тексты на двух языках
TEXTS = {
    'ru': {
        'lang_prompt':     "🌐 Выберите язык:\n1️⃣ Русский\n2️⃣ Қазақша",
        'welcome':         "👋 Добро пожаловать!",
        'menu':            "1️⃣ Опломбирование\n2️⃣ Показания воды\n3️⃣ Техподдержка\n4️⃣ Сменить язык",
        'support':         f"☎️ Техподдержка: {TECH_PHONE}",
        'enter_ls_seal':   "📝 Введите лицевой счёт для опломбирования:",
        'enter_ls_read':   "📘 Введите лицевой счёт для показаний:",
        'invalid_choice':  "❌ Пожалуйста, введите *1*, *2*, *3* или *4*.",
        'ls_not_found':    "❌ ЛС не найден, возвращаю в меню.",
        'enter_reason':    "Укажите причину опломбирования:",
        'choose_water':    "Выберите тип воды:\n1️⃣ Холодная\n2️⃣ Горячая",
        'invalid_water':   "❌ Неправильный выбор, возвращаю в меню.",
        'choose_date':     "🗓 Выберите дату (ответьте номером):",
        'invalid_date':    "❌ Неверный номер, возвращаю в меню.",
        'date_busy':       "❌ На этот день уже есть заявка, возвращаю в меню.",
        'choose_slot':     "⏰ Выберите слот:\n1️⃣ До обеда\n2️⃣ После обеда",
        'invalid_slot':    "❌ Неправильный выбор, возвращаю в меню.",
        'seal_success':    "✅ Заявка принята!\nЛС: {ls}\nПричина: {reason}\nТип воды: {kind}\nДата: {date}\nСлот: {slot}",
        'enter_cold':      "❄️ Введите показание ХОЛОДНОЙ воды:",
        'invalid_number':  "❌ Некорректное число, возвращаю в меню.",
        'enter_hot':       "🔥 Теперь — показание ГОРЯЧЕЙ воды:",
        'reading_success': "✅ Показания сохранены:\n❄️ {cold}\n🔥 {hot}",
        'cannot_edit':     "❌ Нельзя изменить показания после 24 ч или если меньше предыдущего, возвращаю в меню.",
        'error':           "❌ Что-то пошло не так, возвращаю в меню.",
    },
    'kz': {
        'lang_prompt':     "🌐 Тілді таңдаңыз:\n1️⃣ Русский\n2️⃣ Қазақша",
        'welcome':         "👋 Қош келдіңіз!",
        'menu':            "1️⃣ Пломба қою\n2️⃣ Су көрсеткіштері\n3️⃣ Тех қолдау\n4️⃣ Тілді ауыстыру",
        'support':         f"☎️ Тех қолдау: {TECH_PHONE}",
        'enter_ls_seal':   "📝 Есепшот нөмірін енгізіңіз:",
        'enter_ls_read':   "📘 Көрсеткіш үшін есепшот нөмірін енгізіңіз:",
        'invalid_choice':  "❌ Өтінеміз, *1*, *2*, *3* немесе *4* енгізіңіз.",
        'ls_not_found':    "❌ Есепшот табылмады, басты мәзірге ораламыз.",
        'enter_reason':    "Пломба себебін жазыңыз:",
        'choose_water':    "Суды таңдаңыз:\n1️⃣ Суық\n2️⃣ Ыстық",
        'invalid_water':   "❌ Қате таңдау, басты мәзірге ораламыз.",
        'choose_date':     "🗓 Күнді таңдаңыз (нөмірі):",
        'invalid_date':    "❌ Қате нөмір, басты мәзірге ораламыз.",
        'date_busy':       "❌ Осы күнге өтініш бар, басты мәзірге ораламыз.",
        'choose_slot':     "⏰ Уақытты таңдаңыз:\n1️⃣ Таңертең\n2️⃣ Күні бойы",
        'invalid_slot':    "❌ Қате таңдау, басты мәзірге ораламыз.",
        'seal_success':    "✅ Өтініш қабылданды!\nЕсепшот: {ls}\nСебеп: {reason}\nСу түрі: {kind}\nКүн: {date}\nУақыт: {slot}",
        'enter_cold':      "❄️ Суық көрсеткіш енгізіңіз:",
        'invalid_number':  "❌ Қате сан, басты мәзірге ораламыз.",
        'enter_hot':       "🔥 Ыстық көрсеткіш енгізіңіз:",
        'reading_success': "✅ Көрсеткіштер сақталды:\n❄️ {cold}\n🔥 {hot}",
        'cannot_edit':     "❌ 24 сағаттан кейін немесе аз көрсеткішті түзетуге болмайды, басты мәзірге ораламыз.",
        'error':           "❌ Қате, басты мәзірге ораламыз.",
    }
}

def get_session(phone_raw):
    phone = phone_raw.replace("whatsapp:", "")
    sess, _ = WhatsAppSession.objects.get_or_create(
        phone=phone,
        defaults={'data': {}, 'state': ''}
    )
    if sess.data is None:
        sess.data = {}
    return sess

@csrf_exempt
def whatsapp_webhook(request):
    incoming = request.POST
    from_     = incoming.get("From", "")
    body      = incoming.get("Body", "").strip()
    resp      = MessagingResponse()
    msg       = resp.message()

    sess  = get_session(from_)
    state = sess.state or ""
    data  = sess.data
    lang  = data.get('lang', 'ru')

    # — выбор языка —
    if state in ("", "END"):
        msg.body(TEXTS['ru']['lang_prompt'])
        sess.state = "CHOOSE_LANG"

    elif state == "CHOOSE_LANG":
        if body == "1":
            data['lang'] = 'ru'
        elif body == "2":
            data['lang'] = 'kz'
        else:
            msg.body("❌ 1 или 2 енгізіңіз / введите 1 или 2")
            sess.save()
            return HttpResponse(str(resp), content_type="text/xml")

        lang = data['lang']
        msg.body(f"{TEXTS[lang]['welcome']}\n{TEXTS[lang]['menu']}")
        sess.state = "CHOOSE_ACTION"

    # — главное меню —
    elif state == "CHOOSE_ACTION":
        lang = data.get('lang', 'ru')
        if body == "1":
            msg.body(TEXTS[lang]['enter_ls_seal'])
            sess.state = "SEAL_ACCOUNT"
        elif body == "2":
            msg.body(TEXTS[lang]['enter_ls_read'])
            sess.state = "READING_ACCOUNT"
        elif body == "3":
            msg.body(TEXTS[lang]['support'])
            sess.state = "END"
            sess.data  = {}
        elif body == "4":
            msg.body(TEXTS['ru']['lang_prompt'])
            sess.state = "CHOOSE_LANG"
        else:
            msg.body(f"{TEXTS[lang]['invalid_choice']}\n{TEXTS[lang]['menu']}")

    # — опломбирование —
    elif state == "SEAL_ACCOUNT":
        lang = data.get('lang', 'ru')
        if not Meter.objects.using('meter').filter(punumber=body).exists():
            msg.body(TEXTS[lang]['ls_not_found'] + "\n" + TEXTS[lang]['menu'])
            sess.state = "CHOOSE_ACTION"
        else:
            data['ls'] = body
            msg.body(TEXTS[lang]['enter_reason'])
            sess.state = "SEAL_REASON"

    elif state == "SEAL_REASON":
        lang = data.get('lang', 'ru')
        data['reason'] = body
        msg.body(TEXTS[lang]['choose_water'])
        sess.state = "SEAL_TYPE"

    elif state == "SEAL_TYPE":
        lang = data.get('lang', 'ru')
        if body == "1":
            data['kind'] = TEXTS[lang]['choose_water'].split('\n')[0].split(' ')[1]
        elif body == "2":
            data['kind'] = TEXTS[lang]['choose_water'].split('\n')[1].split(' ')[1]
        else:
            msg.body(TEXTS[lang]['invalid_water'] + "\n" + TEXTS[lang]['menu'])
            sess.state = "CHOOSE_ACTION"
            sess.data  = {}
            sess.save()
            return HttpResponse(str(resp), content_type="text/xml")

        today = date.today()
        lines = [f"{i+1}. {(today+timedelta(days=i)).strftime('%d.%m')}" for i in range(14)]
        msg.body(TEXTS[lang]['choose_date'] + "\n" + "\n".join(lines))
        sess.state = "SEAL_DATE"

    elif state == "SEAL_DATE":
        lang = data.get('lang', 'ru')
        try:
            idx = int(body) - 1
            if idx < 0 or idx >= 14:
                raise ValueError
        except ValueError:
            msg.body(TEXTS[lang]['invalid_date'] + "\n" + TEXTS[lang]['menu'])
            sess.state = "CHOOSE_ACTION"
        else:
            sel = date.today() + timedelta(days=idx)
            mu  = MeterUser.objects.using('meter').get(number=data['ls'])
            if Seal.objects.using('meter').filter(user_id=mu.id, scheduledate=sel).exists():
                msg.body(TEXTS[lang]['date_busy'] + "\n" + TEXTS[lang]['menu'])
                sess.state = "CHOOSE_ACTION"
            else:
                data['date'] = sel.isoformat()
                msg.body(TEXTS[lang]['choose_slot'])
                sess.state = "SEAL_SLOT"

    elif state == "SEAL_SLOT":
        lang = data.get('lang', 'ru')
        if body not in ("1","2"):
            msg.body(TEXTS[lang]['invalid_slot'] + "\n" + TEXTS[lang]['menu'])
            sess.state = "CHOOSE_ACTION"
        else:
            slot_code  = "morning" if body == "1" else "afternoon"
            slot_label = {
                'ru':("До обеда","После обеда"),
                'kz':("Таңертең","Күні бойы")
            }[lang][0 if body == "1" else 1]

            sel = date.fromisoformat(data['date'])
            save_seal_request(
                telegram_id=from_,
                account    = data['ls'],
                reason     = data['reason'],
                date       = sel,
                timeslot   = slot_code,
                water_type = data['kind'].lower()
            )
            msg.body(TEXTS[lang]['seal_success'].format(
                ls=data['ls'],
                reason=data['reason'],
                kind=data['kind'],
                date=sel.strftime('%d.%m.%Y'),
                slot=slot_label
            ))
            sess.state = "END"
            sess.data  = {}

    # — показания воды —
    elif state == "READING_ACCOUNT":
        lang = data.get('lang', 'ru')
        if not Meter.objects.using('meter').filter(punumber=body).exists():
            msg.body(TEXTS[lang]['ls_not_found'] + "\n" + TEXTS[lang]['menu'])
            sess.state = "CHOOSE_ACTION"
        else:
            data['ls'] = body
            msg.body(TEXTS[lang]['enter_cold'])
            sess.state = "READING_COLD"

    elif state == "READING_COLD":
        lang = data.get('lang', 'ru')
        try:
            cold = float(body.replace(",","."))
        except ValueError:
            msg.body(TEXTS[lang]['invalid_number'] + "\n" + TEXTS[lang]['menu'])
            sess.state = "CHOOSE_ACTION"
        else:
            last = get_last_record(from_, data['ls'])
            prev = last.readings if last else None
            if prev is not None and cold < prev:
                msg.body(f"❌ {cold} < предыдущего({prev})\n" + TEXTS[lang]['menu'])
                sess.state = "CHOOSE_ACTION"
            else:
                data['cold'] = cold
                msg.body(TEXTS[lang]['enter_hot'])
                sess.state = "READING_HOT"

    elif state == "READING_HOT":
        lang = data.get('lang', 'ru')
        try:
            hot = float(body.replace(",","."))
        except ValueError:
            msg.body(TEXTS[lang]['invalid_number'] + "\n" + TEXTS[lang]['menu'])
            sess.state = "CHOOSE_ACTION"
        else:
            last = get_last_record(from_, data['ls'])
            prev = last.reading2 if last else None
            if prev is not None and hot < prev:
                msg.body(f"❌ {hot} < предыдущего({prev})\n" + TEXTS[lang]['menu'])
                sess.state = "CHOOSE_ACTION"
            else:
                data['hot'] = hot
                now = timezone.now()
                try:
                    save_or_update_reading(from_, data['ls'], data['cold'], "cold", now)
                    save_or_update_reading(from_, data['ls'], hot,           "hot",  now)
                except ValueError as e:
                    msg.body(f"❌ {e}\n\n{TEXTS[lang]['menu']}")
                    sess.state = "CHOOSE_ACTION"
                else:
                    msg.body(TEXTS[lang]['reading_success'].format(
                        cold=data['cold'], hot=hot
                    ))
                    sess.state = "END"
                    sess.data  = {}

    else:
        # непредвиденное — возвращаем в меню
        lang = data.get('lang','ru')
        msg.body(TEXTS[lang]['error'] + "\n" + TEXTS[lang]['menu'])
        sess.state = "CHOOSE_ACTION"
        sess.data  = {}

    sess.data = data
    sess.save()
    return HttpResponse(str(resp), content_type="text/xml")
