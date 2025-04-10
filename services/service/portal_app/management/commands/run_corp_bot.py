import os
import aiohttp
from django.core.management.base import BaseCommand
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from telegram import Update, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import check_password, make_password

from portal_app.models import User, AuthUser, Linked
from portal_app.creds.cred import botTOKEN
from urllib.parse import quote_plus

# Импорт функций из google_service.py
from .google_service import (
    get_drive_files_with_links,
    get_salary_by_iin,
    make_short_name_no_dots_for_user,
    get_vacation_by_user_and_job,
    get_payroll_by_user_from_google_sheet,
    format_payroll,
    save_payroll_to_pdf,
    get_drive_files_by_folder
)

# Состояния диалогов для обычных функций
WAITING_USERNAME = 1
WAITING_PASSWORD = 2
WAITING_JOB = 50
WAITING_LANGUAGE = 100
WAITING_PAYROLL_MONTH = 110
WAITING_PDF_CONFIRM = 120

# Состояния для админского диалога
ADMIN_MENU = 200
ADMIN_CHANGE_PASS_USERNAME = 210
ADMIN_CHANGE_PASS_NEW = 220
ADMIN_BROADCAST_MESSAGE = 230

AUTHORIZED_USERS = set()

# Клавиатуры
AUTHORIZED_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Помощь", "Отпуск", "Расчетный лист", "Язык"],
        ["Зарплата", "Документы", "Контакты", "Админка"]
    ],
    resize_keyboard=True
)
UNAUTHORIZED_KEYBOARD = ReplyKeyboardMarkup(
    [["Помощь", "Язык", "Авторизация"]],
    resize_keyboard=True
)
PDF_KEYBOARD = ReplyKeyboardMarkup([["Сохранить PDF", "Назад"]], resize_keyboard=True)

@sync_to_async
def get_user_department_folder(tg_id: int) -> str:
    """
    Возвращает folder_id из связанного отдела (из модели UserDepartmentMapping)
    для пользователя с заданным telegram_id.
    """
    user = User.objects.filter(telegram_id=tg_id).first()
    if user and hasattr(user, 'department_mapping') and user.department_mapping.department:
        # Предполагается, что в модели Department есть поле folder_id, настроенное через админку
        return user.department_mapping.department.folder_id
    return None
# Обёртки для работы с базой
@sync_to_async
def find_user_by_name(name: str) -> User | None:
    return User.objects.filter(name=name).first()

@sync_to_async
def find_auth_user_by_user(user: User) -> AuthUser | None:
    return AuthUser.objects.filter(user=user).first()

@sync_to_async
def save_user(user: User):
    user.save()

@sync_to_async
def log_to_linked(tg_id, iin, t_number):
    Linked.objects.create(
        telegram_id=tg_id,
        iin=iin or "",
        t_number=t_number or ""
    )

@sync_to_async
def find_user_by_telegram_id(tg_id: int) -> User | None:
    return User.objects.filter(telegram_id=tg_id).first()

@sync_to_async
def get_salary_async(iin: str):
    return get_salary_by_iin(iin)

@sync_to_async
def get_vacation_async(user_obj, job: str):
    return get_vacation_by_user_and_job(user_obj, job)

# Обёртка для поиска расчетного листа из Google Sheets
async_get_payroll_by_user = sync_to_async(get_payroll_by_user_from_google_sheet)

CONTACTS_TEXT = (
    "\n📞 Контакты отдела:\n\n"
    "• Оператор: 101\n"
    "• Бухгалтерия: 102\n"
    "• Отдел кадров: 103\n"
    "• Охрана: 104\n"
    "• Директор: 105"
)

