# services/notifier.py
"""
📢 TELEGRAM NOTIFIER 2030 — УВЕДОМЛЕНИЯ В TELEGRAM
Отправка сообщений о событиях, ошибках, прогрессе
Production ready, без сокращений
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from colorama import Fore, Style

try:
    import aiohttp
except ImportError:
    aiohttp = None

from config.settings import settings


class TelegramNotifier:
    """
    📢 TELEGRAM NOTIFIER 2030
    
    Отправляет уведомления в Telegram:
    - События (login, warmup, alive mode)
    - Ошибки и предупреждения
    - Статистика и прогресс
    - Детальные отчёты
    """
    
    def __init__(self, logger):
        """Инициализация notifier"""
        self.logger = logger
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token or not self.chat_id:
            self.logger.warning("notifier", "Telegram not configured")
    
    # ════════════════════════════════════════════════════════════════
    # ОТПРАВКА СООБЩЕНИЙ
    # ════════════════════════════════════════════════════════════════
    
    async def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown",
        disable_web_page_preview: bool = True,
    ) -> bool:
        """
        Отправить сообщение в Telegram
        
        Args:
            message: Текст сообщения
            parse_mode: Тип форматирования (Markdown, HTML)
            disable_web_page_preview: Отключить preview ссылок
            
        Returns:
            True если отправле��о, False если ошибка
        """
        
        if not self.bot_token or not self.chat_id:
            return False
        
        if not aiohttp:
            self.logger.warning("notifier", "aiohttp not installed")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": disable_web_page_preview,
                }
                
                async with session.post(
                    f"{self.api_url}/sendMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        error = await response.text()
                        self.logger.warning("notifier", f"Telegram error: {error}")
                        return False
        
        except Exception as e:
            self.logger.warning("notifier", f"Failed to send message: {e}")
            return False
    
    # ════════════════════════════════════════════════════════════════
    # СОБЫТИЯ: БОТ
    # ════════════════════════════════════════════════════════════════
    
    async def notify_bot_started(self, total_accounts: int) -> None:
        """Отправить уведомление о запуске бота"""
        
        msg = f"""
✅ *БОТ ЗАПУЩЕН*

📱 Аккаунтов: {total_accounts}
🕐 Время: {datetime.now().strftime('%H:%M:%S')}

Бот готов к работе! 🚀
Используй команды для управления аккаунтами.
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    async def notify_bot_stopped(
        self,
        total_logins: int,
        total_warmups: int,
        total_alive_starts: int,
        runtime_hours: float
    ) -> None:
        """Отправить уведомление об остановке бота"""
        
        msg = f"""
⏹️ *БОТ ОСТАНОВЛЕН*

📊 Статистика:
  • Логинов: {total_logins}
  • Прогревов: {total_warmups}
  • Alive Mode: {total_alive_starts}
  • Время работы: {runtime_hours:.1f} часов

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    # ════════════════════════════════════════════════════════════════
    # СОБЫТИЯ: ЛОГИН
    # ════════════════════════════════════════════════════════════════
    
    async def notify_login_success(
        self,
        account_id: str,
        phone: str,
        method: str = "sms"
    ) -> None:
        """Отправить уведомление об успешном логине"""
        
        method_emoji = "📱" if method == "sms" else "💾"
        method_name = "SMS" if method == "sms" else "Сохранённая сессия"
        
        msg = f"""
✅ *УСПЕШНЫЙ ЛОГИН*

📍 Аккаунт: `{account_id}`
📱 Телефон: {phone}
🔑 Метод: {method_name} {method_emoji}

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    async def notify_login_failed(
        self,
        account_id: str,
        phone: str
    ) -> None:
        """Отправить уведомление об ошибке логина"""
        
        msg = f"""
❌ *ОШИБКА ЛОГИНА*

📍 Аккаунт: `{account_id}`
📱 Телефон: {phone}

⚠️ Не удалось авторизироваться через SMS
Проверь код подтверждения или попробуй позже.

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    # ══════════════��═════════════════════════════════════════════════
    # СОБЫТИЯ: ПРОГРЕВ
    # ════════════════════════════════════════════════════════════════
    
    async def notify_warmup_start(
        self,
        account_id: str,
        start_time: datetime
    ) -> None:
        """Отправить уведомление о начале прогрева"""
        
        msg = f"""
