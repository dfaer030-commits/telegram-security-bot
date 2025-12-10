import os
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Простой HTTP сервер для health check
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health']:
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bot is running')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Отключаем логирование

def run_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Health check server started on port {port}")
    server.serve_forever()

# Запускаем health check сервер
health_thread = Thread(target=run_health_server, daemon=True)
health_thread.start()

# Основной код бота
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Установите переменную BOT_TOKEN в Render

async def start(update: Update, context):
    await update.message.reply_text("Привет! Я бот для проверки мошенничества. Отправьте мне сообщение для анализа.")

async def analyze_message(update: Update, context):
    message_text = update.message.text
    user = update.effective_user
    
    # Простая логика анализа
    scam_keywords = ['крипта', 'биткоин', 'инвестиции', 'быстро', 'гарантия', 'бесплатно']
    
    scam_score = 0
    detected_keywords = []
    
    for keyword in scam_keywords:
        if keyword in message_text.lower():
            scam_score += 1
            detected_keywords.append(keyword)
    
    if scam_score > 0:
        response = f"⚠️ Внимание! Обнаружены признаки мошенничества.\n"
        response += f"Найдены ключевые слова: {', '.join(detected_keywords)}\n"
        response += f"Уровень риска: {scam_score}/6"
    else:
        response = "✅ Сообщение выглядит безопасно."
    
    await update.message.reply_text(response)

async def error_handler(update: Update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_message))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("🚀 Бот запущен и работает...")
    
    # Запускаем polling
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
