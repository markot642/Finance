import asyncio
import logging
import threading
import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from config import BOT_TOKEN
from database import Database
from analytics import Analytics
from handlers import BotHandlers, ENTERING_AMOUNT, ENTERING_DESCRIPTION
from telegram import Update
from web_server import run_web_server

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("Не установлен BOT_TOKEN в переменных окружения!")
        return
    
    # Инициализация компонентов
    db = Database()
    analytics = Analytics(db)
    handlers = BotHandlers(db, analytics)
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настройка обработчиков
    application.add_handler(CommandHandler("start", handlers.start))
    
    # Обработчик кнопок
    application.add_handler(CallbackQueryHandler(handlers.button_handler))
    
    # ConversationHandler для добавления транзакций
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handlers.handle_category_selection, pattern="^category_")],
        states={
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_amount_input)
            ],
            ENTERING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_description_input)
            ]
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)]
    )
    
    application.add_handler(conv_handler)
    
    # Запуск веб-сервера в отдельном потоке (для Railway)
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        logger.info("Запуск в среде Railway - запускаю веб-сервер...")
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
    
    # Запуск бота
    logger.info("Запуск финансового бота...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main()) 