import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import io
from database import Database
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES

class Analytics:
    def __init__(self, db: Database):
        self.db = db
        # Настройка стиля графиков
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_expense_pie_chart(self, user_id: int, days: int = 30) -> bytes:
        """Создание круговой диаграммы расходов"""
        expenses = self.db.get_expenses_by_category(user_id, days)
        
        if not expenses:
            return self._create_empty_chart("Нет данных о расходах")
        
        categories, amounts = zip(*expenses)
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
        
        wedges, texts, autotexts = ax.pie(amounts, labels=categories, autopct='%1.1f%%',
                                          colors=colors, startangle=90)
        
        ax.set_title(f'Расходы по категориям (за {days} дней)', fontsize=16, fontweight='bold')
        
        # Улучшаем отображение текста
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        
        return self._save_chart_to_bytes()
    
    def create_income_vs_expense_chart(self, user_id: int, days: int = 30) -> bytes:
        """Создание графика доходов vs расходов"""
        transactions = self.db.get_transactions(user_id, 1000)  # Получаем больше транзакций
        
        if not transactions:
            return self._create_empty_chart("Нет данных о транзакциях")
        
        # Фильтруем по дате
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_transactions = []
        
        for trans in transactions:
            trans_date = datetime.strptime(trans['date'], '%Y-%m-%d %H:%M:%S')
            if trans_date >= cutoff_date:
                filtered_transactions.append(trans)
        
        if not filtered_transactions:
            return self._create_empty_chart(f"Нет данных за последние {days} дней")
        
        # Группируем по дням
        daily_data = {}
        for trans in filtered_transactions:
            date = trans['date'].split()[0]
            if date not in daily_data:
                daily_data[date] = {'income': 0, 'expense': 0}
            
            if trans['type'] == 'income':
                daily_data[date]['income'] += trans['amount']
            else:
                daily_data[date]['expense'] += trans['amount']
        
        dates = sorted(daily_data.keys())
        incomes = [daily_data[date]['income'] for date in dates]
        expenses = [daily_data[date]['expense'] for date in dates]
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = range(len(dates))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], incomes, width, label='Доходы', color='green', alpha=0.7)
        ax.bar([i + width/2 for i in x], expenses, width, label='Расходы', color='red', alpha=0.7)
        
        ax.set_xlabel('Дата')
        ax.set_ylabel('Сумма (руб.)')
        ax.set_title(f'Доходы vs Расходы (за {days} дней)', fontsize=16, fontweight='bold')
        ax.legend()
        
        # Настройка осей
        ax.set_xticks(x)
        ax.set_xticklabels([date[5:] for date in dates], rotation=45)
        
        plt.tight_layout()
        
        return self._save_chart_to_bytes()
    
    def create_savings_progress_chart(self, user_id: int) -> bytes:
        """Создание графика прогресса накоплений"""
        goals = self.db.get_user_goals(user_id)
        
        if not goals:
            return self._create_empty_chart("У вас нет активных целей")
        
        # Фильтруем только активные цели
        active_goals = [goal for goal in goals if not goal['is_completed']]
        
        if not active_goals:
            return self._create_empty_chart("Все цели достигнуты! 🎉")
        
        goal_names = [goal['title'] for goal in active_goals]
        current_amounts = [goal['current_amount'] for goal in active_goals]
        target_amounts = [goal['target_amount'] for goal in active_goals]
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = range(len(goal_names))
        width = 0.35
        
        # График текущего прогресса
        bars1 = ax.bar([i - width/2 for i in x], current_amounts, width, 
                      label='Текущие накопления', color='lightblue', alpha=0.8)
        
        # График целевой суммы
        bars2 = ax.bar([i + width/2 for i in x], target_amounts, width, 
                      label='Целевая сумма', color='orange', alpha=0.6)
        
        ax.set_xlabel('Цели')
        ax.set_ylabel('Сумма (руб.)')
        ax.set_title('Прогресс накоплений', fontsize=16, fontweight='bold')
        ax.legend()
        
        # Настройка осей
        ax.set_xticks(x)
        ax.set_xticklabels(goal_names, rotation=45, ha='right')
        
        # Добавляем процентное соотношение
        for i, (current, target) in enumerate(zip(current_amounts, target_amounts)):
            percentage = (current / target) * 100 if target > 0 else 0
            ax.text(i, current + max(current_amounts) * 0.02, 
                   f'{percentage:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        return self._save_chart_to_bytes()
    
    def create_monthly_trend_chart(self, user_id: int, months: int = 6) -> bytes:
        """Создание графика месячных трендов"""
        transactions = self.db.get_transactions(user_id, 5000)
        
        if not transactions:
            return self._create_empty_chart("Недостаточно данных для анализа трендов")
        
        # Группируем по месяцам
        monthly_data = {}
        for trans in transactions:
            date = datetime.strptime(trans['date'], '%Y-%m-%d %H:%M:%S')
            month_key = f"{date.year}-{date.month:02d}"
            
            if month_key not in monthly_data:
                monthly_data[month_key] = {'income': 0, 'expense': 0}
            
            if trans['type'] == 'income':
                monthly_data[month_key]['income'] += trans['amount']
            else:
                monthly_data[month_key]['expense'] += trans['amount']
        
        # Сортируем по месяцам
        sorted_months = sorted(monthly_data.keys())
        
        if len(sorted_months) < 2:
            return self._create_empty_chart("Недостаточно данных для анализа трендов")
        
        # Берем последние N месяцев
        recent_months = sorted_months[-months:]
        
        incomes = [monthly_data[month]['income'] for month in recent_months]
        expenses = [monthly_data[month]['expense'] for month in recent_months]
        savings = [income - expense for income, expense in zip(incomes, expenses)]
        
        # Создаем график
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        x = range(len(recent_months))
        width = 0.35
        
        # График доходов и расходов
        ax1.bar([i - width/2 for i in x], incomes, width, label='Доходы', color='green', alpha=0.7)
        ax1.bar([i + width/2 for i in x], expenses, width, label='Расходы', color='red', alpha=0.7)
        ax1.set_title('Месячные доходы и расходы', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.set_xticks(x)
        ax1.set_xticklabels([month[5:] for month in recent_months])
        
        # График накоплений
        colors = ['green' if s >= 0 else 'red' for s in savings]
        ax2.bar(x, savings, color=colors, alpha=0.7)
        ax2.set_title('Месячные накопления', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels([month[5:] for month in recent_months])
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        plt.tight_layout()
        
        return self._save_chart_to_bytes()
    
    def _create_empty_chart(self, message: str) -> bytes:
        """Создание пустого графика с сообщением"""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, message, ha='center', va='center', 
               transform=ax.transAxes, fontsize=14, fontweight='bold')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return self._save_chart_to_bytes()
    
    def _save_chart_to_bytes(self) -> bytes:
        """Сохранение графика в байты"""
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        return buffer.getvalue() 