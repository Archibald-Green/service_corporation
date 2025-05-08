# bots_app/management/commands/telegram_client_bot.py

import os
import django
from datetime import date, timedelta
from django.utils import timezone

# ——— Django setup ———
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "service.settings")
django.setup()

from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.command import Command as AioCommand
from aiogram.filters.state import StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from bots_app.creds.botTOKENS import telegram_api
from meter_app.models import Seal, Meter, MeterUser
from .bot_utils import save_or_update_reading, get_last_record as _sync_get_last_record, save_seal_request

# ——— Тексты ———
TECH_PHONE = "+7 701 123 45 67"
TEXTS = {
    'ru': {
        'lang_prompt':  "🌐 Выберите язык:",
        'lang_buttons': ["Русский","Қазақша"],
        'welcome':      "👋 Добро пожаловать!",
        'menu':         ["📝 Опломбирование","💧 Показания воды"],
        'change_lang':  "🔄 Сменить язык",
        'support_label': "☎️ Техподдержка",
        'support_text':   f"☎️ Техподдержка: {TECH_PHONE}",
        'seal_account': "📝 Введите ЛС для опломбирования:",
        'seal_reason':  "Укажите причину:",
        'seal_type':    "Выберите вид воды:",
        'seal_date':    "🗓 Выберите дату (14 дн.):",
        'seal_slot':    "⏰ Выберите слот:",
        'read_account': "📘 Введите ЛС для показаний:",
        'read_cold':    "❄️ Холодная вода:",
        'read_hot':     "🔥 Горячая вода:",
        'invalid_ls':   "❌ ЛС не найден. Возвращаю в главное меню.",
        'invalid_num':  "❌ Некорректное число. Возвращаю в главное меню.",
        'invalid_choice':"❌ Некорректный выбор. Возвращаю в главное меню.",
        'success_seal': "📤 Заявка принята!\nЛС: {ls}\nПричина: {reason}\nВид: {kind}\nДата: {date}\nСлот: {slot}",
        'success_read': "✅ Показания:\n❄️ {cold}\n🔥 {hot}",
    },
    'kz': {
        'lang_prompt':  "🌐 Тілді таңдаңыз:",
        'lang_buttons': ["Русский","Қазақша"],
        'welcome':      "👋 Қош келдіңіз!",
        'menu':         ["📝 Пломба","💧 Көрсеткіштер"],
        'change_lang':  "🔄 Тілді ауыстыру",
        'support_label': "☎️ Тех қолдау",
        'support_text':  f"☎️ Тех қолдау: {TECH_PHONE}",
        'seal_account': "📝 Есепшот нөмірі:",
        'seal_reason':  "Себебін жазыңыз:",
        'seal_type':    "Суды таңдаңыз:",
        'seal_date':    "🗓 Күнді таңдаңыз (14 күн):",
        'seal_slot':    "⏰ Слот:",
        'read_account': "📘 Есепшот нөмірі:",
        'read_cold':    "❄️ Суық көрсеткіш:",
        'read_hot':     "🔥 Ыстық көрсеткіш:",
        'invalid_ls':   "❌ Есепшот жоқ. Басты мәзірге қайтамын.",
        'invalid_num':  "❌ Қате сан. Басты мәзірге қайтамын.",
        'invalid_choice':"❌ Қате таңдау. Басты мәзірге қайтамын.",
        'success_seal': "📤 Өтініш қабылданды!\nЕсепшот: {ls}\nСебеп: {reason}\nТүрі: {kind}\nКүн: {date}\nСлот: {slot}",
        'success_read': "✅ Көрсеткіштер:\n❄️ {cold}\n🔥 {hot}",
    }
}

# ——— Асинхронные обёртки ———
get_last_record = sync_to_async(_sync_get_last_record)
save_seal       = sync_to_async(save_seal_request)

@sync_to_async
def check_ls_exists(ls: str) -> bool:
    return Meter.objects.using('meter').filter(punumber=ls).exists()

@sync_to_async
def get_user_by_number(number: str) -> MeterUser:
    return MeterUser.objects.using('meter').get(number=number)

@sync_to_async
def seal_exists(mu_id: int, scheduledate: date) -> bool:
    return Seal.objects.using('meter').filter(user_id=mu_id, scheduledate=scheduledate).exists()

@sync_to_async
def slot_taken(scheduledate: date, timeslot: str) -> bool:
    return Seal.objects.using('meter').filter(scheduledate=scheduledate, type=timeslot, status='new').exists()

@sync_to_async
def save_reading_entry(tid, acc, nv, wt, when):
    return save_or_update_reading(tid, acc, nv, wt, when)

# ——— States ———
class ClientStates(StatesGroup):
    choose_lang    = State()
    main_menu      = State()
    seal_account   = State()
    seal_reason    = State()
    seal_type      = State()
    seal_date      = State()
    seal_slot      = State()
    read_account   = State()
    read_cold      = State()
    read_hot       = State()