🔥 *ПРОГРЕВ НАЧАЛСЯ*

📍 Аккаунт: `{account_id}`
⏳ Продолжительность: 85-95 минут
📋 Фазы: 5 этапов

🕐 Начало: {start_time.strftime('%H:%M:%S')}

Прогрев будет выполняться в фоне...
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    async def notify_warmup_progress(
        self,
        account_id: str,
        phase: int,
        total_phases: int,
        elapsed_time: float
    ) -> None:
        """Отправить уведомление о прогрессе прогрева"""
        
        progress_bar = "█" * phase + "░" * (total_phases - phase)
        
        msg = f"""
🔥 *ПРОГРЕВ В ПРОЦЕССЕ*

📍 Аккаунт: `{account_id}`
📊 Прогресс: [{progress_bar}] {phase}/{total_phases}
⏱️ Прошло: {elapsed_time:.1f} минут

Продолжаем работу...
🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    async def notify_warmup_complete(
        self,
        account_id: str,
        completed_phases: int,
        total_phases: int,
        total_duration_minutes: float
    ) -> None:
        """Отправить уведомление о завершении прогрева"""
        
        status_emoji = "✅" if completed_phases == total_phases else "⚠️"
        
        msg = f"""
{status_emoji} *ПРОГРЕВ ЗАВЕРШЁН*

📍 Аккаунт: `{account_id}`
📊 Фазы: {completed_phases}/{total_phases}
⏱️ Время: {total_duration_minutes:.1f} минут

{'✅ Прогрев 100% успешно завершён!' if completed_phases == total_phases else '⚠️ Прогрев завершён с ошибками'}

🚀 Запущен Alive Mode
🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    async def notify_warmup_failed(self, account_id: str) -> None:
        """Отправить уведомление об ошибке прогрева"""
        
        msg = f"""
❌ *ОШИБКА ПРОГРЕВА*

📍 Аккаунт: `{account_id}`

⚠️ Прогрев завершился с ошибками
Не все фазы были пройдены успешно

Попробуй ещё раз или проверь логи.
🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    # ════════════════════════════════════════════════════════════════
    # СОБЫТИЯ: ALIVE MODE
    # ════════════════════════════════════════════════════════════════
    
    async def notify_alive_mode_started(self, account_id: str) -> None:
        """Отправить уведомление о начале Alive Mode"""
        
        msg = f"""
🤖 *ALIVE MODE ЗАПУЩЕН*

📍 Аккаунт: `{account_id}`
🕐 Начало: {datetime.now().strftime('%H:%M:%S')}

Бот будет случайно просматривать карточки и добавлять в избранное весь день! 🌙

Бот работает в фоне, ты можешь использовать другие команды.
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    async def notify_alive_next_action(
        self,
        account_id: str,
        time_until_next_seconds: float,
        tiredness_percent: int,
        mood: str,
        action_count: int
    ) -> None:
        """Отправить уведомление о следующем действии в Alive Mode"""
        
        time_minutes = time_until_next_seconds / 60
        tiredness_emoji = self._get_tiredness_emoji(tiredness_percent)
        
        msg = f"""
🤖 *ALIVE MODE — АКТИВЕН*

📍 Аккаунт: `{account_id}`
📊 Действие #{action_count}
⏱️ Следующее действие через: {time_minutes:.1f} мин

😴 Усталость: {tiredness_emoji} {tiredness_percent}%
🎭 Настроение: {mood}

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    # ════════════════════════════════════════════════════════════════
    # ОШИБКИ И ПРЕДУПРЕЖДЕНИЯ
    # ════════════════════════════════════════════════════════════════
    
    async def notify_error(
        self,
        account_id: str,
        error_type: str,
        error_message: str,
        severity: str = "MEDIUM"
    ) -> None:
        """Отправить уведомление об ошибке"""
        
        severity_emoji = {
            "LOW": "⚠️",
            "MEDIUM": "⛔",
            "HIGH": "🔴",
            "CRITICAL": "🚨",
        }.get(severity, "⚠️")
        
        msg = f"""
{severity_emoji} *ОШИБКА* ({severity})

