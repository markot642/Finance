import sqlite3
import datetime
from typing import List, Dict, Optional, Tuple
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                points INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Таблица транзакций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                category TEXT,
                description TEXT,
                transaction_type TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица целей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                target_amount REAL,
                current_amount REAL DEFAULT 0,
                goal_type TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_completed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица достижений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_id TEXT,
                earned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Добавление нового пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        ''', (user_id, username, first_name))
        
        conn.commit()
        conn.close()
    
    def add_transaction(self, user_id: int, amount: float, category: str, 
                       description: str, transaction_type: str):
        """Добавление транзакции"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (user_id, amount, category, description, transaction_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, category, description, transaction_type))
        
        conn.commit()
        conn.close()
    
    def get_user_balance(self, user_id: int) -> float:
        """Получение баланса пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END), 0)
            FROM transactions 
            WHERE user_id = ?
        ''', (user_id,))
        
        balance = cursor.fetchone()[0] or 0
        conn.close()
        return balance
    
    def get_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получение последних транзакций пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT amount, category, description, transaction_type, date
            FROM transactions 
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT ?
        ''', (user_id, limit))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'amount': row[0],
                'category': row[1],
                'description': row[2],
                'type': row[3],
                'date': row[4]
            })
        
        conn.close()
        return transactions
    
    def get_expenses_by_category(self, user_id: int, days: int = 30) -> List[Tuple]:
        """Получение расходов по категориям за период"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, SUM(amount)
            FROM transactions 
            WHERE user_id = ? AND transaction_type = 'expense' 
            AND date >= datetime('now', '-{} days')
            GROUP BY category
            ORDER BY SUM(amount) DESC
        '''.format(days), (user_id,))
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def add_goal(self, user_id: int, title: str, target_amount: float, goal_type: str):
        """Добавление финансовой цели"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO goals (user_id, title, target_amount, goal_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, title, target_amount, goal_type))
        
        conn.commit()
        conn.close()
    
    def get_user_goals(self, user_id: int) -> List[Dict]:
        """Получение целей пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, target_amount, current_amount, goal_type, is_completed
            FROM goals 
            WHERE user_id = ?
            ORDER BY created_date DESC
        ''', (user_id,))
        
        goals = []
        for row in cursor.fetchall():
            goals.append({
                'id': row[0],
                'title': row[1],
                'target_amount': row[2],
                'current_amount': row[3],
                'goal_type': row[4],
                'is_completed': bool(row[5])
            })
        
        conn.close()
        return goals
    
    def update_goal_progress(self, goal_id: int, amount: float):
        """Обновление прогресса цели"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE goals 
            SET current_amount = current_amount + ?
            WHERE id = ?
        ''', (amount, goal_id))
        
        # Проверяем, достигнута ли цель
        cursor.execute('''
            UPDATE goals 
            SET is_completed = TRUE
            WHERE id = ? AND current_amount >= target_amount
        ''', (goal_id,))
        
        conn.commit()
        conn.close()
    
    def add_achievement(self, user_id: int, achievement_id: str):
        """Добавление достижения пользователю"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO achievements (user_id, achievement_id)
            VALUES (?, ?)
        ''', (user_id, achievement_id))
        
        conn.commit()
        conn.close()
    
    def get_user_achievements(self, user_id: int) -> List[str]:
        """Получение достижений пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT achievement_id FROM achievements WHERE user_id = ?
        ''', (user_id,))
        
        achievements = [row[0] for row in cursor.fetchall()]
        conn.close()
        return achievements
    
    def update_user_points(self, user_id: int, points: int):
        """Обновление очков пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET points = points + ? WHERE user_id = ?
        ''', (points, user_id))
        
        conn.commit()
        conn.close()
    
    def get_user_points(self, user_id: int) -> int:
        """Получение очков пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else 0 