# services/action_logger.py
"""
📝 ACTION LOGGER 2030 — ДОПОЛНИТЕЛЬНОЕ ЛОГИРОВАНИЕ С CONTEXTUALIZED ИНФОРМАЦИЕЙ
Интеграция с session_monitor для единого логирования
"""

from typing import Optional, Dict, Any
from datetime import datetime
import asyncio


class ActionLogger:
    """
    📝 ACTION LOGGER
    
    Логирует все действия через session_monitor
    """
    
    def __init__(self, session_monitor):
        self.monitor = session_monitor
    
    # ════════════════════════════════════════════════════════════════
    # ФАЗА ПРОГРЕВА
    # ════════════════════════════════════════════════════════════════
    
    async def log_warmup_phase_start(
        self,
        account_id: str,
        phase_num: int,
        total_phases: int,
        phase_name: str,
        min_duration: int,
        max_duration: int,
        tiredness: float = 0.0,
        mood: str = "neutral",
    ) -> None:
        """Залогировать начало фазы прогрева"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.PHASE_START,
            details={
                "phase": phase_num,
                "total_phases": total_phases,
                "phase_name": phase_name,
                "min_duration": min_duration,
                "max_duration": max_duration,
            },
            tiredness=tiredness,
            mood=mood,
        )
    
    async def log_warmup_phase_complete(
        self,
        account_id: str,
        phase_num: int,
        duration: float,
        success_count: int,
        error_count: int,
        tiredness: float = 0.0,
        mood: str = "neutral",
    ) -> None:
        """Залогировать завершение фазы"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.PHASE_COMPLETE,
            details={
                "phase": phase_num,
                "duration": duration,
                "success_count": success_count,
                "error_count": error_count,
            },
            tiredness=tiredness,
            mood=mood,
        )
    
    # ════════════════════════════════════════════════════════════════
    # ДЕЙСТВИЯ
    # ════════════════════════════════════════════════════════════════
    
    async def log_deep_view_card(
        self,
        account_id: str,
        card_title: str,
        duration: float,
        tiredness: float = 0.0,
        mood: str = "neutral",
    ) -> None:
        """Залогировать глубокий просмотр карточки"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.DEEP_VIEW,
            details={
                "card_title": card_title,
                "duration": duration,
            },
            tiredness=tiredness,
            mood=mood,
        )
    
    async def log_favorite_added(
        self,
        account_id: str,
        card_title: str,
        today_count: int,
        tiredness: float = 0.0,
        mood: str = "neutral",
    ) -> None:
        """Залогировать добавление в избранное"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.FAVORITE_ADD,
            details={
                "card_title": card_title,
                "today_count": today_count,
            },
            tiredness=tiredness,
            mood=mood,
        )
    
    async def log_navigation(
        self,
        account_id: str,
        url: str,
        status: str = "success",
        duration: float = 0.0,
    ) -> None:
        """Залогировать навигацию"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.NAVIGATION,
            details={
                "url": url,
                "status": status,
                "duration": duration,
            },
        )
    
    async def log_error(
        self,
        account_id: str,
        message: str,
        severity: str = "MEDIUM",
        exception: Optional[Exception] = None,
    ) -> None:
        """Залогировать ошибку"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.ERROR,
            details={
                "message": message,
                "severity": severity,
                "exception": str(exception) if exception else None,
            },
        )
    
    async def log_warning(
        self,
        account_id: str,
        message: str,
    ) -> None:
        """Залогировать предупреждение"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.WARNING,
            details={
                "message": message,
            },
        )
    
    async def log_info(
        self,
        account_id: str,
        message: str,
    ) -> None:
        """Залогировать информацию"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.INFO,
            details={
                "message": message,
            },
        )
    
    async def log_alive_mode_start(
        self,
        account_id: str,
        phone: str,
    ) -> None:
        """Залогировать начало Alive Mode"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.ALIVE_START,
            details={
                "phone": phone,
            },
        )
    
    async def log_alive_mode_stop(
        self,
        account_id: str,
        iterations: int,
    ) -> None:
        """Залогировать остановку Alive Mode"""
        from services.session_monitor import ActionType
        
        await self.monitor.log_action(
            account_id=account_id,
            action_type=ActionType.ALIVE_STOP,
            details={
                "iterations": iterations,
            },
        )