# Асинхронная функция для вызова Google Apps Script,
# возвращающая URL PDF-файла (расчетного листа)
async def request_payroll_pdf(iin: str, month: str) -> str:
    iin_encoded = quote_plus(iin)
    month_encoded = quote_plus(month)
    url = f"https://script.google.com/macros/s/AKfycbwC9Fh_4tl5XrPP4dfAvI5jCboEADwAhUuRedkP4deQW4QSdkP6QdXFDzjfusMJxvbQKw/exec?iin={iin_encoded}&month={month_encoded}"
    print(f"[DEBUG] Отправляем запрос к: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"[ERROR] Google Script вернул статус {response.status}")
                return None
            text = await response.text()
            print(f"[DEBUG] Ответ от скрипта: {text[:300]}...")
            return text.strip()

def format_payroll_text(payroll: dict) -> str:
    return (
        f"ФИО: {payroll.get('ФИО')}\n"
        f"ИИН: {payroll.get('ИИН')}\n"
        f"Табельный номер: {payroll.get('Табельный номер')}\n"
        f"Должность: {payroll.get('Должность')}\n"
        f"Месяц: {payroll.get('Месяц')}\n"
        f"Оклад: {payroll.get('Оклад')}\n"
        f"Премия: {payroll.get('Премия')}\n"
        f"ИПН: {payroll.get('ИПН')}\n"
        f"ОПВ: {payroll.get('ОПВ')}\n"
        f"ОСМС: {payroll.get('ОСМС')}\n"
        f"Удержания: {payroll.get('Удержания')}\n"
        f"Итого к выплате: {payroll.get('Итого к выплате')}"
    )

###############################################################################
# Админпанель: меню и функции
###############################################################################
# Импорт формы для изменения пароля
from portal_app.forms import AuthUserForm

@sync_to_async
def update_auth_user_with_form(auth_user, data: dict) -> tuple[bool, dict]:
    form = AuthUserForm(data=data, instance=auth_user)
    if form.is_valid():
        form.save()
        return True, {}
    else:
        return False, form.errors

# Функция для получения списка всех пользователей
@sync_to_async
def get_all_users() -> str:
    users = User.objects.all()
    if not users:
        return "Нет пользователей."
    result = "Список пользователей:\n"
    for user in users:
        result += f"{user.id}. {user.name} {user.first_name} (Telegram: {user.telegram_id}, Админ: {user.isadmin})\n"
    return result

# Функция для получения логов (здесь для примера статичный ответ)
def get_latest_logs() -> str:
    return ("Логи:\n"
            "- Авторизация: 10 записей\n"
            "- Ошибки: 2 записи\n"
            "- Действия: 5 записей\n")

# Админская панель: стартовое меню
async def start_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    user_obj = await find_user_by_telegram_id(tg_id)
    lang = context.user_data.get("lang", "ru")
    if not user_obj or not user_obj.isadmin:
        msg = "У вас нет прав администратора." if lang == "ru" else "Сізде әкімшілік құқықтар жоқ."
        await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
        return ConversationHandler.END
    admin_keyboard = ReplyKeyboardMarkup(
        [
            ["Сменить пароль", "Просмотреть пользователей"],
            ["Просмотреть логи", "Рассылка"],
            ["Выход"]
        ],
        resize_keyboard=True
    )
    msg = "Выберите действие:" if lang == "ru" else "Іс-әрекетті таңдаңыз:"
    await update.message.reply_text(msg, reply_markup=admin_keyboard)
    return ADMIN_MENU

# Обработчик выбора действия в админском меню
async def admin_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")
    if choice == "Сменить пароль":
        await update.message.reply_text(
            "Введите имя пользователя, чей пароль вы хотите изменить:",
            reply_markup=AUTHORIZED_KEYBOARD
        )
        return ADMIN_CHANGE_PASS_USERNAME
    elif choice == "Просмотреть пользователей":
        users_list = await get_all_users()
        await update.message.reply_text(users_list, reply_markup=AUTHORIZED_KEYBOARD)
        # После показа возвращаем в меню
        return await start_admin_panel(update, context)
    elif choice == "Просмотреть логи":
        # Для примера используем статичные логи
        logs = get_latest_logs()
        await update.message.reply_text(logs, reply_markup=AUTHORIZED_KEYBOARD)
        return await start_admin_panel(update, context)
    elif choice == "Рассылка":
        await update.message.reply_text(
            "Введите сообщение для рассылки всем авторизованным пользователям:",
            reply_markup=AUTHORIZED_KEYBOARD
        )
        return ADMIN_BROADCAST_MESSAGE
    elif choice == "Выход":
        await update.message.reply_text("Выход из админпанели.", reply_markup=AUTHORIZED_KEYBOARD)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Неизвестная команда. Попробуйте еще раз.", reply_markup=AUTHORIZED_KEYBOARD)
        return ADMIN_MENU

# Диалог смены пароля
async def admin_change_pass_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_username = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")
    target_user = await find_user_by_name(target_username)
    if not target_user:
        msg = "Пользователь не найден." if lang == "ru" else "Пайдаланушы табылмады."
        await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
        return ConversationHandler.END
    context.user_data["target_user"] = target_user
    msg = f"Введите новый пароль для пользователя {target_username}:" if lang == "ru" else f"{target_username} үшін жаңа құпия сөзді енгізіңіз:"
    await update.message.reply_text(msg)
    return ADMIN_CHANGE_PASS_NEW

async def admin_change_pass_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_password = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")
    target_user = context.user_data.get("target_user")
    if not target_user:
        msg = "Ошибка: целевой пользователь не найден." if lang == "ru" else "Қате: мақсатты пайдаланушы табылмады."
        await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
        return ConversationHandler.END
    auth_user = await find_auth_user_by_user(target_user)
    if not auth_user:
        msg = "У данного пользователя не установлен пароль." if lang == "ru" else "Осы пайдаланушы үшін құпия сөз орнатылмаған."
        await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
        return ConversationHandler.END
    data = {'user': target_user.id, 'password_raw': new_password}
    success, errors = await update_auth_user_with_form(auth_user, data)
    if success:
        msg = f"Пароль для пользователя {target_user.name or target_user.first_name} успешно изменён." if lang == "ru" else f"{target_user.name or target_user.first_name} үшін құпия сөз сәтті өзгертілді."
        await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
    else:
        msg = f"Ошибка при изменении пароля: {errors}" if lang == "ru" else f"Құпия сөзді өзгерту кезінде қате: {errors}"
        await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
    return await start_admin_panel(update, context)

# Диалог рассылки
async def admin_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    broadcast_text = update.message.text.strip()
    lang = context.user_data.get("lang", "ru")
    if not broadcast_text:
        msg = "Сообщение пустое. Попробуйте еще раз." if lang == "ru" else "Хабарлама бос. Қайтадан көріңіз."
        await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
        return ADMIN_BROADCAST_MESSAGE
    # Рассылка всем авторизованным пользователям
    for user_id in AUTHORIZED_USERS:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"Рассылка:\n{broadcast_text}")
        except Exception as e:
            print(f"[ERROR] При отправке сообщения пользователю {user_id}: {e}")
    msg = "Сообщение отправлено всем авторизованным пользователям." if lang == "ru" else "Хабарлама барлық жүйеге кірген пайдаланушыларға жіберілді."
    await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
    return await start_admin_panel(update, context)