# ——— Keyboards ———
def lang_kb():
    opts = TEXTS['ru']['lang_buttons']
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=opts[0]), KeyboardButton(text=opts[1])]],
        resize_keyboard=True, one_time_keyboard=True
    )

def main_kb(lang):
    t = TEXTS[lang]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t['menu'][0]), KeyboardButton(text=t['menu'][1])],
            [ KeyboardButton(text=t['change_lang']), KeyboardButton(text=t['support_label']) ]
        ],
        resize_keyboard=True
    )

# ——— Handlers ———

# 1) Start & language
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(TEXTS['ru']['lang_prompt'], reply_markup=lang_kb())
    await state.set_state(ClientStates.choose_lang)

async def choose_lang(message: types.Message, state: FSMContext):
    lang = 'kz' if message.text == TEXTS['ru']['lang_buttons'][1] else 'ru'
    await state.update_data(lang=lang)
    t = TEXTS[lang]
    await message.answer(f"{t['welcome']}\n\n" + "\n".join(t['menu']), reply_markup=main_kb(lang))
    await state.set_state(ClientStates.main_menu)

async def cmd_support(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang','ru')
    # отправляем полный текст с номером
    await message.answer(TEXTS[lang]['support_text'], reply_markup=main_kb(lang))

# 2) Seal
async def cmd_seal(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('lang','ru')
    # чистим данные, но сохраняем язык и переводим в main_menu в конце
    await state.clear()
    await state.update_data(lang=lang)
    await message.answer(TEXTS[lang]['seal_account'], reply_markup=main_kb(lang))
    await state.set_state(ClientStates.seal_account)

async def seal_choose_account(message: types.Message, state: FSMContext):
    data = await state.get_data(); lang = data['lang']
    ls = message.text.strip()
    if not await check_ls_exists(ls):
        await message.answer(TEXTS[lang]['invalid_ls'], reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    await state.update_data(ls=ls)
    await message.answer(TEXTS[lang]['seal_reason'], reply_markup=main_kb(lang))
    await state.set_state(ClientStates.seal_reason)

async def seal_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    await state.update_data(reason=message.text.strip())
    # Правильно передавать keyboard как именованный аргумент
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Холодная"), KeyboardButton(text="Горячая")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer(TEXTS[lang]['seal_type'], reply_markup=kb)
    await state.set_state(ClientStates.seal_type)

async def seal_type(message: types.Message, state: FSMContext):
    data = await state.get_data(); lang = data['lang']
    kind = message.text.strip()
    if kind not in ("Холодная","Горячая"):
        await message.answer(TEXTS[lang]['invalid_choice'], reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    await state.update_data(kind=kind)
    today = date.today()
    btns = [InlineKeyboardButton(text=(today+timedelta(days=i)).strftime("%d.%m"), callback_data=f"seal_date:{(today+timedelta(days=i)).isoformat()}") for i in range(14)]
    await message.answer(TEXTS[lang]['seal_date'], reply_markup=InlineKeyboardMarkup(inline_keyboard=[btns[i:i+4] for i in range(0,14,4)]))
    await state.set_state(ClientStates.seal_date)

async def process_seal_date(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data(); lang = data['lang']
    sel = date.fromisoformat(callback_query.data.split(":",1)[1])
    await callback_query.answer()
    if sel < date.today() or await seal_exists((await get_user_by_number(data['ls'])).id, sel):
        await callback_query.message.answer(TEXTS[lang]['invalid_choice'], reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    await state.update_data(date=sel)
    slots = InlineKeyboardMarkup([[ InlineKeyboardButton(text="🕘 До обеда", callback_data="slot:morning"), InlineKeyboardButton(text="🕒 После обеда", callback_data="slot:afternoon") ]])
    await callback_query.message.delete()
    await callback_query.message.answer(TEXTS[lang]['seal_slot'], reply_markup=slots)
    await state.set_state(ClientStates.seal_slot)

async def process_seal_slot(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data(); lang = data['lang']
    code = callback_query.data.split(":",1)[1]
    await callback_query.answer()
    if await slot_taken(data['date'], code):
        return await callback_query.answer(TEXTS[lang]['invalid_choice'], show_alert=True)
    mu = await get_user_by_number(data['ls'])
    await sync_to_async(Seal.objects.using('meter').create)(
        user=mu, txt=data['reason'], createdate=timezone.now(),
        type=code, entity=data['ls'], phone="", status="new",
        ishot=(data['kind']=="Горячая"), iscold=(data['kind']=="Холодная"),
        iselect=False, operatorid=callback_query.from_user.id,
        verificationcode="", verificationphone="", aktnumber="", scheduledate=data['date']
    )
    slot_label = "До обеда" if code=="morning" else "После обеда"
    await callback_query.message.edit_text(TEXTS[lang]['success_seal'].format(
        ls=data['ls'], reason=data['reason'], kind=data['kind'],
        date=data['date'].strftime("%d.%m.%Y"), slot=slot_label
    ))
    await callback_query.message.answer(TEXTS[lang]['support'], reply_markup=main_kb(lang))
    await state.set_state(ClientStates.main_menu)

# 3) Readings
async def cmd_read(message: types.Message, state: FSMContext):
    data = await state.get_data(); lang = data.get('lang','ru')
    await state.clear(); await state.update_data(lang=lang)
    await message.answer(TEXTS[lang]['read_account'], reply_markup=main_kb(lang))
    await state.set_state(ClientStates.read_account)

async def process_read_ls(message: types.Message, state: FSMContext):
    data = await state.get_data(); lang = data['lang']
    ls = message.text.strip()
    if not await check_ls_exists(ls):
        await message.answer(TEXTS[lang]['invalid_ls'], reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    await state.update_data(ls=ls)
    await message.answer(TEXTS[lang]['read_cold'], reply_markup=main_kb(lang))
    await state.set_state(ClientStates.read_cold)

async def process_read_cold(message: types.Message, state: FSMContext):
    data = await state.get_data(); lang = data['lang']
    try:
        cold = float(message.text.replace(',','.'))
    except ValueError:
        await message.answer(TEXTS[lang]['invalid_num'], reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    prev = (await get_last_record(message.from_user.id, data['ls'])).readings or 0
    if cold < prev:
        await message.answer(f"❌ {cold} < {prev}", reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    try:
        await save_reading_entry(message.from_user.id, data['ls'], cold, "cold", message.date)
    except ValueError as e:
        await message.answer(str(e), reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    await state.update_data(cold=cold)
    await message.answer(TEXTS[lang]['read_hot'], reply_markup=main_kb(lang))
    await state.set_state(ClientStates.read_hot)

async def process_read_hot(message: types.Message, state: FSMContext):
    data = await state.get_data(); lang = data['lang']
    try:
        hot = float(message.text.replace(',','.'))
    except ValueError:
        await message.answer(TEXTS[lang]['invalid_num'], reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    prev = (await get_last_record(message.from_user.id, data['ls'])).reading2 or 0
    if hot < prev:
        await message.answer(f"❌ {hot} < {prev}", reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    try:
        await save_reading_entry(message.from_user.id, data['ls'], hot, "hot", message.date)
    except ValueError as e:
        await message.answer(str(e), reply_markup=main_kb(lang))
        return await state.set_state(ClientStates.main_menu)
    await message.answer(TEXTS[lang]['success_read'].format(cold=data['cold'], hot=hot), reply_markup=main_kb(lang))
    await state.set_state(ClientStates.main_menu)

# ——— Запуск ———
class Command(BaseCommand):
    help = "Запустить Telegram-бота для клиентов"
    def handle(self, *args, **options):
        bot = Bot(token=telegram_api)
        dp  = Dispatcher(storage=MemoryStorage())

        dp.message.register(cmd_start, AioCommand(commands=["start"]))
        dp.message.register(choose_lang, lambda m: m.text in TEXTS['ru']['lang_buttons'], StateFilter(ClientStates.choose_lang))

        dp.message.register(cmd_seal, lambda m: m.text in (TEXTS['ru']['menu'][0], TEXTS['kz']['menu'][0]), StateFilter(ClientStates.main_menu))
        dp.message.register(cmd_read, lambda m: m.text in (TEXTS['ru']['menu'][1], TEXTS['kz']['menu'][1]), StateFilter(ClientStates.main_menu))
        dp.message.register(cmd_support, lambda m: m.text in (TEXTS['ru']['support_label'], TEXTS['kz']['support_label']), StateFilter(ClientStates.main_menu))
        dp.message.register(cmd_start, lambda m: m.text in (TEXTS['ru']['change_lang'], TEXTS['kz']['change_lang']), StateFilter(ClientStates.main_menu))

        dp.message.register(seal_choose_account, StateFilter(ClientStates.seal_account))
        dp.message.register(seal_reason,         StateFilter(ClientStates.seal_reason))
        dp.message.register(seal_type,           StateFilter(ClientStates.seal_type))
        dp.callback_query.register(process_seal_date, lambda c: c.data.startswith("seal_date:"), StateFilter(ClientStates.seal_date))
        dp.callback_query.register(process_seal_slot, lambda c: c.data.startswith("slot:"), StateFilter(ClientStates.seal_slot))

        dp.message.register(process_read_ls,   StateFilter(ClientStates.read_account))
        dp.message.register(process_read_cold, StateFilter(ClientStates.read_cold))
        dp.message.register(process_read_hot,  StateFilter(ClientStates.read_hot))

        dp.run_polling(bot, skip_updates=True)
