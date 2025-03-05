from django.core.management.base import BaseCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from portal_app.models import User, Linked  

class Command(BaseCommand):
    help = "Run Corporate Telegram Bot"

    def handle(self, *args, **options):
        BOT_TOKEN = "7890144483:AAHWAPus2UIfOO1o9OV3lblkz6ffbDAbXqU"  

        # Создаём приложение (telegram.ext v20+)
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # /start
        async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("Привет! Я корпоративный бот.\nНапиши /help, чтобы узнать команды.")

        # /help
        async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = (
                "/start — приветствие\n"
                "/help — список команд\n"
                "/bind <username> — привязать ваш Telegram к сотруднику\n"
                "/vacation — посмотреть отпуска\n"
                "/salary — посмотреть зарплату\n"
            )
            await update.message.reply_text(text)

        # /bind <username>
        async def bind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text("Использование: /bind <username>")
                return
            username = context.args[0]
            # Предположим, в User хранится username
            user_obj = User.objects.filter(name=username).first()
            if not user_obj:
                await update.message.reply_text("Пользователь не найден.")
                return
            user_obj.telegram_id = update.effective_user.id
            user_obj.save()
            await update.message.reply_text(f"Telegram привязан к {username}!")

        # /vacation
        async def vacation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            tg_id = update.effective_user.id
            user_obj = User.objects.filter(telegram_id=tg_id).first()
            if not user_obj:
                await update.message.reply_text("Сначала выполните /bind <username>.")
                return
            # Предположим, есть модель Vacation (или Linked) — адаптируйте
            # ... логика извлечения отпуска ...
            await update.message.reply_text("Ваш отпуск: ... (пока нет).")

        # /salary
        async def salary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            tg_id = update.effective_user.id
            user_obj = User.objects.filter(telegram_id=tg_id).first()
            if not user_obj:
                await update.message.reply_text("Сначала выполните /bind <username>.")
                return
            # Предположим, есть модель Payroll
            # ... логика ...
            await update.message.reply_text("Ваша зарплата: ... (пока нет).")

        # Регистрируем команды
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("bind", bind_command))
        app.add_handler(CommandHandler("vacation", vacation_command))
        app.add_handler(CommandHandler("salary", salary_command))

        # Запуск long-polling
        app.run_polling()
