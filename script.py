import smtplib
import re
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Загрузка переменных окружения
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_LOGIN = os.getenv("SMTP_LOGIN")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Проверка, что все переменные окружения загружены
if not all([BOT_TOKEN, SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD]):
    raise EnvironmentError("Проверьте, что файл .env содержит все необходимые переменные: BOT_TOKEN, SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD.")

# Глобальные данные пользователей
user_data = {}

# Регулярное выражение для проверки email
EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Напишите свой email.")

# Обработка email
async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    email = update.message.text.strip()
    if re.match(EMAIL_REGEX, email):
        user_data[update.message.chat_id] = {'email': email}
        await update.message.reply_text("Email принят. Теперь напишите текст сообщения, которое нужно отправить.")
    else:
        await update.message.reply_text("Пожалуйста, введите корректный email.")

# Обработка сообщения и отправка email
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id

    # Проверка, что email уже введен
    if chat_id in user_data and 'email' in user_data[chat_id]:
        email = user_data[chat_id]['email']
        message_text = update.message.text.strip()

        # Попытка отправки сообщения
        if send_email(email, message_text):
            await update.message.reply_text("Сообщение успешно отправлено!")
        else:
            await update.message.reply_text("Ошибка отправки сообщения. Проверьте настройки SMTP.")

        # Очистка данных пользователя
        del user_data[chat_id]
    else:
        await update.message.reply_text("Сначала введите ваш email.")

# Функция для отправки email
def send_email(to_email: str, message_text: str) -> bool:
    try:
        # Создание письма
        msg = MIMEMultipart()
        msg['From'] = SMTP_LOGIN
        msg['To'] = to_email
        msg['Subject'] = "Уведомление от Telegram-бота"
        msg.attach(MIMEText(message_text, 'plain'))

        # Отправка письма через SMTP
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_LOGIN, SMTP_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        logging.error(f"Ошибка при отправке email: {e}")
        return False

# Основной блок
def main():
    # Создание приложения Telegram
    app = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(EMAIL_REGEX), handle_email))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    logging.info("Бот запущен. Нажмите Ctrl+C для остановки.")
    app.run_polling()

if __name__ == '__main__':
    main()
