from django.core.management.base import BaseCommand
# from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
#  BOT_TOKEN = "7890144483:AAHWAPus2UIfOO1o9OV3lblkz6ffbDAbXqU"  
from telegram import Update, ReplyKeyboardMarkup
from portal_app.models import User, Linked, AuthUser
from .google_service import get_drive_files
from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import check_password 
from creds import cred

WAITING_USERNAME = 1
WAITING_PASSWORD = 2
AUTHORIZED_USERS = set()

UNAUTHORIZED_KEYBOARD = ReplyKeyboardMarkup(
    [["/help", "/login"]],
    resize_keyboard=True
)

AUTHORIZED_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["/help", "/bind", "/vacation"],
        ["/salary", "/list_docs"]
    ],
    resize_keyboard=True
)

@sync_to_async
def find_user_by_name(name: str) -> User|None:
    return User.objects.filter(name=name).first()

@sync_to_async
def find_auth_user_by_user(user: User) -> AuthUser|None:
    return AuthUser.objects.filter(user=user).first()

@sync_to_async
def save_user(user: User):
    user.save()

class Command(BaseCommand):
    help = "Bot with login + hiding commands until authorized"

    def handle(self, *args, **options):
        # BOT_TOKEN = "7890144483:AAHWAPus2UIfOO1o9OV3lblkz6ffbDAbXqU"  # вставьте свой токен
        BOT_TOKEN = cred.BOT_TOKEN
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "Привет! Сначала авторизуйтесь: /login",
                reply_markup=UNAUTHORIZED_KEYBOARD
            )

        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id in AUTHORIZED_USERS:
                text = (
                    "Доступные команды:\n"
                    "/help — список команд\n"
                    "/bind <username> — привязать Telegram к сотруднику\n"
                    "/vacation — посмотреть отпуска\n"
                    "/salary — посмотреть зарплату\n"
                    "/list_docs — список файлов из Google Drive\n"
                )
            else:
                text = (
                    "Доступные команды:\n"
                    "/help — эта подсказка\n"
                    "/login — авторизация\n"
                )
            await update.message.reply_text(text)

        async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Начинаем диалог логина"""
            await update.message.reply_text("Введите логин (User.name):")
            return WAITING_USERNAME

        async def username_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
            context.user_data["pending_username"] = update.message.text.strip()
            await update.message.reply_text("Введите пароль:")
            return WAITING_PASSWORD

        async def password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
            tg_id = update.effective_user.id
            username = context.user_data.get("pending_username")
            raw_password = update.message.text.strip()

            # 1. Находим User по name
            user_obj = await find_user_by_name(username)
            if not user_obj:
                await update.message.reply_text(
                    "Пользователь не найден. Повторите /login.",
                    reply_markup=UNAUTHORIZED_KEYBOARD
                )
                return ConversationHandler.END

            # 2. Находим AuthUser
            auth_user = await find_auth_user_by_user(user_obj)
            if not auth_user:
                await update.message.reply_text(
                    "Для этого пользователя не заведён пароль. Обратитесь к админу.",
                    reply_markup=UNAUTHORIZED_KEYBOARD
                )
                return ConversationHandler.END

            # 3. Сравниваем введённый пароль с хэшом в auth_user.password_hash
            #    Если в базе действительно хэш (pbkdf2_sha256$...), используем check_password:
            if check_password(raw_password, auth_user.password_hash):
                # Успех
                AUTHORIZED_USERS.add(tg_id)
                user_obj.telegram_id = tg_id
                await save_user(user_obj)

                await update.message.reply_text(
                    "Авторизация успешна! Теперь доступны все команды.",
                    reply_markup=AUTHORIZED_KEYBOARD
                )
            else:
                await update.message.reply_text(
                    "Неверный пароль. Повторите /login.",
                    reply_markup=UNAUTHORIZED_KEYBOARD
                )

            return ConversationHandler.END

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("login", login_command)],
            states={
                WAITING_USERNAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, username_input)
                ],
                WAITING_PASSWORD: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, password_input)
                ],
            },
            fallbacks=[]
        )

        async def ensure_authorized(update: Update):
            tg_id = update.effective_user.id
            if tg_id not in AUTHORIZED_USERS:
                await update.message.reply_text(
                    "Сначала авторизуйтесь: /login",
                    reply_markup=UNAUTHORIZED_KEYBOARD
                )
                return False
            return True

        async def bind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await ensure_authorized(update):
                return
            if not context.args:
                await update.message.reply_text("Использование: /bind <username>")
                return
            await update.message.reply_text("Bind выполнен (заглушка).")

        async def vacation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await ensure_authorized(update):
                return
            await update.message.reply_text("Ваш отпуск: ... (заглушка).")

        async def salary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await ensure_authorized(update):
                return
            await update.message.reply_text("Ваша зарплата: ... (заглушка).")

        async def list_docs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not await ensure_authorized(update):
                return
            await update.message.reply_text("Список файлов: ... (заглушка).")

        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(conv_handler)
        app.add_handler(CommandHandler("bind", bind_command))
        app.add_handler(CommandHandler("vacation", vacation_command))
        app.add_handler(CommandHandler("salary", salary_command))
        app.add_handler(CommandHandler("list_docs", list_docs_command))

        app.run_polling()