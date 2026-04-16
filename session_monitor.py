# services/session_monitor.py
"""
📊 SESSION MONITOR 2030 — REAL-TIME МОНИТОРИНГ ВСЕХ ДЕЙСТВИЙ
Логирование в терминал (красиво) + Telegram (подробно)
Production ready, без сокращений
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, TYPE_CHECKING
from enum import Enum
from colorama import Fore, Style, init
import json

if TYPE_CHECKING:
    from services.notifier import TelegramNotifier

init(autoreset=True)


class ActionType(Enum):
    """Типы действий"""
    PHASE_START = "phase_start"
    PHASE_COMPLETE = "phase_complete"
    DEEP_VIEW = "deep_view"
    FAVORITE_ADD = "favorite_add"
    NAVIGATION = "navigation"
    CLICK = "click"
    SCROLL = "scroll"
    LOGIN = "login"
    BROWSER_OPEN = "browser_open"
    BROWSER_CLOSE = "browser_close"
    ALIVE_START = "alive_start"
    ALIVE_STOP = "alive_stop"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class SessionMonitor:
    """
    📊 SESSION MONITOR 2030
    
    Отслеживает:
    - Каждое действие каждого аккаунта
    - Статистику в реальном времени
    - Уровень риска (может ли Avito поймать)
    - Усталость и настроение
    - История действий
    """
    
    def __init__(self, logger, notifier):
        self.logger = logger
        self.notifier = notifier
        
        # Данные о сессиях
        self.sessions: Dict[str, Dict] = {}  # account_id → session_data
        self.action_history: Dict[str, List] = {}  # account_id → [actions]
        
        # Глобальная статистика
        self.global_start = datetime.now()
        self.total_actions = 0
        self.total_errors = 0
        
        # Форматтеры
        self.terminal_width = 90
    
    def init_session(self, account_id: str, phone: str) -> None:
        """Инициализировать сессию аккаунта"""
        self.sessions[account_id] = {
            "phone": phone,
            "start_time": datetime.now(),
            "actions_count": 0,
            "errors_count": 0,
            "current_phase": 0,
            "current_phase_name": None,
            "tiredness": 0.0,
            "mood": "neutral",
            "last_action": None,
            "last_action_time": None,
            "browser_state": "closed",
            "status": "idle",
            "total_viewed": 0,
            "total_favorites": 0,
            "risk_score": 0.0,
        }
        
        self.action_history[account_id] = []
    
    # ════════════════════════════════════════════════════════════════
    # ЛОГИРОВАНИЕ ДЕЙСТВИЙ
    # ════════════════════════════════════════════════════════════════
    
    async def log_action(
        self,
        account_id: str,
        action_type: ActionType,
        details: Dict[str, Any],
        tiredness: float = 0.0,
        mood: str = "neutral",
    ) -> None:
        """
        Залогировать действие в терминал и Telegram
        
        Args:
            account_id: ID аккаунта
            action_type: Тип действия (ActionType enum)
            details: Дополнительные детали
            tiredness: Уровень усталости (0-1)
            mood: Настроение
        """
        
        if account_id not in self.sessions:
            self.init_session(account_id, details.get("phone", "unknown"))
        
        session = self.sessions[account_id]
        
        # Получаем строковое значение action_type
        action_type_str = action_type.value if isinstance(action_type, ActionType) else str(action_type)
        
        # Обновляем статус
        session["last_action"] = action_type_str
        session["last_action_time"] = datetime.now()
        session["tiredness"] = tiredness
        session["mood"] = mood
        session["actions_count"] += 1
        self.total_actions += 1
        
        # Сохраняем в историю
        action_record = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type_str,
            "details": details,
            "tiredness": tiredness,
            "mood": mood,
        }
        self.action_history[account_id].append(action_record)
        
        # ─────────────────────────────────────────────────────
        # ЛОГИРОВАНИЕ В ТЕРМИНАЛ
        # ─────────────────────────────────────────────────────
        
        await self._log_to_terminal(account_id, action_type, details, tiredness, mood)
        
        # ─────────────────────────────────────────────────────
        # ЛОГИРОВАНИЕ В TELEGRAM
        # ─────────────────────────────────────────────────────
        
        try:
            await self._log_to_telegram(account_id, action_type, details, tiredness, mood)
        except Exception as e:
            self.logger.warning("session_monitor", f"Telegram log failed: {e}")
    
    async def _log_to_terminal(
        self,
        account_id: str,
        action_type: ActionType,
        details: Dict[str, Any],
        tiredness: float,
        mood: str,
    ) -> None:
        """Логирование в терминал (красиво)"""
        
        phone = self.sessions[account_id]["phone"]
        acc_num = account_id.split("_")[-1]
        
        # Временная ��етка
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Получаем строковое значение
        action_type_str = action_type.value if isinstance(action_type, ActionType) else str(action_type)
        
        # ─────────────────────────────────────────────────────
        # ФОРМАТИРОВАНИЕ ПО ТИПАМ
        # ─────────────────────────────────────────────────────
        
        if action_type == ActionType.PHASE_START:
            phase_num = details.get("phase", "?")
            total_phases = details.get("total_phases", 5)
            phase_name = details.get("phase_name", "Unknown")
            
            msg = f"\n{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}"
            msg += f"\n{Fore.LIGHTYELLOW_EX}[ФАЗА {phase_num}/{total_phases}] {phase_name}{Style.RESET_ALL}"
            msg += f"\n  📍 Аккаунт {acc_num} ({phone})"
            msg += f"\n  ⏱️ {timestamp}"
            msg += f"\n  ⏳ Целевое время: {details.get('min_duration', 0)//60}-{details.get('max_duration', 0)//60} мин"
            msg += f"\n{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}\n"
            print(msg)
        
        elif action_type == ActionType.PHASE_COMPLETE:
            phase_num = details.get("phase", "?")
            duration = details.get("duration", 0)
            success_count = details.get("success_count", 0)
            error_count = details.get("error_count", 0)
            
            status_color = Fore.GREEN if error_count == 0 else Fore.YELLOW
            
            msg = f"\n{status_color}✅ Фаза {phase_num} ЗАВЕРШЕНА{Style.RESET_ALL}"
            msg += f"\n  📍 Аккаунт {acc_num}"
            msg += f"\n  ⏱️ Время: {duration/60:.1f} мин"
            msg += f"\n  ✅ Успешно: {success_count} | ❌ Ошибок: {error_count}"
            msg += f"\n  😴 Усталость: {self._get_tiredness_bar(tiredness)}"
            print(msg)
        
        elif action_type == ActionType.DEEP_VIEW:
            card_title = details.get("card_title", "Карточка")[:40]
            duration = details.get("duration", 0)
            
            msg = f"  {Fore.CYAN}👀{Style.RESET_ALL} Аккаунт {acc_num}: Глубокий просмотр карточки"
            msg += f"\n     📌 {card_title}..."
            msg += f"\n     ⏱️ {duration:.0f}сек | 😴 {self._get_tiredness_bar(tiredness)}"
            print(msg)
        
        elif action_type == ActionType.FAVORITE_ADD:
            card_title = details.get("card_title", "Карточка")[:40]
            count = details.get("today_count", 1)
            
            msg = f"  {Fore.LIGHTRED_EX}❤️{Style.RESET_ALL} Аккаунт {acc_num}: Добавлено в избранное"
            msg += f"\n     📌 {card_title}..."
            msg += f"\n     📊 {count}-е за сегодня"
            print(msg)
        
        elif action_type == ActionType.NAVIGATION:
            url = details.get("url", "unknown")[:50]
            status = details.get("status", "success")
            status_icon = "✓" if status == "success" else "✗"
            status_color = Fore.GREEN if status == "success" else Fore.RED
            
            msg = f"  {status_color}🌐{Style.RESET_ALL} {status_icon} {url}"
            print(msg)
        
        elif action_type == ActionType.ERROR:
            error_msg = details.get("message", "Unknown error")[:60]
            self.sessions[account_id]["errors_count"] += 1
            self.total_errors += 1
            
            msg = f"  {Fore.RED}❌ Ошибка (Аккаунт {acc_num}): {error_msg}{Style.RESET_ALL}"
            print(msg)
        
        elif action_type == ActionType.WARNING:
            warning_msg = details.get("message", "Warning")[:60]
            
            msg = f"  {Fore.YELLOW}⚠️ Предупреждение (Аккаунт {acc_num}): {warning_msg}{Style.RESET_ALL}"
            print(msg)
        
        elif action_type == ActionType.INFO:
            info_msg = details.get("message", "Info")[:70]
            
            msg = f"  {Fore.CYAN}ℹ️ {info_msg}{Style.RESET_ALL}"
            print(msg)
        
        elif action_type == ActionType.ALIVE_START:
            msg = f"\n{Fore.GREEN}{'─' * 90}{Style.RESET_ALL}"
            msg += f"\n{Fore.GREEN}{'🤖 ALIVE MODE ЗАПУЩЕН':^90}{Style.RESET_ALL}"
            msg += f"\n{Fore.CYAN}{'Аккаунт ' + acc_num + ' (' + phone + ')':^90}{Style.RESET_ALL}"
            msg += f"\n{Fore.GREEN}{'─' * 90}{Style.RESET_ALL}\n"
            print(msg)
        
        elif action_type == ActionType.ALIVE_STOP:
            iterations = details.get("iterations", 0)
            msg = f"\n{Fore.YELLOW}⏹️ Alive Mode остановлен (Аккаунт {acc_num}){Style.RESET_ALL}"
            msg += f"\n   Итераций: {iterations}"
            print(msg)
    
    async def _log_to_telegram(
        self,
        account_id: str,
        action_type: ActionType,
        details: Dict[str, Any],
        tiredness: float,
        mood: str,
    ) -> None:
        """Логирование в Telegram (подробно)"""
        
        phone = self.sessions[account_id]["phone"]
        acc_num = account_id.split("_")[-1]
        
        # ─────────────────────────────────────────────────────
        # ФОРМАТИРОВАНИЕ ПО ТИПАМ
        # ─────────────────────────────────────────────────────
        
        if action_type == ActionType.PHASE_START:
            phase_num = details.get("phase", "?")
            phase_name = details.get("phase_name", "Unknown")
            min_dur = details.get("min_duration", 0)
            max_dur = details.get("max_duration", 0)
            
            msg = f"""
