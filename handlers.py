from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import Database
from analytics import Analytics
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES, ACHIEVEMENTS, FINANCIAL_TIPS
import random
from datetime import datetime

# Состояния для ConversationHandler
CHOOSING_CATEGORY, ENTERING_AMOUNT, ENTERING_DESCRIPTION, CHOOSING_GOAL_TYPE, ENTERING_GOAL_AMOUNT = range(5)

class BotHandlers:
    def __init__(self, db: Database, analytics: Analytics):
        self.db = db
        self.analytics = analytics
        self.user_states = {}  # Для хранения состояния пользователей
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name)
        
        welcome_text = f"""
🎉 Привет, {user.first_name}! 

Я твой финансовый помощник для подростков и студентов! 💰

Что я умею:
✅ Учитывать доходы и расходы
✅ Давать советы по финансовой грамотности  
✅ Помогать ставить и достигать цели
✅ Мотивировать через геймификацию
✅ Показывать аналитику и графики

Выбери действие:
        """
        
        keyboard = [
            [InlineKeyboardButton("💰 Доход", callback_data="income")],
            [InlineKeyboardButton("💸 Расход", callback_data="expense")],
            [InlineKeyboardButton("📊 Баланс", callback_data="balance")],
            [InlineKeyboardButton("🎯 Цели", callback_data="goals")],
            [InlineKeyboardButton("🏆 Достижения", callback_data="achievements")],
            [InlineKeyboardButton("💡 Советы", callback_data="tips")],
            [InlineKeyboardButton("📈 Аналитика", callback_data="analytics")],
            [InlineKeyboardButton("📋 История", callback_data="history")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "income":
            await self.show_income_categories(query)
        elif query.data == "expense":
            await self.show_expense_categories(query)
        elif query.data == "balance":
            await self.show_balance(query)
        elif query.data == "goals":
            await self.show_goals(query)
        elif query.data == "achievements":
            await self.show_achievements(query)
        elif query.data == "tips":
            await self.show_tips(query)
        elif query.data == "analytics":
            await self.show_analytics_menu(query)
        elif query.data == "history":
            await self.show_history(query)
        elif query.data.startswith("category_"):
            await self.handle_category_selection(query)
        elif query.data.startswith("analytics_"):
            await self.handle_analytics_selection(query)
        elif query.data == "add_goal":
            await self.start_add_goal(query)
        elif query.data == "back_to_main":
            await self.show_main_menu(query)
    
    async def show_income_categories(self, query):
        """Показать категории доходов"""
        keyboard = []
        for category in INCOME_CATEGORIES:
            keyboard.append([InlineKeyboardButton(category, callback_data=f"category_income_{category}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите категорию дохода:", reply_markup=reply_markup)
    
    async def show_expense_categories(self, query):
        """Показать категории расходов"""
        keyboard = []
        for category in EXPENSE_CATEGORIES:
            keyboard.append([InlineKeyboardButton(category, callback_data=f"category_expense_{category}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите категорию расхода:", reply_markup=reply_markup)
    
    async def handle_category_selection(self, query):
        """Обработка выбора категории"""
        parts = query.data.split("_", 2)
        transaction_type = parts[1]
        category = parts[2]
        
        # Сохраняем состояние пользователя
        self.user_states[query.from_user.id] = {
            'transaction_type': transaction_type,
            'category': category
        }
        
        await query.edit_message_text(
            f"Введите сумму ({'дохода' if transaction_type == 'income' else 'расхода'}):\n"
            f"Категория: {category}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Отмена", callback_data="back_to_main")]])
        )
        
        return ENTERING_AMOUNT
    
    async def handle_amount_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода суммы"""
        try:
            amount = float(update.message.text.replace(',', '.'))
            if amount <= 0:
                await update.message.reply_text("Сумма должна быть больше нуля!")
                return ENTERING_AMOUNT
            
            user_id = update.effective_user.id
            if user_id not in self.user_states:
                await update.message.reply_text("Произошла ошибка. Попробуйте снова.")
                return ConversationHandler.END
            
            state = self.user_states[user_id]
            state['amount'] = amount
            
            await update.message.reply_text(
                f"Введите описание транзакции:\n"
                f"Сумма: {amount} руб.\n"
                f"Категория: {state['category']}"
            )
            
            return ENTERING_DESCRIPTION
            
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректную сумму!")
            return ENTERING_AMOUNT
    
    async def handle_description_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода описания"""
        description = update.message.text
        user_id = update.effective_user.id
        state = self.user_states[user_id]
        
        # Сохраняем транзакцию
        self.db.add_transaction(
            user_id=user_id,
            amount=state['amount'],
            category=state['category'],
            description=description,
            transaction_type=state['transaction_type']
        )
        
        # Проверяем достижения
        await self.check_achievements(user_id, state['amount'], state['transaction_type'])
        
        # Очищаем состояние
        del self.user_states[user_id]
        
        emoji = "💰" if state['transaction_type'] == 'income' else "💸"
        await update.message.reply_text(
            f"{emoji} Транзакция сохранена!\n"
            f"Сумма: {state['amount']} руб.\n"
            f"Категория: {state['category']}\n"
            f"Описание: {description}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]])
        )
        
        return ConversationHandler.END
    
    async def show_balance(self, query):
        """Показать баланс пользователя"""
        user_id = query.from_user.id
        balance = self.db.get_user_balance(user_id)
        
        # Получаем последние транзакции
        transactions = self.db.get_transactions(user_id, 5)
        
        balance_text = f"💰 Ваш баланс: {balance:.2f} руб.\n\n"
        
        if transactions:
            balance_text += "📋 Последние транзакции:\n"
            for trans in transactions:
                emoji = "💰" if trans['type'] == 'income' else "💸"
                date = trans['date'][:10]  # Берем только дату
                balance_text += f"{emoji} {trans['amount']} руб. - {trans['category']} ({date})\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(balance_text, reply_markup=reply_markup)
    
    async def show_goals(self, query):
        """Показать цели пользователя"""
        user_id = query.from_user.id
        goals = self.db.get_user_goals(user_id)
        
        if not goals:
            goals_text = "🎯 У вас пока нет финансовых целей.\n\nСоздайте свою первую цель!"
            keyboard = [
                [InlineKeyboardButton("➕ Добавить цель", callback_data="add_goal")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
            ]
        else:
            goals_text = "🎯 Ваши финансовые цели:\n\n"
            for goal in goals:
                status = "✅" if goal['is_completed'] else "⏳"
                progress = (goal['current_amount'] / goal['target_amount']) * 100
                goals_text += f"{status} {goal['title']}\n"
                goals_text += f"   Прогресс: {goal['current_amount']:.2f}/{goal['target_amount']:.2f} руб. ({progress:.1f}%)\n\n"
            
            keyboard = [
                [InlineKeyboardButton("➕ Добавить цель", callback_data="add_goal")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(goals_text, reply_markup=reply_markup)
    
    async def start_add_goal(self, query):
        """Начать процесс добавления цели"""
        keyboard = [
            [InlineKeyboardButton("💰 Накопить сумму", callback_data="goal_type_save")],
            [InlineKeyboardButton("💸 Не тратить на категорию", callback_data="goal_type_spend")],
            [InlineKeyboardButton("🔙 Назад", callback_data="goals")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите тип цели:", reply_markup=reply_markup)
    
    async def show_achievements(self, query):
        """Показать достижения пользователя"""
        user_id = query.from_user.id
        user_achievements = self.db.get_user_achievements(user_id)
        points = self.db.get_user_points(user_id)
        
        achievements_text = f"🏆 Ваши достижения\n\n"
        achievements_text += f"💎 Очки: {points}\n\n"
        
        if user_achievements:
            achievements_text += "Полученные достижения:\n"
            for achievement_id in user_achievements:
                if achievement_id in ACHIEVEMENTS:
                    achievement = ACHIEVEMENTS[achievement_id]
                    achievements_text += f"✅ {achievement['name']}\n"
                    achievements_text += f"   {achievement['description']}\n\n"
        else:
            achievements_text += "Пока нет достижений. Продолжайте экономить! 💪\n\n"
        
        # Показываем все доступные достижения
        achievements_text += "Доступные достижения:\n"
        for achievement_id, achievement in ACHIEVEMENTS.items():
            status = "✅" if achievement_id in user_achievements else "🔒"
            achievements_text += f"{status} {achievement['name']} (+{achievement['points']} очков)\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(achievements_text, reply_markup=reply_markup)
    
    async def show_tips(self, query):
        """Показать финансовые советы"""
        tip = random.choice(FINANCIAL_TIPS)
        
        tips_text = f"💡 Финансовый совет дня:\n\n{tip}\n\n"
        tips_text += "💡 Другие полезные советы:\n"
        
        # Показываем еще несколько советов
        other_tips = [t for t in FINANCIAL_TIPS if t != tip][:3]
        for i, tip in enumerate(other_tips, 1):
            tips_text += f"{i}. {tip}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Другой совет", callback_data="tips")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(tips_text, reply_markup=reply_markup)
    
    async def show_analytics_menu(self, query):
        """Показать меню аналитики"""
        keyboard = [
            [InlineKeyboardButton("📊 Расходы по категориям", callback_data="analytics_expenses")],
            [InlineKeyboardButton("📈 Доходы vs Расходы", callback_data="analytics_income_vs_expense")],
            [InlineKeyboardButton("🎯 Прогресс целей", callback_data="analytics_goals")],
            [InlineKeyboardButton("📊 Месячные тренды", callback_data="analytics_trends")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📊 Выберите тип аналитики:", reply_markup=reply_markup)
    
    async def handle_analytics_selection(self, query):
        """Обработка выбора типа аналитики"""
        user_id = query.from_user.id
        analytics_type = query.data.split("_", 1)[1]
        
        await query.edit_message_text("📊 Генерирую график...")
        
        try:
            if analytics_type == "expenses":
                chart_bytes = self.analytics.create_expense_pie_chart(user_id)
                caption = "📊 Расходы по категориям за последние 30 дней"
            elif analytics_type == "income_vs_expense":
                chart_bytes = self.analytics.create_income_vs_expense_chart(user_id)
                caption = "📈 Доходы vs Расходы за последние 30 дней"
            elif analytics_type == "goals":
                chart_bytes = self.analytics.create_savings_progress_chart(user_id)
                caption = "🎯 Прогресс накоплений"
            elif analytics_type == "trends":
                chart_bytes = self.analytics.create_monthly_trend_chart(user_id)
                caption = "📊 Месячные тренды за последние 6 месяцев"
            else:
                await query.edit_message_text("Неизвестный тип аналитики")
                return
            
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="analytics")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_photo(
                chat_id=query.from_user.id,
                photo=chart_bytes,
                caption=caption,
                reply_markup=reply_markup
            )
            
            # Удаляем сообщение "Генерирую график..."
            await query.delete()
            
        except Exception as e:
            await query.edit_message_text(f"Ошибка при создании графика: {str(e)}")
    
    async def show_history(self, query):
        """Показать историю транзакций"""
        user_id = query.from_user.id
        transactions = self.db.get_transactions(user_id, 10)
        
        if not transactions:
            history_text = "📋 У вас пока нет транзакций.\n\nНачните вести учет своих финансов!"
        else:
            history_text = "📋 Последние транзакции:\n\n"
            for i, trans in enumerate(transactions, 1):
                emoji = "💰" if trans['type'] == 'income' else "💸"
                date = trans['date'][:10]
                history_text += f"{i}. {emoji} {trans['amount']} руб.\n"
                history_text += f"   {trans['category']}\n"
                history_text += f"   {trans['description']}\n"
                history_text += f"   {date}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(history_text, reply_markup=reply_markup)
    
    async def show_main_menu(self, query):
        """Показать главное меню"""
        keyboard = [
            [InlineKeyboardButton("💰 Доход", callback_data="income")],
            [InlineKeyboardButton("💸 Расход", callback_data="expense")],
            [InlineKeyboardButton("📊 Баланс", callback_data="balance")],
            [InlineKeyboardButton("🎯 Цели", callback_data="goals")],
            [InlineKeyboardButton("🏆 Достижения", callback_data="achievements")],
            [InlineKeyboardButton("💡 Советы", callback_data="tips")],
            [InlineKeyboardButton("📈 Аналитика", callback_data="analytics")],
            [InlineKeyboardButton("📋 История", callback_data="history")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)
    
    async def check_achievements(self, user_id: int, amount: float, transaction_type: str):
        """Проверка и выдача достижений"""
        balance = self.db.get_user_balance(user_id)
        transactions = self.db.get_transactions(user_id, 1000)
        
        # Проверяем различные достижения
        achievements_to_check = []
        
        # Первая экономия
        if transaction_type == 'income' and balance > 0:
            achievements_to_check.append('first_save')
        
        # Большой накопитель
        if balance >= 1000:
            achievements_to_check.append('big_saver')
        
        # Проверяем недельную экономию (упрощенно)
        if len(transactions) >= 7:
            achievements_to_check.append('week_saver')
        
        # Выдаем достижения
        for achievement_id in achievements_to_check:
            self.db.add_achievement(user_id, achievement_id)
            if achievement_id in ACHIEVEMENTS:
                achievement = ACHIEVEMENTS[achievement_id]
                self.db.update_user_points(user_id, achievement['points'])
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена операции"""
        user_id = update.effective_user.id
        if user_id in self.user_states:
            del self.user_states[user_id]
        
        await update.message.reply_text(
            "Операция отменена.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]])
        )
        
        return ConversationHandler.END 