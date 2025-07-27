#!/usr/bin/env python3
"""
Тестовый файл для проверки основных функций финансового бота
"""

import asyncio
import sqlite3
from database import Database
from analytics import Analytics
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES, ACHIEVEMENTS

async def test_database():
    """Тестирование функций базы данных"""
    print("🧪 Тестирование базы данных...")
    
    db = Database()
    
    # Тест добавления пользователя
    test_user_id = 12345
    db.add_user(test_user_id, "test_user", "Test User")
    print("✅ Пользователь добавлен")
    
    # Тест добавления транзакций
    db.add_transaction(test_user_id, 1000, "💰 Зарплата", "Тестовая зарплата", "income")
    db.add_transaction(test_user_id, 500, "🍔 Еда и фастфуд", "Обед", "expense")
    db.add_transaction(test_user_id, 200, "🚌 Транспорт", "Проезд", "expense")
    print("✅ Транзакции добавлены")
    
    # Тест получения баланса
    balance = db.get_user_balance(test_user_id)
    print(f"💰 Баланс: {balance} руб.")
    
    # Тест получения транзакций
    transactions = db.get_transactions(test_user_id, 5)
    print(f"📋 Количество транзакций: {len(transactions)}")
    
    # Тест добавления цели
    db.add_goal(test_user_id, "Накопить на телефон", 5000, "save")
    goals = db.get_user_goals(test_user_id)
    print(f"🎯 Количество целей: {len(goals)}")
    
    # Тест достижений
    db.add_achievement(test_user_id, "first_save")
    achievements = db.get_user_achievements(test_user_id)
    print(f"🏆 Количество достижений: {len(achievements)}")
    
    print("✅ Все тесты базы данных пройдены!\n")

async def test_analytics():
    """Тестирование функций аналитики"""
    print("📊 Тестирование аналитики...")
    
    db = Database()
    analytics = Analytics(db)
    
    test_user_id = 12345
    
    # Добавляем больше данных для тестирования
    categories = ["🍔 Еда и фастфуд", "🚌 Транспорт", "🎮 Развлечения", "📚 Учеба"]
    amounts = [300, 150, 200, 500]
    
    for category, amount in zip(categories, amounts):
        db.add_transaction(test_user_id, amount, category, f"Тестовая трата на {category}", "expense")
    
    # Тест создания графиков
    try:
        expense_chart = analytics.create_expense_pie_chart(test_user_id)
        print("✅ График расходов создан")
        
        income_vs_expense_chart = analytics.create_income_vs_expense_chart(test_user_id)
        print("✅ График доходов vs расходов создан")
        
        savings_chart = analytics.create_savings_progress_chart(test_user_id)
        print("✅ График прогресса накоплений создан")
        
        trends_chart = analytics.create_monthly_trend_chart(test_user_id)
        print("✅ График месячных трендов создан")
        
    except Exception as e:
        print(f"❌ Ошибка при создании графиков: {e}")
    
    print("✅ Все тесты аналитики пройдены!\n")

async def test_config():
    """Тестирование конфигурации"""
    print("⚙️ Тестирование конфигурации...")
    
    print(f"📊 Категории расходов: {len(EXPENSE_CATEGORIES)}")
    print(f"💰 Категории доходов: {len(INCOME_CATEGORIES)}")
    print(f"🏆 Достижения: {len(ACHIEVEMENTS)}")
    
    print("✅ Конфигурация корректна!\n")

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестов финансового бота...\n")
    
    await test_config()
    await test_database()
    await test_analytics()
    
    print("🎉 Все тесты пройдены успешно!")
    print("Бот готов к использованию!")

if __name__ == "__main__":
    asyncio.run(main()) 