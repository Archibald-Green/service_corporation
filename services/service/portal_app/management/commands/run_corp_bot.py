import os
import aiohttp
from django.core.management.base import BaseCommand
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from telegram import Update, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import check_password

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
    save_payroll_to_pdf
)

# Состояния диалогов
WAITING_USERNAME = 1
WAITING_PASSWORD = 2
WAITING_JOB = 50
WAITING_LANGUAGE = 100
WAITING_PAYROLL_MONTH = 110
WAITING_PDF_CONFIRM = 120

AUTHORIZED_USERS = set()

# Клавиатуры
AUTHORIZED_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Помощь", "Отпуск", "Расчетный лист", "Язык"],
        ["Зарплата", "Документы"]
    ],
    resize_keyboard=True
)
UNAUTHORIZED_KEYBOARD = ReplyKeyboardMarkup(
    [["Помощь", "Язык", "Авторизация"]],
    resize_keyboard=True
)
PDF_KEYBOARD = ReplyKeyboardMarkup([["Сохранить PDF", "Назад"]], resize_keyboard=True)

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

# Асинхронная функция для вызова веб‑приложения Google Apps Script,
# которая возвращает URL созданного PDF‑файла (расчетного листа)     url = f"https://script.google.com/macros/s/AKfycbwC9Fh_4tl5XrPP4dfAvI5jCboEADwAhUuRedkP4deQW4QSdkP6QdXFDzjfusMJxvbQKw/exec"


async def request_payroll_pdf(iin: str, month: str) -> str:
    from urllib.parse import quote_plus

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
            print(f"[DEBUG] Ответ от скрипта: {text[:300]}...")  # выводим только первые 300 символов
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
# Основной код бота
###############################################################################
class Command(BaseCommand):
    help = "Bot with payroll lookup and PDF generation (Russian/Kazakh)."

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

            # Получаем пользователя из context или по Telegram ID
            user_obj = context.user_data.get("user_obj")
            if not user_obj:
                user_obj = await find_user_by_telegram_id(tg_id)
                context.user_data["user_obj"] = user_obj  # чтобы не терять снова

            selected_month = context.user_data.get("selectedMonth") or context.user_data.get("selected_payroll", {}).get("Месяц")

            # Вывод отладочной информации
            await update.message.reply_text(
                f"DEBUG: user_obj.iin = {getattr(user_obj, 'iin', None)} / selectedMonth = {selected_month}"
            )

            if not user_obj or not user_obj.iin or not selected_month:
                await update.message.reply_text(
                    "Ошибка: недостаточно данных. Пожалуйста, повторно авторизуйтесь или выберите расчётный лист.",
                    reply_markup=AUTHORIZED_KEYBOARD
                )
                return ConversationHandler.END

            # Отладочное сообщение с параметрами
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
                    resp = ("Доступные команды:\n- Помощь\n- Отпуск\n- Расчетный лист\n- Зарплата\n- Документы"
                            if lang == "ru" else
                            "Қол жетімді командалар:\n- Помощь\n- Отпуск\n- Расчетный лист\n- Зарплата\n- Документы")
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
                    files = get_drive_files_with_links(10)
                    if not files:
                        resp = ("Нет доступных файлов." if lang == "ru" else "Қолжетімді файлдар жоқ.")
                        await update.message.reply_text(resp, reply_markup=AUTHORIZED_KEYBOARD)
                    else:
                        doc_text = "Список доступных файлов:\n" if lang == "ru" else "Қолжетімді файлдар тізімі:\n"
                        for f in files:
                            link = f["file_link"]
                            name = f["name"]
                            if link:
                                doc_text += f"- [{name}]({link})\n"
                            else:
                                doc_text += f"- {name} (нет ссылки)\n"
                        await update.message.reply_text(doc_text, parse_mode="Markdown", reply_markup=AUTHORIZED_KEYBOARD)
                elif text == "Отпуск":
                    await start_vacation(update, context)
                elif text == "Расчетный лист":
                    return await start_payroll(update, context)
                else:
                    resp = ("Неизвестная команда. Нажмите 'Помощь'."
                            if lang == "ru" else "Белгісіз команда. 'Помощь' батырмасын басыңыз.")
                    await update.message.reply_text(resp, reply_markup=AUTHORIZED_KEYBOARD)
            return ConversationHandler.END

        # Регистрируем ConversationHandlers и основной обработчик
        app.add_handler(language_conv_handler)
        app.add_handler(auth_conv_handler)
        app.add_handler(vacation_conv_handler)
        app.add_handler(payroll_conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

        app.run_polling()
