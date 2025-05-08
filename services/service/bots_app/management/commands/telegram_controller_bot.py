# bots_app/management/commands/run_controller_bot.py

import os
from functools import wraps
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from asgiref.sync import sync_to_async

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

from bots_app.creds.botTOKENS import telegraim_api_cont
from meter_app.models import Controller, MeterUser, Address, UserArea, Seal, Reading

# ——— состояния FSM ———
(
    AUTH_LOGIN,
    AUTH_PASSWORD,
    SELECT_LANG,
    MAIN_MENU,
    INPUT_READ_LS,
    INPUT_COLD,
    INPUT_HOT,
    INPUT_SEAL_LS,
    INPUT_SEAL_REASON,
    INPUT_SEAL_TYPE,
    INPUT_SEAL_DATE,
    INPUT_SEAL_SLOT,
) = range(12)


def login_markup():
    return ReplyKeyboardMarkup(
        [["🔐 Авторизоваться"]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def lang_markup():
    return ReplyKeyboardMarkup(
        [["Русский", "Қазақша"]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def main_menu_markup(lang="ru"):
    if lang == "kz":
        return ReplyKeyboardMarkup([
            ["💧 Көрсеткіштер", "📝 Пломба"],
            ["📋 Барлық ЛС аймағы"],
            ["🔄 Тілді ауыстыру", "🚪 Шығу"],
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            ["💧 Показания воды", "📝 Опломбирование"],
            ["📋 Все ЛС района"],
            ["🔄 Сменить язык", "🚪 Выйти"],
        ], resize_keyboard=True)


def login_required(func):
    @wraps(func)
    async def wrapped(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if "controller_id" not in ctx.user_data:
            await update.message.reply_text(
                "❗ Сначала авторизуйтесь:",
                reply_markup=login_markup()
            )
            return AUTH_LOGIN
        return await func(update, ctx)
    return wrapped


class Command(BaseCommand):
    help = "Запустить Telegram-бота для контролёров"

    def handle(self, *args, **options):
        app = ApplicationBuilder().token(telegraim_api_cont).build()

        conv = ConversationHandler(
            entry_points=[
                # Любой входящий текст до авторизации — уводит в AUTH_LOGIN
                MessageHandler(filters.ALL, start),
            ],
            states={
                AUTH_LOGIN: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, auth_login),
                ],
                AUTH_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, auth_password),
                ],
                SELECT_LANG: [
                    MessageHandler(filters.Regex("^(Русский|Қазақша)$"), set_lang),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
                MAIN_MENU: [
                    MessageHandler(filters.Regex("^(💧|Көрсеткіштер)"), menu_readings),
                    MessageHandler(filters.Regex("^(📝|Пломба)"), menu_seals),
                    MessageHandler(filters.Regex("^(📋)"), show_all_ls),
                    MessageHandler(filters.Regex(r"^(🔄\s*Сменить язык|🔄\s*Тілді ауыстыру)$"), choose_language),
                    MessageHandler(filters.Regex(r"^🔄 Тілді ауыстыру$"), choose_language),
                    MessageHandler(filters.Regex("^(🚪|Выйти|Шығу)$"), cancel),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
                INPUT_READ_LS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, read_ls),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
                INPUT_COLD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, read_cold),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
                INPUT_HOT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, read_hot),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
                INPUT_SEAL_LS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, seal_ls),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
                INPUT_SEAL_REASON: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, seal_reason),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
                INPUT_SEAL_TYPE: [
                    MessageHandler(filters.Regex("^(Холодная|Горячая)$"), seal_type),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
                INPUT_SEAL_DATE: [
                    CallbackQueryHandler(process_seal_date, pattern=r"^seal_date:"),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
                INPUT_SEAL_SLOT: [
                    CallbackQueryHandler(process_seal_slot, pattern=r"^slot:"),
                    MessageHandler(filters.ALL, fallback_to_menu),
                ],
            },
            fallbacks=[MessageHandler(filters.Command("cancel"), cancel)],
            per_message=False,
        )

        app.add_handler(conv)
        app.run_polling()


