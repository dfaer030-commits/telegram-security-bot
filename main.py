import os
from flask import Flask
from threading import Thread
import logging

# Создаем простой Flask сервер для health check
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running', 200

@app.route('/health')
def health():
    return 'OK', 200

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Запускаем Flask в отдельном потоке
web_thread = Thread(target=run_web, daemon=True)
web_thread.start()

# Дальше ваш основной код бота...
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

from fraud_analyzer import FraudAnalyzer

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация анализатора
fraud_analyzer = FraudAnalyzer()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
🔒 <b>Антимошеннический бот</b>

Я помогу проанализировать сообщения на признаки мошенничества.

<b>Просто отправьте мне подозрительное сообщение!</b>

🤖 <i>Используется AI-анализ + эвристики</i>

<b>Команды:</b>
/start - показать справку
/status - статус системы
    """
    await update.message.reply_html(welcome_text)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    api_status = "✅ Активен" if os.getenv('HF_API_KEY') else "⚠️ Только эвристики"
    
    status_text = f"""
<b>Статус системы:</b>

🤖 <b>Hugging Face API:</b> {api_status}
🔍 <b>Анализатор:</b> ✅ Активен
📊 <b>Паттернов:</b> {len(fraud_analyzer.fraud_patterns)}

💡 <i>Бот готов к работе</i>
    """
    await update.message.reply_html(status_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений"""
    try:
        message_text = update.message.text
        
        # Отправляем сообщение о процессе анализа
        processing_msg = await update.message.reply_text("🔍 Анализирую сообщение...")
        
        # Анализируем сообщение
        analysis_result = fraud_analyzer.analyze_message(message_text)
        
        # Формируем ответ
        if analysis_result['is_fraud']:
            response = f"""
⚠️ <b>ВНИМАНИЕ: Обнаружены признаки мошенничества!</b>

{'🤖 AI-анализ' if analysis_result['ai_used'] else '🔍 Эвристический анализ'}
📊 <b>Уверенность:</b> {analysis_result['confidence']:.1%}
🚨 <b>Уровень риска:</b> {analysis_result['risk_level']}
🔍 <b>Причина:</b> {analysis_result['reason']}

<code>Рекомендации:</code>
• Не переходите по ссылкам
• Не передавайте данные
• Не совершайте платежи
• Проверьте информацию
            """
        else:
            response = f"""
✅ <b>Сообщение выглядит безопасно</b>

{'🤖 AI-анализ' if analysis_result['ai_used'] else '🔍 Эвристический анализ'}
📊 <b>Уверенность:</b> {analysis_result['confidence']:.1%}
📝 <b>Уровень риска:</b> {analysis_result['risk_level']}

💡 Всегда сохраняйте бдительность
            """
        
        # Удаляем сообщение о процессе и отправляем результат
        await processing_msg.delete()
        await update.message.reply_html(response)
        
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        await update.message.reply_text("❌ Произошла ошибка при анализе. Попробуйте позже.")

def main():
    """Запуск бота"""
    # Получаем токен бота и очищаем его от лишних символов
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден!")
        return
    
    BOT_TOKEN = BOT_TOKEN.strip()
    
    try:
        # Создаем Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запускаем бота
        logger.info("🚀 Бот запущен!")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

if __name__ == '__main__':
    main()
