"""
🚨 CIRCUIT BREAKER — Защита от блокировки
После N ошибок отключает аккаунт на M минут
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
from colorama import Fore, Style

from config.settings import settings


class CircuitBreaker:
    """🚨 Выключатель для защиты от блокировки"""

    def __init__(self, logger, notifier=None):
        self.logger = logger
        self.notifier = notifier
        
        # Статусы: {account_id: {"state": "CLOSED|OPEN|HALF_OPEN", "errors": int, "opened_at": datetime}}
        self.states: Dict[str, dict] = {}

    def _ensure_state(self, account_id: str):
        """Инициализировать состояние если нужно"""
        if account_id not in self.states:
            self.states[account_id] = {
                "state": "CLOSED",
                "errors": 0,
                "opened_at": None,
                "last_success": datetime.now(),
            }

    def can_proceed(self, account_id: str) -> bool:
        """Может ли выполняться действие?"""
        self._ensure_state(account_id)
        state = self.states[account_id]

        if state["state"] == "CLOSED":
            return True

        if state["state"] == "OPEN":
            # Проверить, прошло ли время восстановления
            cooldown = settings.circuit_breaker_cooldown_minutes * 60
            elapsed = (datetime.now() - state["opened_at"]).total_seconds()
            
            if elapsed > cooldown:
                state["state"] = "HALF_OPEN"
                state["errors"] = 0
                return True
            return False

        if state["state"] == "HALF_OPEN":
            # В режиме восстановления - позволяем пробовать
            return True

        return False

    def record_success(self, account_id: str):
        """Записать успешное действие"""
        self._ensure_state(account_id)
        state = self.states[account_id]
        
        state["errors"] = 0
        state["last_success"] = datetime.now()
        
        if state["state"] == "HALF_OPEN":
            state["state"] = "CLOSED"
            self.logger.success(
                account_id,
                f"🔄 Circuit Breaker восстановлен"
            )

    def record_error(self, account_id: str, error: str, severity: str = "MEDIUM"):
        """Записать ошибку"""
        self._ensure_state(account_id)
        state = self.states[account_id]
        
        state["errors"] += 1
        
        self.logger.error(
            account_id,
            f"Circuit Breaker: {error} ({state['errors']}/{settings.circuit_breaker_threshold})",
            severity=severity
        )

        # Если ошибок слишком много - открываем выключатель
        if state["errors"] >= settings.circuit_breaker_threshold:
            state["state"] = "OPEN"
            state["opened_at"] = datetime.now()
            
            self.logger.error(
                account_id,
                f"🚨 CIRCUIT BREAKER OPEN! Паузa {settings.circuit_breaker_cooldown_minutes} мин",
                severity="CRITICAL"
            )
            
            if self.notifier:
                try:
                    import asyncio
                    asyncio.create_task(
                        self.notifier.notify_circuit_breaker(account_id, error)
                    )
                except Exception:
                    pass

    def reset(self, account_id: str):
        """Ручной сброс"""
        self._ensure_state(account_id)
        self.states[account_id] = {
            "state": "CLOSED",
            "errors": 0,
            "opened_at": None,
            "last_success": datetime.now(),
        }
        self.logger.success(account_id, "Circuit Breaker вручную сброшен")

    def get_status(self, account_id: str) -> Dict:
        """Получить статус выключателя"""
        self._ensure_state(account_id)
        state = self.states[account_id]
        
        recovery_minutes = 0
        if state["state"] == "OPEN" and state["opened_at"]:
            cooldown = settings.circuit_breaker_cooldown_minutes * 60
            elapsed = (datetime.now() - state["opened_at"]).total_seconds()
            recovery_minutes = int((cooldown - elapsed) / 60)
        
        return {
            "state": state["state"],
            "errors": state["errors"],
            "threshold": settings.circuit_breaker_threshold,
            "recovery_minutes": max(0, recovery_minutes),
        }

    def print_status(self):
        """Вывести статус всех Circuit Breaker'ов"""
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'🚨 CIRCUIT BREAKER STATUS':^60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

        for account_id, state in self.states.items():
            status = self.get_status(account_id)
            
            state_color = {
                "CLOSED": Fore.GREEN,
                "HALF_OPEN": Fore.YELLOW,
                "OPEN": Fore.RED,
            }.get(status["state"], Fore.WHITE)
            
            print(f"  {Fore.YELLOW}{account_id}{Style.RESET_ALL}")
            print(f"    Статус: {state_color}{status['state']}{Style.RESET_ALL}")
            print(f"    Ошибок: {status['errors']}/{status['threshold']}")
            
            if status["state"] == "OPEN":
                print(f"    Восстановление через: {status['recovery_minutes']} мин")
            
            print()

        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")