# ——— fallback на возврат в меню ———
async def fallback_to_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    await update.message.reply_text(
        "❌ Неправильный ввод, возвращаю в главное меню.",
        reply_markup=main_menu_markup(lang)
    )
    return MAIN_MENU


# ——— хендлеры ———

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "🔐 Пожалуйста, авторизуйтесь:",
        reply_markup=login_markup()
    )
    return AUTH_LOGIN


async def auth_login(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # нажатие кнопки
    if text == "🔐 Авторизоваться":
        await update.message.reply_text(
            "🔐 Пожалуйста, авторизуйтесь:",
            reply_markup=login_markup()
        )
        return AUTH_LOGIN

    # проверяем логин
    try:
        ctrl = await sync_to_async(Controller.objects.using("meter").get)(username=text)
    except Controller.DoesNotExist:
        await update.message.reply_text("❌ Логин не найден, попробуйте ещё раз:")
        return AUTH_LOGIN

    ctx.user_data["controller_id"] = ctrl.id
    ctx.user_data["area_id"]       = ctrl.area_id

    await update.message.reply_text("Введите пароль:")
    return AUTH_PASSWORD


async def auth_password(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    pwd = update.message.text.strip()
    cid = ctx.user_data["controller_id"]
    try:
        await sync_to_async(Controller.objects.using("meter").get)(id=cid, password=pwd)
    except Controller.DoesNotExist:
        await update.message.reply_text("❌ Неверный пароль, попробуйте ещё раз:")
        return AUTH_PASSWORD

    # после пароля сразу выбор языка
    await update.message.reply_text(
        "Выберите язык / Тілді таңдаңыз:", reply_markup=lang_markup()
    )
    return SELECT_LANG


async def set_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    lang = "kz" if choice == "Қазақша" else "ru"
    ctx.user_data["lang"] = lang

    welcome = "✅ Успешно вошли! Что дальше?" if lang=="ru" else "✅ Сәтті кірдіңіз! Келесі қадамды таңдаңыз:"
    await update.message.reply_text(welcome, reply_markup=main_menu_markup(lang))
    return MAIN_MENU

@login_required
async def choose_language(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # смена языка из меню
    await update.message.reply_text("Выберите язык / Тілді таңдаңыз:", reply_markup=lang_markup())
    return SELECT_LANG


@login_required
async def show_all_ls(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    area = ctx.user_data["area_id"]
    uas = await sync_to_async(list)(
        UserArea.objects.using("meter")
            .filter(area_id=area)
            .select_related("user__address")
    )
    if not uas:
        msg = lang=="kz" and "Аймақта абоненттер жоқ." or "В вашем районе ещё нет абонентов."
        await update.message.reply_text(msg)
    else:
        lines = []
        for ua in uas:
            mu = ua.user
            try:
                a = mu.address
                addr = f"{a.street}, д. {a.building}"
                if a.apartment:
                    addr += f", кв. {a.apartment}"
            except Address.DoesNotExist:
                addr = lang=="kz" and "мекенжай жоқ" or "адрес не задан"
            lines.append(f"{mu.number} — {addr}")
        header = lang=="kz" and "📋 Барлық ЛС аймағы:" or "📋 Все ЛС района:"
        await update.message.reply_text(header + "\n" + "\n".join(lines))

    prompt = lang=="kz" and "Келесі?" or "Что дальше?"
    await update.message.reply_text(prompt, reply_markup=main_menu_markup(lang))
    return MAIN_MENU


# ——— Показания воды ———

@login_required
async def menu_readings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    area = ctx.user_data["area_id"]
    uas = await sync_to_async(list)(
        UserArea.objects.using("meter")
            .filter(area_id=area)
            .select_related("user")
    )
    if not uas:
        await update.message.reply_text(
            lang=="kz" and "Аймақта абоненттер жоқ." or "В вашем районе нет абонентов.",
            reply_markup=main_menu_markup(lang)
        )
        return MAIN_MENU

    nums = [ua.user.number for ua in uas]
    prompt = (lang=="kz" and "📘 Есепшот нөмірін енгізіңіз:" 
                    or "📘 Введите лицевой счёт:")
    await update.message.reply_text(prompt + "\n" + "\n".join(nums))
    return INPUT_READ_LS


@login_required
async def read_ls(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    ls = update.message.text.strip()
    ok = await sync_to_async(
        MeterUser.objects.using("meter").filter(number=ls).exists
    )()
    if not ok:
        await update.message.reply_text(
            lang=="kz" and "❌ Есепшот табылмады." or "❌ ЛС не найден.",
            reply_markup=main_menu_markup(lang)
        )
        return MAIN_MENU

    ctx.user_data["ls"] = ls
    await update.message.reply_text(
        lang=="kz" and "❄️ Суық көрсеткіш енгізіңіз:" or "❄️ Введите показание холодной воды:"
    )
    return INPUT_COLD


@login_required
async def read_cold(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    try:
        cold = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(
            lang=="kz" and "❌ Қате сан." or "❌ Некорректное число.",
            reply_markup=main_menu_markup(lang)
        )
        return MAIN_MENU

    ctx.user_data["cold"] = cold
    await update.message.reply_text(
        lang=="kz" and "🔥 Ыстық көрсеткіш енгізіңіз:" or "🔥 Теперь — показание горячей воды:"
    )
    return INPUT_HOT


@login_required
async def read_hot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    try:
        hot = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(
            lang=="kz" and "❌ Қате сан." or "❌ Некорректное число.",
            reply_markup=main_menu_markup(lang)
        )
        return MAIN_MENU

    ls   = ctx.user_data["ls"]
    cold = ctx.user_data["cold"]
    uid  = ctx.user_data["controller_id"]
    mu   = await sync_to_async(MeterUser.objects.using("meter").get)(number=ls)

    # одна запись cold+hot
    await sync_to_async(Reading.objects.using("meter").create)(
        user_id      = mu.id,
        entity       = ls,
        punumber     = ls,
        readings     = cold,
        reading2     = hot,
        createdate   = timezone.now(),
        code         = "",
        disabled     = False,
        meterid      = 0,
        disconnected = False,
        corrected    = False,
        isactual     = True,
        sourcecode   = "both",
        yearmonth    = timezone.now().strftime("%Y%m"),
        restricted   = False,
        consumption  = int(cold + hot),
        operatorid   = uid,
        erc_meter_id = 0,
    )

    text = lang=="kz" and f"✅ Көрсеткіштер сақталды:\n❄️ {cold}\n🔥 {hot}" \
                        or f"✅ Показания сохранены:\n❄️ {cold}\n🔥 {hot}"
    await update.message.reply_text(text, reply_markup=main_menu_markup(lang))
    return MAIN_MENU


# ——— Опломбирование ———

@login_required
async def menu_seals(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    area = ctx.user_data["area_id"]
    uas = await sync_to_async(list)(
        UserArea.objects.using("meter")
            .filter(area_id=area)
            .select_related("user")
    )
    if not uas:
        await update.message.reply_text(
            lang=="kz" and "Аймақта абоненттер жоқ." or "В вашем районе нет абонентов.",
            reply_markup=main_menu_markup(lang)
        )
        return MAIN_MENU

    nums = [ua.user.number for ua in uas]
    prompt = lang=="kz" and "📝 Есепшот нөмірін енгізіңіз:" or "📝 Введите ЛС для опломбирования:"
    await update.message.reply_text(prompt + "\n" + "\n".join(nums))
    return INPUT_SEAL_LS


@login_required
async def seal_ls(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    ls = update.message.text.strip()
    ok = await sync_to_async(MeterUser.objects.using("meter").filter(number=ls).exists)()
    if not ok:
        await update.message.reply_text(
            lang=="kz" and "❌ Есепшот табылмады." or "❌ ЛС не найден.",
            reply_markup=main_menu_markup(lang)
        )
        return MAIN_MENU

    ctx.user_data["ls"] = ls
    await update.message.reply_text(
        lang=="kz" and "Пломба себебін жазыңыз:" or "Укажите причину опломбирования:"
    )
    return INPUT_SEAL_REASON


@login_required
async def seal_reason(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    ctx.user_data["reason"] = update.message.text.strip()
    kb = ReplyKeyboardMarkup([["Холодная", "Горячая"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        lang=="kz" and "Суды таңдаңыз:\n1️⃣ Суық\n2️⃣ Ыстық" or "Для какого типа воды опломбирование?",
        reply_markup=kb
    )
    return INPUT_SEAL_TYPE


@login_required
async def seal_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    kind = update.message.text.strip()
    ctx.user_data["seal_kind"] = kind.lower()
    today = date.today()
    buttons = [
        InlineKeyboardButton(
            (today + timedelta(days=i)).strftime("%d.%m"),
            callback_data=f"seal_date:{(today + timedelta(days=i)).isoformat()}"
        ) for i in range(14)
    ]
    kb = [buttons[i:i+4] for i in range(0, len(buttons), 4)]
    await update.message.reply_text(
        lang=="kz" and "🗓 Күнді таңдаңыз:" or "🗓 Выберите дату:",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    return INPUT_SEAL_DATE


@login_required
async def process_seal_date(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    q = update.callback_query
    await q.answer()
    sel = date.fromisoformat(q.data.split(":", 1)[1])
    ctx.user_data["date"] = sel
    slots = InlineKeyboardMarkup([[ 
        InlineKeyboardButton("🕘 До обеда", callback_data="slot:morning"),
        InlineKeyboardButton("🕒 После обеда", callback_data="slot:afternoon"),
    ]])
    await q.message.edit_text(
        lang=="kz" and "⏰ Уақытты таңдаңыз:" or "⏰ Выберите слот:",
        reply_markup=slots
    )
    return INPUT_SEAL_SLOT


@login_required
async def process_seal_slot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = ctx.user_data.get("lang", "ru")
    q = update.callback_query
    await q.answer()
    code = q.data.split(":", 1)[1]
    slot_label = lang=="kz" and ("Таңертең","Күні бойы")[0 if code=="morning" else 1] \
                or ("До обеда","После обеда")[0 if code=="morning" else 1]

    ls     = ctx.user_data["ls"]
    reason = ctx.user_data["reason"]
    kind   = ctx.user_data["seal_kind"]
    sel    = ctx.user_data["date"]
    uid    = ctx.user_data["controller_id"]

    exists = await sync_to_async(
        Seal.objects.using("meter")
            .filter(scheduledate=sel, type=code, status="new")
            .exists
    )()
    if exists:
        await q.answer(lang=="kz" and "❌ Бұл уақыт бос емес." or "❌ Слот занят.", show_alert=True)
        return await process_seal_date(update, ctx)

    mu = await sync_to_async(MeterUser.objects.using("meter").get)(number=ls)
    await sync_to_async(Seal.objects.using("meter").create)(
        user            = mu,
        txt             = reason,
        createdate      = timezone.now(),
        type            = code,
        entity          = ls,
        phone           = "",
        status          = "new",
        ishot           = (kind=="горячая"),
        iscold          = (kind=="холодная"),
        iselect         = False,
        operatorid      = uid,
        verificationcode= "",
        verificationphone="",
        aktnumber       = "",
        scheduledate    = sel
    )

    msg = (
        f"📤 {lang=='kz' and 'Өтініш қабылданды!' or 'Заявка принята!'}\n"
        f"{lang=='kz' and 'Есепшот' or 'ЛС'}: {ls}\n"
        f"{lang=='kz' and 'Себеп' or 'Причина'}: {reason}\n"
        f"{lang=='kz' and 'Су түрі' or 'Тип'}: {kind}\n"
        f"{lang=='kz' and 'Күн' or 'Дата'}: {sel.strftime('%d.%m.%Y')}\n"
        f"{lang=='kz' and 'Уақыт' or 'Слот'}: {slot_label}"
    )
    await q.message.edit_text(msg)
    await q.message.reply_text(lang=="kz" and "Келесі?" or "Что дальше?", reply_markup=main_menu_markup(lang))
    return MAIN_MENU


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "🚪 " + (ctx.user_data.get("lang")=="kz" and "Шығу. Қайта авторизация үшін басыңыз:" 
                                        or "Выход. Чтобы начать заново — нажмите:"),
        reply_markup=login_markup()
    )
    return ConversationHandler.END
