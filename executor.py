# core/engine/executor.py
"""
⚡ ACTION EXECUTOR 2030 — ЕДИНАЯ ТОЧКА ВЫПОЛНЕНИЯ ВСЕХ ДЕЙСТВИЙ
"""

from __future__ import annotations  # ← ДОБАВЬ ЭТО СТРОКА В САМЫЙ ВЕРХ!

import asyncio
import random
from datetime import datetime
from typing import Callable, Any, Dict, Optional, Tuple, TYPE_CHECKING
from colorama import Fore, Style

from core.safety.circuit_breaker import CircuitBreaker
from core.safety.risk_analyzer import RiskAnalyzer, RiskLevel
from core.safety.night_mode import NightMode

# Используем TYPE_CHECKING для избежания циклических импортов
if TYPE_CHECKING:
    from playwright.async_api import Page
    from core.browser.launcher import BrowserLauncher
    from core.human.behavior import HumanBehavior


class ActionExecutor:
    """⚡ ActionExecutor 2030"""

    def __init__(
        self,
        circuit_breaker: CircuitBreaker,
        risk_analyzer: RiskAnalyzer,
        night_mode: NightMode,
        logger,
        notifier=None,
    ):
        """Инициализация executor"""
        self.cb = circuit_breaker
        self.risk = risk_analyzer
        self.night = night_mode
        self.logger = logger
        self.notifier = notifier

    # ══════════════════════════════════════════════════��═════════════
    # ОСНОВНОЙ EXECUTE МЕТОД
    # ════════════════════════════════════════════════════════════════

    async def execute(
        self,
        account_id: str,
        action_name: str,
        callback: Callable,
        *args,
        skip_night_check: bool = False,
        skip_risk_check: bool = False,
        **kwargs,
    ) -> Dict:
        """
        Выполнить действие с проверкой всех фильтров
        
        Args:
            account_id: ID аккаунта
            action_name: Название действия (для логирования)
            callback: Async функция для выполнения
            skip_night_check: Пропустить проверку ночного режима
            skip_risk_check: Пропустить проверку рисков
            
        Returns:
            Dict с результатом, статусом и деталями
        """
        
        result = {
            "account_id": account_id,
            "action": action_name,
            "timestamp": datetime.now().isoformat(),
            "status": "PENDING",
            "checks": {},
            "result": None,
            "error": None,
            "duration": 0.0,
        }

        # ─────────────────────────────────────────────────────────────
        # 1. NIGHT MODE CHECK
        # ─────────────────────────────────────────────────────────────
        
        if not skip_night_check:
            can_work = self.night.can_work(account_id)
            result["checks"]["night_mode"] = {"can_work": can_work}

            if not can_work:
                result["status"] = "BLOCKED_NIGHT"
                self.logger.action(account_id, action_name, "BLOCKED_NIGHT")
                return result

        # ─────────────────────────────────────────────────────────────
        # 2. CIRCUIT BREAKER CHECK
        # ─────────────────────────────────────────────────────────────
        
        can_proceed = self.cb.can_proceed(account_id)
        result["checks"]["circuit_breaker"] = {"can_proceed": can_proceed}

        if not can_proceed:
            status = self.cb.get_status(account_id)
            recovery = status.get("recovery_minutes", 0)
            result["status"] = "BLOCKED_CIRCUIT_BREAKER"
            self.logger.action(
                account_id,
                action_name,
                "BLOCKED_CB",
                recovery_minutes=recovery
            )
            return result

        # ─────────────────────────────────────────────────────────────
        # 3. RISK ANALYSIS CHECK
        # ─────────────────────────────────────────────────────────────
        
        if not skip_risk_check:
            risk_level, risk_details = await self.risk.analyze(account_id)
            result["checks"]["risk"] = risk_details

            if risk_level == RiskLevel.CRITICAL:
                self.cb.record_error(account_id, "CRITICAL risk level", "CRITICAL")
                result["status"] = "BLOCKED_RISK_CRITICAL"
                self.logger.action(account_id, action_name, "BLOCKED_RISK_CRITICAL")
                return result

            if risk_level == RiskLevel.HIGH:
                pause = await self.risk.get_recommended_pause(account_id)
                if pause > 0:
                    self.logger.info(account_id, f"Risk pause: {pause:.1f}s")
                    await asyncio.sleep(pause)

        # ─────────────────────────────────────────────────────────────
        # 4. ПРЕ-ПАУЗА (натуральное поведение)
        # ─────────────────────────────────────────────────────────────
        
        pre_pause = random.uniform(0.5, 2.0)
        await asyncio.sleep(pre_pause)

        # ─────────────────────────────────────────────────────────────
        # 5. ВЫПОЛНЕНИЕ ДЕЙСТВИЯ
        # ─────────────────────────────────────────────────────────────
        
        start = datetime.now()
        try:
            if asyncio.iscoroutinefunction(callback):
                action_result = await callback(*args, **kwargs)
            else:
                action_result = callback(*args, **kwargs)

            duration = (datetime.now() - start).total_seconds()

            result["status"] = "SUCCESS"
            result["result"] = action_result
            result["duration"] = duration

            # Записываем успех
            self.cb.record_success(account_id)
            self.risk.record_action(account_id)

            self.logger.action(
                account_id,
                action_name,
                "SUCCESS",
                duration=duration
            )

        except Exception as e:
            duration = (datetime.now() - start).total_seconds()

            result["status"] = "ERROR"
            result["error"] = str(e)
            result["duration"] = duration

            # Записываем ошибку
            self.cb.record_error(account_id, str(e), "HIGH")

            self.logger.error(
                account_id,
                f"{action_name} failed: {str(e)[:100]}",
                severity="HIGH"
            )

        # ─────────────────────────────────────────────────────────────
        # 6. ПОСТ-ПАУЗА
        # ─────────────────────────────────────────────────────────────
        
        post_pause = random.uniform(0.3, 1.5)
        await asyncio.sleep(post_pause)

        return result

    # ════════════════════════════════════════════════════════════════
    # СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ДЛЯ AVITO
    # ════════════════════════════════════════════════════════════════

    async def execute_navigation(
        self,
        page: Page,
        account_id: str,
        url: str,
        wait_until: str = "domcontentloaded",
        browser_launcher: BrowserLauncher | None = None,
    ) -> bool:
        """
        ВЫПОЛНИТЬ НАВИГАЦИЮ НА URL
        
        Особенности:
        - Проходит через все фильтры (Night Mode, CB, Risk)
        - Использует browser_launcher.goto_safe() для максимальной устойчивости
        - Возвращает True/False (не dict)
        
        Args:
            page: Playwright Page
            account_id: ID аккаунта
            url: URL для перехода
            wait_until: Тип ожидания (domcontentloaded, networkidle, load)
            browser_launcher: BrowserLauncher для использования goto_safe
            
        Returns:
            True если успешно, False если ошибка
        """
        
        try:
            # ─────────────────────────────────────────────────────
            # 1. NIGHT MODE
            # ─────────────────────────────────────────────────────
            
            if not self.night.can_work(account_id):
                self.logger.warning(account_id, f"Navigation blocked by night mode: {url[:60]}")
                return False

            # ─────────────────────────────────────────────────────
            # 2. CIRCUIT BREAKER
            # ─────────────────────────────────────────────────────
            
            if not self.cb.can_proceed(account_id):
                self.logger.warning(account_id, f"Navigation blocked by circuit breaker: {url[:60]}")
                return False

            # ─────────────────────────────────────────────────────
            # 3. RISK ANALYSIS
            # ─────────────────────────────────────────────────────
            
            risk_level, risk_details = await self.risk.analyze(account_id)
            
            if risk_level == RiskLevel.CRITICAL:
                self.logger.error(account_id, f"Navigation blocked: CRITICAL risk for {url[:60]}", severity="HIGH")
                self.cb.record_error(account_id, "CRITICAL risk", "CRITICAL")
                return False

            # ─────────────────────────────────────────────────────
            # 4. НАВИГАЦИЯ
            # ─────────────────────────────────────────────────────
            
            start = datetime.now()
            
            try:
                if browser_launcher:
                    # Используем goto_safe из browser_launcher
                    success = await browser_launcher.goto_safe(
                        page=page,
                        account_id=account_id,
                        url=url,
                        wait_until=wait_until
                    )
                else:
                    # Fallback на прямую навигацию
                    try:
                        await asyncio.wait_for(
                            page.goto(url, wait_until=wait_until, timeout=20000),
                            timeout=25.0
                        )
                        success = True
                    except Exception as e:
                        self.logger.warning(account_id, f"Direct navigation failed: {str(e)[:80]}")
                        success = False
                
                duration = (datetime.now() - start).total_seconds()
                
                if success:
                    self.cb.record_success(account_id)
                    self.risk.record_action(account_id)
                    self.logger.action(account_id, "NAVIGATE", "SUCCESS", url=url[:60], duration=duration)
                else:
                    self.cb.record_error(account_id, f"Navigation timeout: {url[:60]}", "MEDIUM")
                    self.logger.action(account_id, "NAVIGATE", "FAILED", url=url[:60])
                
                return success
                
            except Exception as e:
                duration = (datetime.now() - start).total_seconds()
                self.cb.record_error(account_id, f"Navigation error: {str(e)[:80]}", "HIGH")
                self.logger.error(account_id, f"Navigation error: {str(e)[:100]}", severity="HIGH")
                return False

        except Exception as e:
            self.logger.error(account_id, f"Execute navigation wrapper error: {e}", severity="HIGH")
            return False

    async def execute_click(
        self,
        page: Page,
        account_id: str,
        selector: str,
        browser_launcher: BrowserLauncher | None = None,
    ) -> bool:
        """
        ВЫПОЛНИТЬ КЛИК НА ЭЛЕМЕНТ
        
        Особенности:
        - Проходит через все фильтры
        - Retry при ошибке
        - Натуральная пауза после клика
        
        Args:
            page: Playwright Page
            account_id: ID аккаунта
            selector: CSS selector элемента
            browser_launcher: BrowserLauncher (не используется, для совместимости)
            
        Returns:
            True если успешно, False если ошибка
        """
        
        start = None
        
        try:
            # ─────────────────────────────────────────────────────
            # ФИЛЬТРЫ
            # ─────────────────────────────────────────────────────
            
            if not self.night.can_work(account_id):
                return False

            if not self.cb.can_proceed(account_id):
                return False

            risk_level, _ = await self.risk.analyze(account_id)
            if risk_level == RiskLevel.CRITICAL:
                self.cb.record_error(account_id, "CRITICAL risk", "CRITICAL")
                return False

            # ─────────────────────────────────────────────────────
            # КЛИК С RETRY
            # ─────────────────────────────────────────────────────
            
            start = datetime.now()
            
            for attempt in range(1, 3):
                try:
                    await page.locator(selector).first.click(timeout=5000)
                    
                    # Натуральная пауза
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    duration = (datetime.now() - start).total_seconds()
                    
                    self.cb.record_success(account_id)
                    self.risk.record_action(account_id)
                    self.logger.action(
                        account_id,
                        "CLICK",
                        "SUCCESS",
                        selector=selector[:40],
                        duration=duration
                    )
                    return True
                    
                except Exception as e:
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    else:
                        raise

            return False
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds() if start else 0
            self.cb.record_error(account_id, str(e), "MEDIUM")
            self.logger.error(
                account_id,
                f"Click error: {str(e)[:80]}",
                severity="MEDIUM"
            )
            return False

    async def execute_deep_view_card(
        self,
        page: Page,
        account_id: str,
        selector_index: int,
        browser_launcher: BrowserLauncher | None = None,
        human_behavior: HumanBehavior | None = None,
    ) -> bool:
        """
        ВЫПОЛНИТЬ ГЛУБОКИЙ ПРОСМОТР КАРТОЧКИ
        
        Процесс:
        1. Открыть карточку
        2. Просмотреть фото 20-45 сек
        3. Прочитать описание 10-25 сек
        4. Посмотреть детали/отзывы
        5. Вернуться назад
        
        Args:
            page: Playwright Page
            account_id: ID аккаунта
            selector_index: Индекс карточки в списке
            browser_launcher: BrowserLauncher (не используется)
            human_behavior: HumanBehavior для использования deep_view_card()
            
        Returns:
            True если успешно, False если ошибка
        """
        
        start = None
        
        try:
            # ─────────────────────────────────────────────────────
            # ФИЛЬТРЫ
            # ─────────────────────────────────────────────────────
            
            if not self.night.can_work(account_id):
                return False

            if not self.cb.can_proceed(account_id):
                return False

            risk_level, _ = await self.risk.analyze(account_id)
            if risk_level == RiskLevel.CRITICAL:
                self.cb.record_error(account_id, "CRITICAL risk", "CRITICAL")
                return False

            # ─────────────────────────────────────────────────────
            # ГЛУБОКИЙ ПРОСМОТР
            # ─────────────────────────────────────────────────────
            
            if not human_behavior:
                self.logger.warning(account_id, "Deep view failed: no human_behavior")
                return False

            start = datetime.now()

            success = await human_behavior.deep_view_card(
                page=page,
                selector_index=selector_index,
                duration_seconds=random.uniform(45, 90)
            )

            duration = (datetime.now() - start).total_seconds()

            if success:
                self.cb.record_success(account_id)
                self.risk.record_action(account_id)
                self.logger.action(
                    account_id,
                    "DEEP_VIEW_CARD",
                    "SUCCESS",
                    index=selector_index,
                    duration=duration
                )
            else:
                self.cb.record_error(account_id, f"Deep view failed", "LOW")
                self.logger.action(
                    account_id,
                    "DEEP_VIEW_CARD",
                    "FAILED",
                    index=selector_index
                )

            return success
            
        except Exception as e:
            self.logger.error(account_id, f"Deep view card error: {str(e)[:80]}", severity="MEDIUM")
            self.cb.record_error(account_id, str(e), "LOW")
            return False

    async def execute_natural_favorite(
        self,
        page: Page,
        account_id: str,
        selector_index: int,
        browser_launcher: BrowserLauncher | None = None,
        human_behavior: HumanBehavior | None = None,
    ) -> bool:
        """
        ВЫПОЛНИТЬ ДОБАВЛЕНИЕ В ИЗБРАННОЕ (ЕСТЕСТВЕННО)
        
        Процесс:
        1. Открыть карточку
        2. Посмотреть её (short view)
        3. Найти кнопку "в избранное"
        4. Добавить с паузой (показать раздумье)
        5. Вернуться
        
        Args:
            page: Playwright Page
            account_id: ID аккаунта
            selector_index: Индекс карточки в списке
            browser_launcher: BrowserLauncher (не используется)
            human_behavior: HumanBehavior для использования natural_favorite()
            
        Returns:
            True если успешно добавлено в избранное, False если ошибка
        """
        
        start = None
        
        try:
            # ─────────────────────────────────────────────────────
            # ФИЛЬТРЫ
            # ─────────────────────────────────────────────────────
            
            if not self.night.can_work(account_id):
                return False

            if not self.cb.can_proceed(account_id):
                return False

            risk_level, _ = await self.risk.analyze(account_id)
            if risk_level == RiskLevel.CRITICAL:
                self.cb.record_error(account_id, "CRITICAL risk", "CRITICAL")
                return False

            # ─────────────────────────────────────────────────────
            # ДОБАВЛЕНИЕ В ИЗБРАННОЕ
            # ─────────────────────────────────────────────────────
            
            if not human_behavior:
                self.logger.warning(account_id, "Natural favorite failed: no human_behavior")
                return False

            start = datetime.now()

            success = await human_behavior.natural_favorite(
                page=page,
                selector_index=selector_index
            )

            duration = (datetime.now() - start).total_seconds()

            if success:
                self.cb.record_success(account_id)
                self.risk.record_action(account_id)
                self.logger.action(
                    account_id,
                    "ADD_FAVORITE",
                    "SUCCESS",
                    index=selector_index,
                    duration=duration
                )
            else:
                self.cb.record_error(account_id, "Add favorite failed", "LOW")
                self.logger.action(
                    account_id,
                    "ADD_FAVORITE",
                    "FAILED",
                    index=selector_index
                )

            return success
            
        except Exception as e:
            self.logger.error(account_id, f"Natural favorite error: {str(e)[:80]}", severity="MEDIUM")
            self.cb.record_error(account_id, str(e), "LOW")
            return False

    # ════════════════════════════════════════════════════════════════
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ════════════════════════════════════════════════════════════════

    async def get_account_status(self, account_id: str) -> Dict:
        """Получить полный статус аккаунта"""
        return {
            "circuit_breaker": self.cb.get_status(account_id),
            "night_mode": self.night.get_status(account_id),
            "risk_analysis": await self.risk.get_status(account_id),
        }

    def reset_account(self, account_id: str) -> None:
        """Сбросить все фильтры для аккаунта"""
        self.cb.reset(account_id)
        self.risk.reset(account_id)
        self.logger.action(account_id, "RESET", "SUCCESS")