📍 Аккаунт: `{account_id}`
📝 Тип: {error_type}
💬 Сообщение: {error_message}

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    async def notify_warning(
        self,
        account_id: str,
        warning_message: str
    ) -> None:
        """Отправить уведомление о предупреждении"""
        
        msg = f"""
⚠️ *ПРЕДУПРЕЖДЕНИЕ*

📍 Аккаунт: `{account_id}`
💬 {warning_message}

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    # ════════════════════════════════════════════════════════════════
    # ДЕЙСТВИЯ
    # ════════════════════════════════════════════════════════════════
    
    async def notify_deep_view_card(
        self,
        account_id: str,
        card_title: str,
        duration_seconds: float
    ) -> None:
        """Отправить уведомление о глубоком просмотре карточки"""
        
        msg = f"""
👀 *ГЛУБОКИЙ ПРОСМОТР КАРТОЧКИ*

📍 Аккаунт: `{account_id}`
📌 Карточка: {card_title[:50]}...
⏱️ Время просмотра: {duration_seconds:.0f} секунд

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    async def notify_favorite_added(
        self,
        account_id: str,
        card_title: str,
        today_count: int
    ) -> None:
        """Отправить уведомление о добавлении в избранное"""
        
        msg = f"""
❤️ *ДОБАВЛЕНО В ИЗБРАННОЕ*

📍 Аккаунт: `{account_id}`
📌 Карточка: {card_title[:50]}...
📊 Всего за сегодня: {today_count}

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    # ════════════════════════════════════════════════════════════════
    # НОЧНОЙ РЕЖИМ
    # ════════════════════════════════════════════════════════════════
    
    async def notify_night_mode_enabled(
        self,
        account_id: str,
        night_start: str,
        night_end: str
    ) -> None:
        """Отправить уведомление о включении ночного режима"""
        
        msg = f"""
🌙 *НОЧНОЙ РЕЖИМ ВКЛЮЧЕН*

📍 Аккаунт: `{account_id}`
🕐 Период: {night_start} — {night_end}

Бот не будет активничать ночью.
Работа возобновится с утра 🌅
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    # ════════════════════════���═══════════════════════════════════════
    # СТАТИСТИКА
    # ════════════════════════════════════════════════════════════════
    
    async def notify_daily_summary(
        self,
        account_id: str,
        total_actions: int,
        total_views: int,
        total_favorites: int,
        total_errors: int
    ) -> None:
        """Отправить суточный отчёт"""
        
        msg = f"""
📊 *СУТОЧНЫЙ ОТЧЁТ*

📍 Аккаунт: `{account_id}`

📈 Статистика за день:
  • Всего действий: {total_actions}
  • Просмотров: {total_views}
  • В избранное: {total_favorites}
  • Ошибок: {total_errors}

✅ День прошёл успешно!
🕐 {datetime.now().strftime('%H:%M:%S')}
"""
        try:
            await self.send_message(msg, parse_mode="Markdown")
        except Exception:
            pass
    
    # ════════════════════════════════════════════════════════════════
    # УТИЛИТЫ
    # ════════════════════════════════════════════════════════════════
    
    def _get_tiredness_emoji(self, tiredness_percent: int) -> str:
        """Получить эмодзи для усталости"""
        if tiredness_percent < 20:
            return "😄"
        elif tiredness_percent < 40:
            return "😊"
        elif tiredness_percent < 60:
            return "😐"
        elif tiredness_percent < 80:
            return "😴"
        else:
            return "💤"