🔥 *ФАЗА {phase_num}/5 НАЧАЛАСЬ*

📍 Аккаунт: `{acc_num}` ({phone})
📋 Название: {phase_name}
⏳ Целевое время: {min_dur//60}-{max_dur//60} мин

😴 Усталость: {self._get_tiredness_emoji(tiredness)} {int(tiredness*100)}%
🎭 Настроение: {mood}
🕐 {datetime.now().strftime('%H:%M:%S')}
"""
            await self.notifier.send_message(msg, parse_mode="Markdown")
        
        elif action_type == ActionType.PHASE_COMPLETE:
            phase_num = details.get("phase", "?")
            duration = details.get("duration", 0)
            success_count = details.get("success_count", 0)
            error_count = details.get("error_count", 0)
            
            status_emoji = "✅" if error_count == 0 else "⚠️"
            
            msg = f"""
{status_emoji} *ФАЗА {phase_num} ЗАВЕРШЕНА*

📍 Аккаунт: `{acc_num}` ({phone})
⏱️ Время выполнения: {duration/60:.1f} мин
✅ Успешно: {success_count}
❌ Ошибок: {error_count}

😴 Усталость: {self._get_tiredness_emoji(tiredness)} {int(tiredness*100)}%
🕐 {datetime.now().strftime('%H:%M:%S')}
"""
            await self.notifier.send_message(msg, parse_mode="Markdown")
        
        elif action_type == ActionType.DEEP_VIEW:
            card_title = details.get("card_title", "Карточка")[:60]
            duration = details.get("duration", 0)
            
            msg = f"""
👀 *ГЛУБОКИЙ ПРОСМОТР КАРТОЧКИ*

📍 Аккаунт: `{acc_num}`
📌 Карточка: {card_title}
⏱️ Время просмотра: {duration:.0f} сек

😴 Усталость: {int(tiredness*100)}%
🕐 {datetime.now().strftime('%H:%M:%S')}
"""
            await self.notifier.send_message(msg, parse_mode="Markdown")
        
        elif action_type == ActionType.FAVORITE_ADD:
            card_title = details.get("card_title", "Карточка")[:60]
            count = details.get("today_count", 1)
            
            msg = f"""
❤️ *ДОБАВЛЕНО В ИЗБРАННОЕ*

📍 Аккаунт: `{acc_num}`
📌 Карточка: {card_title}
📊 Всего за сегодня: {count}

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
            await self.notifier.send_message(msg, parse_mode="Markdown")
        
        elif action_type == ActionType.ERROR:
            error_msg = details.get("message", "Unknown error")
            severity = details.get("severity", "MEDIUM")
            
            msg = f"""
❌ *ОШИБКА* ({severity})

📍 Аккаунт: `{acc_num}` ({phone})
📝 Сообщение: {error_msg}

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
            await self.notifier.send_message(msg, parse_mode="Markdown")
        
        elif action_type == ActionType.ALIVE_START:
            msg = f"""
🤖 *ALIVE MODE ЗАПУЩЕН*

📍 Аккаунт: `{acc_num}` ({phone})
🕐 Начало: {datetime.now().strftime('%H:%M:%S')}

Бот будет случайно просматривать карточки и добавлять в избранное весь день 🌙
"""
            await self.notifier.send_message(msg, parse_mode="Markdown")
    
    # ════════════════════════════════════════════════════════════════
    # УТИЛИТЫ
    # ════════════════════════════════════════════════════════════════
    
    def _get_tiredness_bar(self, tiredness: float) -> str:
        """Получить визуальную полоску усталости"""
        level = int(tiredness * 10)
        bar = "█" * level + "░" * (10 - level)
        
        if tiredness < 0.3:
            color = Fore.GREEN
        elif tiredness < 0.6:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        
        return f"{color}{bar}{Style.RESET_ALL} {int(tiredness*100)}%"
    
    def _get_tiredness_emoji(self, tiredness: float) -> str:
        """Получить эмодзи для усталости"""
        if tiredness < 0.2:
            return "😄"
        elif tiredness < 0.4:
            return "😊"
        elif tiredness < 0.6:
            return "😐"
        elif tiredness < 0.8:
            return "😴"
        else:
            return "💤"
    
    def get_session_status(self, account_id: str) -> Dict:
        """Получить статус сессии"""
        if account_id not in self.sessions:
            return None
        
        session = self.sessions[account_id]
        elapsed = (datetime.now() - session["start_time"]).total_seconds()
        
        return {
            "account_id": account_id,
            "phone": session["phone"],
            "elapsed_time": elapsed,
            "actions_count": session["actions_count"],
            "errors_count": session["errors_count"],
            "tiredness": session["tiredness"],
            "mood": session["mood"],
            "status": session["status"],
            "last_action": session["last_action"],
            "last_action_time": session["last_action_time"],
        }
    
    def get_global_stats(self) -> Dict:
        """Получить глобальную статистику"""
        elapsed = (datetime.now() - self.global_start).total_seconds()
        
        return {
            "total_actions": self.total_actions,
            "total_errors": self.total_errors,
            "total_accounts": len(self.sessions),
            "elapsed_time": elapsed,
            "average_actions_per_account": self.total_actions / max(len(self.sessions), 1),
        }
    
    def get_action_history(self, account_id: str, limit: int = 20) -> List:
        """Получить историю действий аккаунта"""
        if account_id not in self.action_history:
            return []
        
        return self.action_history[account_id][-limit:]