# Админский ConversationHandler
admin_panel_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^Админка$"), start_admin_panel)],
    states={
        ADMIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu_choice)],
        ADMIN_CHANGE_PASS_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_change_pass_username)],
        ADMIN_CHANGE_PASS_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_change_pass_new)],
        ADMIN_BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_message)]
    },
    fallbacks=[MessageHandler(filters.Regex("^Выход$"), lambda update, context: ConversationHandler.END)]
)

###############################################################################
# Основной код бота
###############################################################################
class Command(BaseCommand):
    help = "Bot with payroll lookup, PDF generation and admin panel (Russian/Kazakh)."

    def handle(self, *args, **options):
        BOT_TOKEN = botTOKEN
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # ---------- Language Selection ----------
        async def start_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
            language_keyboard = ReplyKeyboardMarkup([["Русский", "Қазақша"]], resize_keyboard=True)
            await update.message.reply_text(
                "Выберите язык / Тілді таңдаңыз:",
                reply_markup=language_keyboard
            )
            return WAITING_LANGUAGE

        async def language_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
            choice = update.message.text.strip()
            if choice == "Русский":
                context.user_data["lang"] = "ru"
            elif choice == "Қазақша":
                context.user_data["lang"] = "kz"
            else:
                await update.message.reply_text("Неверный выбор. Попробуйте еще раз.")
                return WAITING_LANGUAGE
            await update.message.reply_text(
                "Язык переключен.",
                reply_markup=(AUTHORIZED_KEYBOARD if update.effective_user.id in AUTHORIZED_USERS else UNAUTHORIZED_KEYBOARD)
            )
            return ConversationHandler.END

        language_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^Язык$"), start_language)],
            states={WAITING_LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, language_choice)]},
            fallbacks=[]
        )

        # ---------- Authorization ----------
        async def start_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
            lang = context.user_data.get("lang", "ru")
            text = "Введите логин:" if lang == "ru" else "Логинді енгізіңіз:"
            await update.message.reply_text(text)
            return WAITING_USERNAME

        async def username_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
            context.user_data["pending_username"] = update.message.text.strip()
            lang = context.user_data.get("lang", "ru")
            text = "Введите пароль:" if lang == "ru" else "Құпия сөзді енгізіңіз:"
            await update.message.reply_text(text)
            return WAITING_PASSWORD

        async def password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
            tg_id = update.effective_user.id
            username = context.user_data.get("pending_username")
            raw_password = update.message.text.strip()
            user_obj = await find_user_by_name(username)
            lang = context.user_data.get("lang", "ru")
            if not user_obj:
                text = ("Пользователь не найден. Нажмите 'Авторизация' снова."
                        if lang == "ru" else
                        "Пайдаланушы табылмады. Қайта 'Авторизация' батырмасын басыңыз.")
                await update.message.reply_text(text, reply_markup=UNAUTHORIZED_KEYBOARD)
                return ConversationHandler.END
            auth_user = await find_auth_user_by_user(user_obj)
            if not auth_user:
                text = ("Для этого пользователя нет пароля. Обратитесь к администратору."
                        if lang == "ru" else
                        "Осы пайдаланушы үшін құпия сөз жоқ. Әкімшіден көмек сұраңыз.")
                await update.message.reply_text(text, reply_markup=UNAUTHORIZED_KEYBOARD)
                return ConversationHandler.END
            if check_password(raw_password, auth_user.password_hash):
                AUTHORIZED_USERS.add(tg_id)
                user_obj.telegram_id = tg_id
                await save_user(user_obj)
                await log_to_linked(tg_id, getattr(user_obj, "iin", ""), getattr(user_obj, "t_number", ""))
                text = ("Авторизация успешна! Теперь доступны все команды."
                        if lang == "ru" else
                        "Авторизация сәтті өтті! Енді барлық командалар қол жетімді.")
                await update.message.reply_text(text, reply_markup=AUTHORIZED_KEYBOARD)
            else:
                text = ("Неверный пароль. Нажмите 'Авторизация', чтобы попробовать снова."
                        if lang == "ru" else
                        "Қате құпия сөз. Қайта 'Авторизация' батырмасын басыңыз.")
                await update.message.reply_text(text, reply_markup=UNAUTHORIZED_KEYBOARD)
            return ConversationHandler.END

        auth_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^Авторизация$"), start_auth)],
            states={
                WAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username_input)],
                WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_input)]
            },
            fallbacks=[]
        )

        # ---------- Vacation (без изменений) ----------
        async def start_vacation(update: Update, context: ContextTypes.DEFAULT_TYPE):
            tg_id = update.effective_user.id
            lang = context.user_data.get("lang", "ru")
            if tg_id not in AUTHORIZED_USERS:
                text = ("Сначала авторизуйтесь (нажмите 'Авторизация')."
                        if lang == "ru" else "Алдымен жүйеге кіру қажет ('Авторизация' батырмасын басыңыз).")
                await update.message.reply_text(text, reply_markup=UNAUTHORIZED_KEYBOARD)
                return ConversationHandler.END
            user_obj = await find_user_by_telegram_id(tg_id)
            if not user_obj or (not user_obj.name and not user_obj.first_name):
                text = ("Ваше ФИО не заполнено в БД. Обратитесь к администратору."
                        if lang == "ru" else "Дерекқорда ФИО толтырылмаған. Әкімшіден көмек сұраңыз.")
                await update.message.reply_text(text)
                return ConversationHandler.END
            short_fio = make_short_name_no_dots_for_user(user_obj)
            context.user_data["short_fio"] = short_fio
            context.user_data["user_obj"] = user_obj
            text = ("Введите вашу должность:" if lang == "ru" else "Лауазымыңызды енгізіңіз:")
            await update.message.reply_text(text)
            return WAITING_JOB

        async def vacation_job_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
            job = update.message.text.strip()
            user_obj = context.user_data.get("user_obj")
            lang = context.user_data.get("lang", "ru")
            if not user_obj:
                text = ("Ошибка: пользователь не найден в контексте." 
                        if lang == "ru" else "Қате: пайдаланушы контексте табылмады.")
                await update.message.reply_text(text, reply_markup=AUTHORIZED_KEYBOARD)
                return ConversationHandler.END
            vac_data = await get_vacation_async(user_obj, job)
            if not vac_data:
                text = ("Не найдено в графике отпусков." 
                        if lang == "ru" else "Демалыс кестесінде сәйкес жазба табылмады.")
                await update.message.reply_text(text, reply_markup=AUTHORIZED_KEYBOARD)
            else:
                short_fio = make_short_name_no_dots_for_user(user_obj)
                msg = (
                    f"ФИО (сокр.): {short_fio}\n"
                    f"Должность: {job}\n"
                    f"Кол. дней: {vac_data['days']}\n"
                    f"Согласованные дни: {vac_data['agreed']}\n"
                    f"Перенесение: {vac_data['transfer']}\n"
                    f"Примечание: {vac_data['note']}"
                )
                await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
            return ConversationHandler.END

        vacation_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^Отпуск$"), start_vacation)],
            states={WAITING_JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, vacation_job_input)]},
            fallbacks=[]
        )

        # ---------- ConversationHandler для "Расчетный лист" ----------
        async def start_payroll(update: Update, context: ContextTypes.DEFAULT_TYPE):
            tg_id = update.effective_user.id
            lang = context.user_data.get("lang", "ru")
            user_obj = await find_user_by_telegram_id(tg_id)
            if not user_obj:
                await update.message.reply_text("Пользователь не найден в базе. Обратитесь к администратору.",
                                                reply_markup=AUTHORIZED_KEYBOARD)
                return ConversationHandler.END
            payrolls = await async_get_payroll_by_user(user_obj, month=None)
            if not payrolls:
                await update.message.reply_text("Расчетный лист для вас не найден.", reply_markup=AUTHORIZED_KEYBOARD)
                return ConversationHandler.END
            available_months = sorted({p.get("Месяц") for p in payrolls if p.get("Месяц")})
            if len(available_months) > 1:
                context.user_data["payrolls"] = payrolls
                month_keyboard = ReplyKeyboardMarkup([[m] for m in available_months] + [["Назад"]], resize_keyboard=True)
                await update.message.reply_text("Найдено несколько расчетных листов. Выберите месяц:", reply_markup=month_keyboard)
                return WAITING_PAYROLL_MONTH
            else:
                context.user_data["selectedMonth"] = available_months[0]
                payroll = payrolls[0]
                msg = format_payroll_text(payroll)
                await update.message.reply_text(msg, reply_markup=PDF_KEYBOARD)
                context.user_data["selected_payroll"] = payroll
                return WAITING_PDF_CONFIRM

        async def choose_payroll_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
            chosen = update.message.text.strip()
            if chosen.lower() == "назад":
                await update.message.reply_text("Возвращаемся в основное меню.", reply_markup=AUTHORIZED_KEYBOARD)
                return ConversationHandler.END
            payrolls = context.user_data.get("payrolls", [])
            selected = [p for p in payrolls if p.get("Месяц") == chosen]
            if not selected:
                await update.message.reply_text("Расчетный лист для выбранного месяца не найден.", reply_markup=AUTHORIZED_KEYBOARD)
                return ConversationHandler.END
            else:
                payroll = selected[0]
                msg = format_payroll_text(payroll)
                await update.message.reply_text(msg, reply_markup=PDF_KEYBOARD)
                context.user_data["selected_payroll"] = payroll
                context.user_data["selectedMonth"] = chosen
                return WAITING_PDF_CONFIRM

        async def pdf_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
            lang = context.user_data.get("lang", "ru")
            tg_id = update.effective_user.id
            user_obj = context.user_data.get("user_obj")
            if not user_obj:
                user_obj = await find_user_by_telegram_id(tg_id)
                context.user_data["user_obj"] = user_obj
            selected_month = context.user_data.get("selectedMonth") or context.user_data.get("selected_payroll", {}).get("Месяц")
            await update.message.reply_text(
                f"DEBUG: user_obj.iin = {getattr(user_obj, 'iin', None)} / selectedMonth = {selected_month}"
            )
            if not user_obj or not user_obj.iin or not selected_month:
                await update.message.reply_text(
                    "Ошибка: недостаточно данных. Пожалуйста, повторно авторизуйтесь или выберите расчётный лист.",
                    reply_markup=AUTHORIZED_KEYBOARD
                )
                return ConversationHandler.END
            await update.message.reply_text(
                f"Отправляем запрос с ИИН: {user_obj.iin} и месяцем: {selected_month}"
            )
            text = update.message.text.strip().lower()
            if text == "сохранить pdf":
                pdf_url = await request_payroll_pdf(user_obj.iin, selected_month)
                if not pdf_url:
                    await update.message.reply_text(
                        "Ошибка при создании расчетного листа.",
                        reply_markup=AUTHORIZED_KEYBOARD
                    )
                    return ConversationHandler.END
                await update.message.reply_text(
                    f"PDF-версия расчетного листа: {pdf_url}",
                    reply_markup=AUTHORIZED_KEYBOARD
                )
            elif text == "назад":
                await update.message.reply_text(
                    "Возвращаемся к выбору месяца.",
                    reply_markup=AUTHORIZED_KEYBOARD
                )
                return await start_payroll(update, context)
            else:
                await update.message.reply_text("Расчетный лист не сохранен.", reply_markup=AUTHORIZED_KEYBOARD)
            return ConversationHandler.END

        payroll_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^Расчетный лист$"), start_payroll)],
            states={
                WAITING_PAYROLL_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_payroll_month)],
                WAITING_PDF_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, pdf_confirm)]
            },
            fallbacks=[]
        )

        # ---------- Общий обработчик текстов ----------
        async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = update.message.text.strip()
            tg_id = update.effective_user.id
            lang = context.user_data.get("lang", "ru")
            if tg_id not in AUTHORIZED_USERS:
                if text == "Помощь":
                    if not context.user_data.get("help_sent", False):
                        resp = ("Для получения помощи, пожалуйста, свяжитесь с техническим специалистом:\n"
                                "https://t.me/TechSupport\n"
                                "Или нажмите 'Авторизация' для входа."
                                if lang == "ru" else
                                "Көмек алу үшін техникалық маманмен байланысыңыз:\n"
                                "https://t.me/TechSupport\n"
                                "Немесе 'Авторизация' арқылы кіруді басыңыз.")
                        await update.message.reply_text(resp, reply_markup=UNAUTHORIZED_KEYBOARD)
                        context.user_data["help_sent"] = True
                    else:
                        resp = ("Вы можете:\n- 'Авторизация' для входа\n- 'Помощь' для контактов техподдержки"
                                if lang == "ru" else
                                "Сіз мыналарды орындай аласыз:\n- 'Авторизация' арқылы кіру\n- 'Помощь' арқылы техникалық көмек контактілері")
                        await update.message.reply_text(resp, reply_markup=UNAUTHORIZED_KEYBOARD)
                else:
                    resp = ("Сначала авторизуйтесь (нажмите 'Авторизация')."
                            if lang == "ru" else
                            "Алдымен жүйеге кіру қажет ('Авторизация' батырмасын басыңыз).")
                    await update.message.reply_text(resp, reply_markup=UNAUTHORIZED_KEYBOARD)
            else:
                if text == "Помощь":
                    resp = ("Доступные команды:\n- Помощь\n- Отпуск\n- Расчетный лист\n- Зарплата\n- Документы\n- Админка"
                            if lang == "ru" else
                            "Қол жетімді командалар:\n- Помощь\n- Отпуск\n- Расчетный лист\n- Зарплата\n- Документы\n- Админка")
                    await update.message.reply_text(resp, reply_markup=AUTHORIZED_KEYBOARD)
                elif text == "Зарплата":
                    user_obj = await find_user_by_telegram_id(tg_id)
                    if not user_obj:
                        resp = ("Не найден пользователь в БД. Обратитесь к администратору."
                                if lang == "ru" else
                                "Дерекқорда пайдаланушы табылмады. Әкімшіден көмек сұраңыз.")
                        await update.message.reply_text(resp, reply_markup=AUTHORIZED_KEYBOARD)
                    elif not user_obj.iin:
                        resp = ("У вас не заполнен ИИН в БД. Обратитесь к администратору."
                                if lang == "ru" else
                                "Сіздің ИИН толтырылмаған. Әкімшіден көмек сұраңыз.")
                        await update.message.reply_text(resp, reply_markup=AUTHORIZED_KEYBOARD)
                    else:
                        result = await get_salary_async(user_obj.iin)
                        if not result:
                            resp = ("Ваш ИИН не найден в таблице зарплат."
                                    if lang == "ru" else
                                    "Сіздің ИИН кестеде табылмады.")
                            await update.message.reply_text(resp, reply_markup=AUTHORIZED_KEYBOARD)
                        else:
                            fio, salary = result
                            msg = (f"По вашему ИИН: {user_obj.iin}\nФИО: {fio}\nЗарплата: {salary}"
                                   if lang == "ru" else
                                   f"Сіздің ИИН: {user_obj.iin}\nФИО: {fio}\nЖалақы: {salary}")
                            await update.message.reply_text(msg, reply_markup=AUTHORIZED_KEYBOARD)
                elif text == "Документы":
                    # Получаем folder_id для отдела пользователя
                    department_folder_id = await get_user_department_folder(tg_id)
                    if not department_folder_id:
                        await update.message.reply_text(
                            "Ваш отдел не определён или папка не назначена. Обратитесь к администратору.",
                            reply_markup=AUTHORIZED_KEYBOARD
                        )
                    else:
                        files = get_drive_files_by_folder(page_size=10, folder_id=department_folder_id)
                        if not files:
                            await update.message.reply_text(
                                "Нет доступных файлов для вашего отдела.",
                                reply_markup=AUTHORIZED_KEYBOARD
                            )
                        else:
                            doc_text = "Список доступных файлов:\n"
                            for f in files:
                                link = f.get("file_link")
                                name = f.get("name")
                                doc_text += f"- [{name}]({link})\n" if link else f"- {name} (нет ссылки)\n"
                            await update.message.reply_text(doc_text, parse_mode="Markdown", reply_markup=AUTHORIZED_KEYBOARD)
                elif text == "Отпуск":
                    await start_vacation(update, context)
                elif text == "Расчетный лист":
                    return await start_payroll(update, context)
                elif text == "Контакты":
                     await update.message.reply_text(CONTACTS_TEXT, reply_markup=AUTHORIZED_KEYBOARD)
                elif text == "Админка":
                    return await start_admin_panel(update, context)
                else:
                    resp = ("Неизвестная команда. Нажмите 'Помощь'."
                            if lang == "ru" else "Белгісіз команда. 'Помощь' батырмасын басыңыз.")
                    await update.message.reply_text(resp, reply_markup=AUTHORIZED_KEYBOARD)
            return ConversationHandler.END

        # Регистрируем все ConversationHandler'ы и основной обработчик
        app.add_handler(language_conv_handler)
        app.add_handler(auth_conv_handler)
        app.add_handler(vacation_conv_handler)
        app.add_handler(payroll_conv_handler)
        app.add_handler(admin_panel_conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

        app.run_polling()
