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
# Импортируем новые функции из google_service
from .google_service import (
    get_drive_files_with_links,
    get_salary_by_iin,
    make_short_name_no_dots_for_user,      # новая функция, использующая user_obj.name и user_obj.first_name
    get_vacation_by_user_and_job             # новая функция для поиска отпуска по user_obj и должности
)

# Состояния для Авторизация
WAITING_USERNAME = 1
WAITING_PASSWORD = 2

# Состояния для Отпуск
WAITING_JOB = 50

AUTHORIZED_USERS = set()

UNAUTHORIZED_KEYBOARD = ReplyKeyboardMarkup(
    [["Помощь", "Авторизация"]],
    resize_keyboard=True
)

AUTHORIZED_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["Помощь", "Привязать", "Отпуск"],
        ["Зарплата", "Документы"]
    ],
    resize_keyboard=True
)

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

# Обёртка для новой функции поиска отпуска, принимающая объект пользователя и должность
@sync_to_async
def get_vacation_async(user_obj, job: str):
    return get_vacation_by_user_and_job(user_obj, job)

class Command(BaseCommand):
    help = "Bot with text-based commands (Russian) and hidden logic until authorized"

    def handle(self, *args, **options):
        BOT_TOKEN = botTOKEN
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # ---------- ConversationHandler для Авторизация ----------
        async def start_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("Введите логин:")
            return WAITING_USERNAME

        async def username_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
            context.user_data["pending_username"] = update.message.text.strip()
            await update.message.reply_text("Введите пароль:")
            return WAITING_PASSWORD

        async def password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
            tg_id = update.effective_user.id
            username = context.user_data.get("pending_username")
            raw_password = update.message.text.strip()

            user_obj = await find_user_by_name(username)
            if not user_obj:
                await update.message.reply_text(
                    "Пользователь не найден. Нажмите 'Авторизация' снова.",
                    reply_markup=UNAUTHORIZED_KEYBOARD
                )
                return ConversationHandler.END

            auth_user = await find_auth_user_by_user(user_obj)
            if not auth_user:
                await update.message.reply_text(
                    "Для этого пользователя нет пароля. Обратитесь к администратору.",
                    reply_markup=UNAUTHORIZED_KEYBOARD
                )
                return ConversationHandler.END

            if check_password(raw_password, auth_user.password_hash):
                AUTHORIZED_USERS.add(tg_id)
                user_obj.telegram_id = tg_id
                await save_user(user_obj)

                await log_to_linked(
                    tg_id,
                    getattr(user_obj, "iin", ""),
                    getattr(user_obj, "t_number", "")
                )

                await update.message.reply_text(
                    "Авторизация успешна! Теперь доступны все команды.",
                    reply_markup=AUTHORIZED_KEYBOARD
                )
            else:
                await update.message.reply_text(
                    "Неверный пароль. Нажмите 'Авторизация', чтобы попробовать снова.",
                    reply_markup=UNAUTHORIZED_KEYBOARD
                )
            return ConversationHandler.END

        auth_conv_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^Авторизация$"), start_auth)],
            states={
                WAITING_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username_input)],
                WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_input)],
            },
            fallbacks=[]
        )

        # ---------- ConversationHandler для "Отпуск" ----------
        async def start_vacation(update: Update, context: ContextTypes.DEFAULT_TYPE):
            tg_id = update.effective_user.id
            if tg_id not in AUTHORIZED_USERS:
                await update.message.reply_text(
                    "Сначала авторизуйтесь (нажмите 'Авторизация').",
                    reply_markup=UNAUTHORIZED_KEYBOARD
                )
                return ConversationHandler.END

            # Находим пользователя
            user_obj = await find_user_by_telegram_id(tg_id)
            # Проверяем, что хотя бы одно из полей ФИО заполнено
            if not user_obj or (not user_obj.name and not user_obj.first_name):
                await update.message.reply_text("Ваше ФИО не заполнено в БД. Обратитесь к администратору.")
                return ConversationHandler.END

            # Формируем сокращённое ФИО, используя новые функции (например, "ИвановИ")
            short_fio = make_short_name_no_dots_for_user(user_obj)
            context.user_data["short_fio"] = short_fio
            # Сохраняем объект пользователя для последующего использования
            context.user_data["user_obj"] = user_obj

            await update.message.reply_text("Введите вашу должность:")
            return WAITING_JOB

        async def vacation_job_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
            job = update.message.text.strip()
            user_obj = context.user_data.get("user_obj")
            if not user_obj:
                await update.message.reply_text("Ошибка: пользователь не найден в контексте.", reply_markup=AUTHORIZED_KEYBOARD)
                return ConversationHandler.END

            vac_data = await get_vacation_async(user_obj, job)
            if not vac_data:
                await update.message.reply_text("Не найдено в графике отпусков.", reply_markup=AUTHORIZED_KEYBOARD)
            else:
                # Вычисляем сокращённое ФИО для вывода
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
            states={
                WAITING_JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, vacation_job_input)]
            },
            fallbacks=[]
        )

        # ---------- Общий обработчик текстов ----------
        async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = update.message.text
            tg_id = update.effective_user.id

            if tg_id not in AUTHORIZED_USERS:
                if text == "Помощь":
                    await update.message.reply_text(
                        "Вы можете:\n- 'Авторизация' для входа\n- 'Помощь' для этого сообщения",
                        reply_markup=UNAUTHORIZED_KEYBOARD
                    )
                else:
                    await update.message.reply_text(
                        "Сначала авторизуйтесь (нажмите 'Авторизация').",
                        reply_markup=UNAUTHORIZED_KEYBOARD
                    )
            else:
                # Авторизован
                if text == "Помощь":
                    await update.message.reply_text(
                        "Доступные команды:\n"
                        "- Помощь\n"
                        "- Привязать\n"
                        "- Отпуск\n"
                        "- Зарплата\n"
                        "- Документы",
                        reply_markup=AUTHORIZED_KEYBOARD
                    )
                elif text == "Привязать":
                    await update.message.reply_text("Привязка не реализована.", reply_markup=AUTHORIZED_KEYBOARD)
                elif text == "Зарплата":
                    user_obj = await find_user_by_telegram_id(tg_id)
                    if not user_obj:
                        await update.message.reply_text(
                            "Не найден пользователь в БД. Обратитесь к администратору.",
                            reply_markup=AUTHORIZED_KEYBOARD
                        )
                    else:
                        if not user_obj.iin:
                            await update.message.reply_text(
                                "У вас не заполнен ИИН в БД. Обратитесь к администратору.",
                                reply_markup=AUTHORIZED_KEYBOARD
                            )
                        else:
                            result = await get_salary_async(user_obj.iin)
                            if not result:
                                await update.message.reply_text(
                                    "Ваш ИИН не найден в таблице зарплат.",
                                    reply_markup=AUTHORIZED_KEYBOARD
                                )
                            else:
                                fio, salary = result
                                msg = (f"По вашему ИИН: {user_obj.iin}\n"
                                       f"ФИО: {fio}\n"
                                       f"Зарплата: {salary}")
                                await update.message.reply_text(
                                    msg,
                                    reply_markup=AUTHORIZED_KEYBOARD
                                )
                elif text == "Документы":
                    files = get_drive_files_with_links(page_size=10)
                    if not files:
                        await update.message.reply_text("Нет доступных файлов.", reply_markup=AUTHORIZED_KEYBOARD)
                    else:
                        doc_text = "Список доступных файлов:\n"
                        for f in files:
                            link = f["file_link"]
                            name = f["name"]
                            if link:
                                doc_text += f"- [{name}]({link})\n"
                            else:
                                doc_text += f"- {name} (нет ссылки)\n"

                        await update.message.reply_text(
                            doc_text,
                            parse_mode="Markdown",
                            reply_markup=AUTHORIZED_KEYBOARD
                        )
                else:
                    await update.message.reply_text(
                        "Неизвестная команда. Нажмите 'Помощь'.",
                        reply_markup=AUTHORIZED_KEYBOARD
                    )

        # Регистрируем ConversationHandlers и text_handler
        app.add_handler(auth_conv_handler)
        app.add_handler(vacation_conv_handler)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

        app.run_polling()
