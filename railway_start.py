#!/usr/bin/env python3
"""
Специальный файл запуска для Railway
Запускает и веб-сервер, и Telegram бота
"""

import asyncio
import logging
import threading
import os
import time
from flask import Flask, jsonify

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

@app.route('/')
def health_check():
    """Health check endpoint для Railway"""
    return jsonify({
        "status": "healthy",
        "service": "Telegram Finance Bot",
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    """Дополнительный health check endpoint"""
    return jsonify({"status": "ok"})

def run_web_server():
    """Запуск веб-сервера"""
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Запуск веб-сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

async def run_telegram_bot():
    """Запуск Telegram бота"""
    try:
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
        from config import BOT_TOKEN
        from database import Database
        from analytics import Analytics
        from handlers import BotHandlers, ENTERING_AMOUNT, ENTERING_DESCRIPTION
        from telegram import Update
        
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
        
        # Запуск бота
        logger.info("Запуск финансового бота...")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

def main():
    """Основная функция"""
    logger.info("Запуск приложения на Railway...")
    
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    logger.info("Веб-сервер запущен")
    
    # Даем время веб-серверу запуститься
    time.sleep(2)
    
    # Запускаем Telegram бота
    logger.info("Запуск Telegram бота...")
    asyncio.run(run_telegram_bot())

if __name__ == '__main__':
    main() 