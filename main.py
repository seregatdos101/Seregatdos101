# main.py
"""
🚀 AVITO BOT PRO 2030 — ГЛАВНЫЙ ФАЙЛ
ПОЛНОСТЬЮ АСИНХРОННЫЙ, PRODUCTION-READY
Управление 3+ аккаунтами одновременно, real-time мониторинг, Telegram уведомления
БЕЗ СОКРАЩЕНИЙ, максимально детальный
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from colorama import Fore, Style, init
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
import sys

init(autoreset=True)

from config.settings import settings
from services.logger import Logger
from services.metrics import MetricsCollector
from services.notifier import TelegramNotifier
from services.session_monitor import SessionMonitor, ActionType
from services.action_logger import ActionLogger
from core.account.manager import AccountManager
from core.browser.launcher import BrowserLauncher
from core.proxy.manager import ProxyManager
from core.proxy.checker import check_all_proxies
from core.safety.circuit_breaker import CircuitBreaker
from core.safety.risk_analyzer import RiskAnalyzer
from core.safety.night_mode import NightMode
from core.engine.executor import ActionExecutor
from core.avito.navigator import AvitoNavigator
from core.avito.login import login_with_session, login_with_sms
from core.warmup.engine import WarmupEngine, AliveMode
from core.human.behavior import HumanBehavior


class AvitoBot:
    """
    🚀 AVITO BOT PRO 2030 — ГЛАВНЫЙ КЛАСС
    
    Функционал:
    - Управление 3+ аккаунтами одновременно
    - Асинхронный CLI (всегда отзывчив)
    - Полный прогрев (5 фаз, 85-95 мин)
    - Alive Mode (весь день)
    - Real-time мониторинг
    - Telegram уведомления
    - Детальное логирование
    - Защита от блокировок (Night Mode, Circuit Breaker, Risk Analyzer)
    """
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ИНИЦИАЛИЗАЦИЯ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def __init__(self):
        """Инициализация бота с полным функционалом"""
        
        # ─────────────────────────────────────────────────────────────
        # ЛОГИРОВАНИЕ И МОНИТОРИНГ
        # ─────────────────────────────────────────────────────────────
        
        self.logger = Logger()
        self.metrics = MetricsCollector(self.logger)
        self.notifier = TelegramNotifier(self.logger) if settings.telegram_enabled else None
        self.session_monitor = SessionMonitor(self.logger, self.notifier)
        self.action_logger = ActionLogger(self.session_monitor)
        
        # ─────────────────────────────────────────────────────────────
        # БРАУЗЕР И ПРОКСИ
        # ─────────────────────────────────────────────────────────────
        
        self.proxy_manager = ProxyManager(self.logger)
        self.browser_launcher = BrowserLauncher(self.logger, self.proxy_manager)
        
        # ─────────────────────────────────────────────────────────────
        # БЕЗОПАСНОСТЬ
        # ─────────────────────────────────────────────────────────────
        
        self.circuit_breaker = CircuitBreaker(self.logger, self.notifier)
        self.risk_analyzer = RiskAnalyzer(self.logger)
        self.night_mode = NightMode(self.logger, self.notifier)
        
        # ─────────────────────────────────────────────────────────────
        # EXECUTOR И NAVIGATOR
        # ─────────────────────────────────────────────────────────────
        
        self.executor = ActionExecutor(
            circuit_breaker=self.circuit_breaker,
            risk_analyzer=self.risk_analyzer,
            night_mode=self.night_mode,
            logger=self.logger,
            notifier=self.notifier,
        )
        
        self.navigator = AvitoNavigator(self.logger)
        self.warmup_engine = WarmupEngine(
            logger=self.logger,
            executor=self.executor,
            notifier=self.notifier,
        )
        
        # ─────────────────────────────────────────────────────────────
        # УПРАВЛЕНИЕ АККАУНТАМИ И ЗАДАЧАМИ
        # ─────────────────────────────────────────────────────────────
        
        self.accounts: Dict[str, AccountManager] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_counter = 0
        self.alive_modes: Dict[str, AliveMode] = {}
        self.shutdown_event = asyncio.Event()
        
        # ─────────────────────────────────────────────────────────────
        # СТАТИСТИКА
        # ─────────────────────────────────────────────────────────────
        
        self.bot_start_time = datetime.now()
        self.total_logins = 0
        self.total_warmups = 0
        self.total_alive_starts = 0
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ИНИЦИАЛИЗАЦИЯ И ЗАПУСК
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def initialize(self):
        """
        Инициализация бота
        
        Этапы:
        1. Инициализация Playwright
        2. Загрузка конфигурации
        3. Инициализация аккаунтов
        4. Проверка прокси
        5. Подготовка к работе
        """
        
        print(f"\n{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'🤖 AVITO BOT PRO 2030 — ИНИЦИАЛИЗАЦИЯ':^90}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}\n")
        
        self.logger.system("Bot initialization started")
        
        # ─────────────────────────────────────────────────────
        # 1. PLAYWRIGHT
        # ─────────────────────────────────────────────────────
        
        print(f"  {Fore.CYAN}🌐 Инициализирую Playwright...{Style.RESET_ALL}")
        try:
            await self.browser_launcher.initialize()
            print(f"  {Fore.GREEN}✅ Playwright инициализирован{Style.RESET_ALL}")
        except Exception as e:
            print(f"  {Fore.RED}❌ Ошибка инициализации Playwright: {e}{Style.RESET_ALL}")
            raise
        
        # ─────────────────────────────────────────────────────
        # 2. АККАУНТЫ
        # ─────────────────────────────────────────────────────
        
        print(f"  {Fore.CYAN}📱 Загружаю аккаунты...{Style.RESET_ALL}")
        for acc_id, acc_config in settings.accounts.items():
            self.accounts[acc_id] = AccountManager(
                acc_id,
                acc_config,
                self.logger,
                self.notifier,
            )
            print(f"     {Fore.GREEN}✅ {acc_id}: {acc_config['phone']}{Style.RESET_ALL}")
        
        # ─────────────────────────────────────────────────────
        # 3. КОНФИГУРАЦИЯ
        # ─────────────────────────────────────────────────────
        
        print(f"\n{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'⚙️  КОНФИГУРАЦИЯ':^90}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}\n")
        
        settings.print_summary()
        
        # ─────────────────────────────────────────────────────
        # 4. ЛОГИРОВАНИЕ
        # ─────────────────────────────────────────────────────
        
        self.logger.system(f"Bot initialized: {len(self.accounts)} accounts")
        
        try:
            if self.notifier:
                await self.notifier.notify_bot_started(len(self.accounts))
        except Exception as e:
            self.logger.warning("bot", f"Failed to send startup notification: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # УПРАВЛЕНИЕ ЗАДАЧАМИ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def get_account_id(self, num: str) -> str:
        """Конвертировать номер аккаунта в ID"""
        return f"account_{num}"
    
    def _get_next_task_id(self) -> str:
        """Получить уникальный ID для задачи"""
        self.task_counter += 1
        return f"task_{self.task_counter}"
    
    async def _run_task(self, task_id: str, coro) -> None:
        """
        Выполнить корутину с полной обработкой ошибок
        
        Args:
            task_id: ID задачи
            coro: Корутина для выполнения
        """
        try:
            await coro
        except asyncio.CancelledError:
            print(f"\n  {Fore.YELLOW}⏸️ Задача {task_id} отменена{Style.RESET_ALL}")
            self.logger.info("bot", f"Task {task_id} cancelled")
        except Exception as e:
            print(f"\n  {Fore.RED}❌ Ошибка в задаче {task_id}: {str(e)[:100]}{Style.RESET_ALL}")
            self.logger.error("bot", f"Task {task_id} error: {e}", severity="HIGH")
        finally:
            self.running_tasks.pop(task_id, None)
    
    async def _launch_task(self, task_name: str, coro) -> str:
        """
        Запустить новую фо��овую задачу
        
        Args:
            task_name: Название задачи
            coro: Корутина для выполнения
            
        Returns:
            task_id: ID запущенной задачи
        """
        task_id = self._get_next_task_id()
        
        task = asyncio.create_task(
            self._run_task(task_id, coro)
        )
        
        self.running_tasks[task_id] = task
        
        print(f"\n  {Fore.GREEN}✅ {task_name} запущена (задача #{self.task_counter}){Style.RESET_ALL}")
        self.logger.info("bot", f"Task {task_id} started: {task_name}")
        
        return task_id
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # КОМАНДЫ: ЛОГИН
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def cmd_login(self, acc_id: str):
        """
        Логин аккаунта (синхронно, в главном потоке)
        
        Процесс:
        1. Запуск браузера
        2. Попытка входа с сохранённой сессией
        3. Если не работает — вход через SMS
        4. Сохранение cookies
        """
        
        if acc_id not in self.accounts:
            print(f"  {Fore.RED}❌ Аккаунт {acc_id} не найден{Style.RESET_ALL}")
            return
        
        account = self.accounts[acc_id]
        phone = account.phone
        
        print(f"\n{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}🔐 ЛОГИН АККАУНТА: {acc_id} ({phone}){Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}\n")
        
        # Инициализируем мониторинг сессии
        self.session_monitor.init_session(acc_id, phone)
        
        self.total_logins += 1
        self.logger.action(acc_id, "LOGIN", "START", phone=phone)
        
        try:
            # ─────────────────────────────────────────────────────
            # ЗАПУСК БРАУЗЕРА
            # ─────────────────────────────────────────────────────
            
            print(f"  {Fore.CYAN}🌐 Запускаю браузер...{Style.RESET_ALL}")
            await self.action_logger.log_info(acc_id, "Запуск браузера...")
            
            page = await self.browser_launcher.launch(acc_id)
            if not page:
                print(f"  {Fore.RED}❌ Не удалось запустить браузер{Style.RESET_ALL}")
                await self.action_logger.log_error(
                    acc_id,
                    "Не удалось запустить браузер",
                    severity="CRITICAL"
                )
                self.logger.error(acc_id, "Failed to launch browser", severity="CRITICAL")
                return
            
            fp = self.browser_launcher.get_fingerprint(acc_id)
            account.set_page(page, fp)
            
            print(f"  {Fore.GREEN}✅ Браузер запущен{Style.RESET_ALL}")
            await self.action_logger.log_info(acc_id, "Браузер готов")
            
            # ─────────────────────────────────────────────────────
            # ПОПЫТКА ВХОДА С СОХРАНЁННОЙ СЕССИЕЙ
            # ─────────────────────────────────────────────────────
            
            print(f"  {Fore.CYAN}🔑 Пробую вход с сохранённой сессией...{Style.RESET_ALL}")
            await self.action_logger.log_info(acc_id, "Проверка сохранённой сессии...")
            
            is_logged = await login_with_session(
                page,
                acc_id,
                self.navigator,
                self.logger
            )
            
            if is_logged:
                print(f"  {Fore.GREEN}✅ Авторизирован (сохранённая сессия){Style.RESET_ALL}")
                await self.action_logger.log_info(acc_id, "✅ Авторизирован (сохранённая сессия)")
                
                account.set_authenticated(True)
                self.logger.success(acc_id, "Logged in with saved session")
                
                try:
                    if self.notifier:
                        await self.notifier.notify_login_success(acc_id, phone, "saved_session")
                except Exception:
                    pass
                
                return
            
            print(f"  {Fore.YELLOW}⚠️ Сохранённая сессия не сработала{Style.RESET_ALL}")
            
            # ─────────────────────────────────────────────────────
            # ВХОД ЧЕРЕЗ SMS
            # ─────────────────────────────────────────────────────
            
            print(f"  {Fore.CYAN}📱 Вход через SMS для {phone}...{Style.RESET_ALL}")
            await self.action_logger.log_info(acc_id, f"Вход через SMS на {phone}")
            
            is_logged = await login_with_sms(
                page,
                acc_id,
                phone,
                self.navigator,
                self.logger,
                self.notifier,
                fp,
            )
            
            if is_logged:
                print(f"  {Fore.GREEN}✅ Авторизирован (SMS){Style.RESET_ALL}")
                await self.action_logger.log_info(acc_id, "✅ Авторизирован (SMS код)")
                
                account.set_authenticated(True)
                self.logger.success(acc_id, "Logged in with SMS")
                
                try:
                    if self.notifier:
                        await self.notifier.notify_login_success(acc_id, phone, "sms")
                except Exception:
                    pass
            else:
                print(f"  {Fore.RED}❌ Авторизация не удалась{Style.RESET_ALL}")
                await self.action_logger.log_error(
                    acc_id,
                    "Авторизация не удалась",
                    severity="HIGH"
                )
                self.logger.error(acc_id, "SMS login failed", severity="HIGH")
                
                try:
                    if self.notifier:
                        await self.notifier.notify_login_failed(acc_id, phone)
                except Exception:
                    pass
        
        except Exception as e:
            print(f"  {Fore.RED}❌ Ошибка при логине: {str(e)[:80]}{Style.RESET_ALL}")
            await self.action_logger.log_error(acc_id, f"Login error: {e}", severity="HIGH")
            self.logger.error(acc_id, f"Login error: {e}", severity="HIGH")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # КОМАНДЫ: ПРОГРЕВ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _warmup_task(self, acc_id: str):
        """
        Фоновая задача прогрева (5 фаз, 85-95 мин)
        
        Процесс:
        1. Проверка аккаунта
        2. Выполнение 5 фаз с логированием
        3. После завершения — автоматический Alive Mode
        """
        
        account = self.accounts[acc_id]
        phone = account.phone
        
        # ───��─────────────────────────────────────────────────
        # ПРОВЕРКИ
        # ─────────────────────────────────────────────────────
        
        if not account.page:
            print(f"  {Fore.YELLOW}⚠️ Браузер не запущен для {acc_id}{Style.RESET_ALL}")
            await self.action_logger.log_warning(acc_id, "Браузер не запущен")
            return
        
        if not account.state.is_authenticated:
            print(f"  {Fore.YELLOW}⚠️ Аккаунт не авторизирован{Style.RESET_ALL}")
            await self.action_logger.log_warning(acc_id, "Аккаунт не авторизирован")
            return
        
        # ─────────────────────────────────────────────────────
        # ИНИЦИАЛИЗАЦИЯ ПРОГРЕВА
        # ─────────────────────────────────────────────────────
        
        self.total_warmups += 1
        self.logger.action(acc_id, "WARMUP", "START", phone=phone)
        
        print(f"\n{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'🔥 ПОЛНЫЙ ПРОГРЕВ АККАУНТА':^90}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'5 ФАЗ, 85-95 МИНУТ':^90}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}\n")
        
        await self.action_logger.log_info(acc_id, "🔥 Начинается полный прогрев (5 фаз)")
        
        try:
            if self.notifier:
                await self.notifier.notify_warmup_start(
                    acc_id,
                    datetime.now()
                )
        except Exception:
            pass
        
        # ─────────────────────────────────────────────────────
        # ЗАПУСК ПРОГРЕВА
        # ─────────────────────────────────────────────────────
        
        success = await self.warmup_engine.run_full_warmup(
            account.page,
            acc_id,
            self.navigator,
            self.night_mode,
            account.fingerprint,
            self.browser_launcher,
        )
        
        # ─────────────────────────────────────────────────────
        # ЛОГИРОВАНИЕ РЕЗУЛЬТАТА
        # ─────────────────────────────────────────────────────
        
        if success:
            account.set_warmed_up(True)
            self.logger.success(acc_id, "WARMUP COMPLETE")
            
            print(f"\n{Fore.GREEN}{'✅✅✅ ПРОГРЕВ 100% УСПЕШНО ЗАВЕРШЁН ✅✅✅':^90}{Style.RESET_ALL}\n")
            
            await self.action_logger.log_info(
                acc_id,
                f"✅ Прогрев завершён за {self.warmup_engine.total_warmup_duration/60:.1f} мин (5/5 фаз)"
            )
            
            try:
                if self.notifier:
                    await self.notifier.notify_warmup_complete(
                        acc_id,
                        5,
                        5,
                        self.warmup_engine.total_warmup_duration / 60
                    )
            except Exception:
                pass
            
            # ─────────────────────────────────────────────────
            # АВТОМАТИЧЕСКИЙ ALIVE MODE
            # ─────────────────────────────────────────────────
            
            print(f"  {Fore.GREEN}🚀 Запускаю Alive Mode в фоне...{Style.RESET_ALL}\n")
            await self.action_logger.log_info(acc_id, "🚀 Запуск Alive Mode")
            
            await self._launch_alive_task(acc_id)
        
        else:
            self.logger.error(acc_id, "WARMUP FAILED", severity="HIGH")
            
            print(f"\n{Fore.YELLOW}{'⚠️ ПРОГРЕВ ЗАВЕРШЁН С ОШИБКАМИ ⚠️':^90}{Style.RESET_ALL}\n")
            
            await self.action_logger.log_warning(
                acc_id,
                f"⚠️ Прогрев завершён с ошибками (не все фазы пройдены)"
            )
            
            try:
                if self.notifier:
                    await self.notifier.notify_warmup_failed(acc_id)
            except Exception:
                pass
    
    async def cmd_warmup(self, acc_id: str):
        """
        Запустить прогрев в фоне
        
        Проверяет:
        - Существует ли аккаунт
        - Не запущен ли уже прогрев для этого аккаунта
        - Браузер запущен и авторизирован
        """
        
        if acc_id not in self.accounts:
            print(f"  {Fore.RED}❌ Аккаунт {acc_id} не найден{Style.RESET_ALL}")
            return
        
        # Проверяем нет ли уже запущенного warmup
        for task_id, task in list(self.running_tasks.items()):
            if acc_id in str(task) and "warmup" in str(task):
                print(f"  {Fore.YELLOW}⚠️ Прогрев уже запущен для {acc_id}{Style.RESET_ALL}")
                return
        
        await self._launch_task(
            f"Warmup {acc_id}",
            self._warmup_task(acc_id)
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # КОМАНДЫ: ALIVE MODE
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _alive_task(self, acc_id: str):
        """
        Фоновая задача Alive Mode
        
        Бот ведёт себя как живой человек:
        - Просматривает карточки
        - Добавляет в избранное
        - Поиск
        - Скролл
        - Случайные паузы
        """
        
        account = self.accounts[acc_id]
        phone = account.phone
        
        if not account.page:
            print(f"  {Fore.YELLOW}⚠️ Браузер не запущен для {acc_id}{Style.RESET_ALL}")
            return
        
        alive_mode = AliveMode(self.logger, self.executor, self.notifier)
        self.alive_modes[acc_id] = alive_mode
        
        self.total_alive_starts += 1
        
        print(f"\n{Fore.GREEN}{'=' * 90}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'🤖 ALIVE MODE — ПОЛНОСТЬЮ АСИНХРОННЫЙ РЕЖИМ':^90}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'Бот просматривает карточки и добавляет в избранное весь день':^90}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'=' * 90}{Style.RESET_ALL}\n")
        
        await self.action_logger.log_alive_mode_start(acc_id, phone)
        
        self.logger.action(acc_id, "ALIVE_MODE", "START", phone=phone)
        
        try:
            if self.notifier:
                await self.notifier.notify_alive_mode_started(acc_id)
        except Exception:
            pass
        
        await alive_mode.run(
            account.page,
            acc_id,
            self.navigator,
            self.night_mode,
            account.fingerprint,
            self.browser_launcher,
        )
    
    async def _launch_alive_task(self, acc_id: str):
        """Запустить Alive Mode в фоне"""
        
        if acc_id not in self.accounts:
            print(f"  {Fore.RED}❌ Аккаунт {acc_id} не найден{Style.RESET_ALL}")
            return
        
        if acc_id in self.alive_modes and self.alive_modes[acc_id].running:
            print(f"  {Fore.YELLOW}⚠️ Alive Mode уже работает для {acc_id}{Style.RESET_ALL}")
            return
        
        await self._launch_task(
            f"Alive {acc_id}",
            self._alive_task(acc_id)
        )
    
    async def cmd_alive(self, acc_id: str):
        """Запустить Alive Mode"""
        await self._launch_alive_task(acc_id)
    
    async def cmd_stop_alive(self, acc_id: str):
        """Остановить Alive Mode"""
        
        if acc_id in self.alive_modes:
            alive_mode = self.alive_modes[acc_id]
            iterations = alive_mode.iteration_count
            
            alive_mode.stop()
            
            print(f"  {Fore.YELLOW}⏹️ Alive Mode остановлен для {acc_id}{Style.RESET_ALL}")
            print(f"     Выполнено итераций: {iterations}")
            
            await self.action_logger.log_alive_mode_stop(acc_id, iterations)
            
            self.logger.action(acc_id, "ALIVE_MODE", "STOP", iterations=iterations)
        else:
            print(f"  {Fore.YELLOW}⚠️ Alive Mode не запущен для {acc_id}{Style.RESET_ALL}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # КОМАНДЫ: УПРАВЛЕНИЕ БРАУЗЕРОМ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def cmd_close(self, acc_id: str):
        """Закрыть браузер (сессия сохранена)"""
        
        await self.cmd_stop_alive(acc_id)
        await self.browser_launcher.close(acc_id)
        self.accounts[acc_id].page = None
        
        print(f"  {Fore.GREEN}✅ Браузер закрыт (сессия сохранена){Style.RESET_ALL}")
        await self.action_logger.log_info(acc_id, "✅ Браузер закрыт")
        self.logger.action(acc_id, "BROWSER", "CLOSE")
    
    async def cmd_reset(self, acc_id: str):
        """Полный сброс аккаунта"""
        
        await self.cmd_stop_alive(acc_id)
        await self.browser_launcher.reset_session(acc_id)
        self.accounts[acc_id].reset()
        self.circuit_breaker.reset(acc_id)
        
        print(f"  {Fore.GREEN}✅ Аккаунт полностью сброшен{Style.RESET_ALL}")
        await self.action_logger.log_info(acc_id, "✅ Полный сброс сессии")
        self.logger.action(acc_id, "RESET", "COMPLETE")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # КОМАНДЫ: СТАТУС И ИНФОРМАЦИЯ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def cmd_status(self, acc_id: str = None):
        """Статус аккаунта или всех"""
        
        if acc_id and acc_id in self.accounts:
            account = self.accounts[acc_id]
            status = account.get_status_report()
            session_status = self.session_monitor.get_session_status(acc_id)
            
            print(f"\n{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}")
            print(f"{Fore.LIGHTYELLOW_EX}📊 СТАТУС: {acc_id} ({account.phone}){Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}\n")
            
            print(f"  {Fore.LIGHTYELLOW_EX}📱 Информация:{Style.RESET_ALL}")
            print(f"     Телефон: {status['phone']}")
            print(f"     Авторизирован: {'✅ Да' if status['is_authenticated'] else '❌ Нет'}")
            print(f"     Прогрет: {'✅ Да' if status['is_warmed_up'] else '❌ Нет'}")
            print(f"     Статус: {status['status'].upper()}")
            
            if session_status:
                print(f"\n  {Fore.LIGHTYELLOW_EX}📊 Статистика:{Style.RESET_ALL}")
                print(f"     Действий выполнено: {session_status['actions_count']}")
                print(f"     Ошибок: {session_status['errors_count']}")
                print(f"     Усталость: {int(session_status['tiredness']*100)}%")
                print(f"     Настроение: {session_status['mood']}")
                print(f"     Время сессии: {int(session_status['elapsed_time'] / 60)} мин")
            
            print(f"\n  {Fore.LIGHTYELLOW_EX}🔄 Задачи:{Style.RESET_ALL}")
            alive_status = '🟢 Активен' if acc_id in self.alive_modes and self.alive_modes[acc_id].running else '⚫ Неактивен'
            print(f"     Alive Mode: {alive_status}")
            
            print(f"{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}\n")
        
        else:
            print(f"\n{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}")
            print(f"{Fore.LIGHTYELLOW_EX}📊 СТАТУС ВСЕХ АККАУНТОВ{Style.RESET_ALL}")
            print(f"{Fore.LIGHTYELLOW_EX}🔄 ФОНОВЫХ ЗАДАЧ: {len(self.running_tasks)}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}\n")
            
            for acc_id, account in self.accounts.items():
                status = account.get_status_report()
                auth = '✅' if status['is_authenticated'] else '❌'
                warm = '✅' if status['is_warmed_up'] else '❌'
                num = acc_id.split('_')[-1]
                alive_status = '🟢' if acc_id in self.alive_modes and self.alive_modes[acc_id].running else '⚫'
                
                session_status = self.session_monitor.get_session_status(acc_id)
                if session_status:
                    actions = session_status['actions_count']
                    errors = session_status['errors_count']
                else:
                    actions = 0
                    errors = 0
                
                print(f"  {num}: {status['phone']} | Auth:{auth} Warm:{warm} Alive:{alive_status}")
                print(f"     Действий: {actions} | Ошибок: {errors}\n")
            
            print(f"{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}")
            print(f"{Fore.LIGHTYELLOW_EX}🔄 ЗАПУЩЕННЫЕ ЗАДАЧИ:{Style.RESET_ALL}\n")
            
            if not self.running_tasks:
                print(f"  (нет активных задач)\n")
            else:
                for i, (task_id, task) in enumerate(self.running_tasks.items(), 1):
                    status_icon = "🔄" if not task.done() else "✅"
                    status_text = "выполняется" if not task.done() else "завершена"
                    print(f"  {i}. {task_id}: {status_icon} {status_text}")
                print()
            
            # Глобальная статистика
            global_stats = self.session_monitor.get_global_stats()
            
            print(f"{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}")
            print(f"{Fore.LIGHTYELLOW_EX}📈 ГЛОБАЛЬНАЯ СТАТИСТИКА:{Style.RESET_ALL}\n")
            print(f"  Total Actions: {global_stats['total_actions']}")
            print(f"  Total Errors: {global_stats['total_errors']}")
            print(f"  Total Accounts: {global_stats['total_accounts']}")
            print(f"  Elapsed: {int(global_stats['elapsed_time'] / 60)} мин\n")
            
            print(f"{Fore.CYAN}{'─' * 90}{Style.RESET_ALL}\n")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # КОМАНДЫ: НОЧНОЙ РЕЖИМ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def cmd_night_override(self, acc_id: str, hours: float):
        """Отключить ночной режим на N часов"""
        
        self.night_mode.override(acc_id, hours)
        print(f"  {Fore.GREEN}✅ Ночь отключена на {hours} часов для {acc_id}{Style.RESET_ALL}")
        self.logger.action(acc_id, "NIGHT_MODE", "OVERRIDE", hours=hours)
    
    def cmd_night_reset(self, acc_id: str):
        """Вернуть ночной режим"""
        
        self.night_mode.reset_override(acc_id)
        print(f"  {Fore.GREEN}✅ Ночной режим восстановлен{Style.RESET_ALL}")
        self.logger.action(acc_id, "NIGHT_MODE", "RESET")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # КОМАНДЫ: ПРОКСИ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def cmd_proxy_check(self):
        """Проверить прокси"""
        
        print(f"\n{Fore.CYAN}🌐 Проверяю прокси...{Style.RESET_ALL}\n")
        
        results = await check_all_proxies(self.proxy_manager, self.logger)
        
        print(f"\n{Fore.GREEN}✅ Результаты:{Style.RESET_ALL}\n")
        
        for proxy_id, result in results.items():
            status = f"{Fore.GREEN}✅{Style.RESET_ALL}" if result["ok"] else f"{Fore.RED}❌{Style.RESET_ALL}"
            ip = result.get('ip', 'unknown')
            country = result.get('country', 'unknown')
            latency = result.get('latency', 0)
            
            print(f"  {status} {proxy_id}")
            print(f"     IP: {ip} | Country: {country} | Latency: {latency:.0f}ms\n")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # СПРАВКА
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def print_help(self):
        """Справка по командам"""
        
        print(f"""
{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}
{Fore.LIGHTYELLOW_EX}{'КОМАНДЫ AVITO BOT PRO 2030':^90}{Style.RESET_ALL}
{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}

{Fore.GREEN}📱 ЛОГИН:{Style.RESET_ALL}
  {Fore.YELLOW}1 login{Style.RESET_ALL}              - Логин аккаунта 1
  {Fore.YELLOW}2 login{Style.RESET_ALL}              - Логин аккаунта 2
  {Fore.YELLOW}3 login{Style.RESET_ALL}              - Логин аккаунта 3

{Fore.GREEN}🔥 ПРОГРЕВ (в фоне):{Style.RESET_ALL}
  {Fore.YELLOW}1 warmup{Style.RESET_ALL}             - Запустить прогрев (5 фаз, 85-95 мин)
  {Fore.YELLOW}2 warmup{Style.RESET_ALL}             - Запустить прогрев для 2-го аккаунта
  {Fore.YELLOW}3 warmup{Style.RESET_ALL}             - Запустить прогрев для 3-го аккаунта

{Fore.GREEN}🤖 ALIVE MODE (в фоне):{Style.RESET_ALL}
  {Fore.YELLOW}1 alive{Style.RESET_ALL}              - Запустить Alive Mode (бот весь день)
  {Fore.YELLOW}1 stop{Style.RESET_ALL}               - Остановить Alive Mode
  {Fore.YELLOW}2 alive{Style.RESET_ALL}              - Alive Mode для 2-го аккаунта
  {Fore.YELLOW}2 stop{Style.RESET_ALL}               - Остановить Alive Mode 2-го

{Fore.GREEN}🌐 УПРАВЛЕНИЕ БРАУЗЕРОМ:{Style.RESET_ALL}
  {Fore.YELLOW}1 close{Style.RESET_ALL}              - Закрыть браузер (сессия сохранена)
  {Fore.YELLOW}1 reset{Style.RESET_ALL}              - Полный сброс аккаунта

{Fore.GREEN}🌙 НОЧНОЙ РЕЖИМ:{Style.RESET_ALL}
  {Fore.YELLOW}1 night 1{Style.RESET_ALL}            - Отключить ночь на 1 час для 1-го
  {Fore.YELLOW}1 night 2{Style.RESET_ALL}            - Отключить ночь на 2 часа
  {Fore.YELLOW}1 night_reset{Style.RESET_ALL}        - Вернуть ночной режим

{Fore.GREEN}📊 СТАТУС И ИНФОРМАЦИЯ:{Style.RESET_ALL}
  {Fore.YELLOW}1 status{Style.RESET_ALL}             - Статус аккаунта 1
  {Fore.YELLOW}status{Style.RESET_ALL}               - Статус ВСЕХ аккаунтов + статистика
  {Fore.YELLOW}proxy_check{Style.RESET_ALL}          - Проверить прокси

{Fore.GREEN}🔧 ДРУГОЕ:{Style.RESET_ALL}
  {Fore.YELLOW}help{Style.RESET_ALL}                 - Эта справка
  {Fore.YELLOW}exit{Style.RESET_ALL}                 - Выход и корректное завершение

{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}
{Fore.LIGHTGREEN_EX}💡 ВАЖНО: Все операции (warmup, alive mode) запускаются в ФОНЕ!{Style.RESET_ALL}
{Fore.LIGHTGREEN_EX}💡 CLI ВСЕГДА ОТЗЫВЧИВ — можешь запустить несколько аккаунтов одновременно!{Style.RESET_ALL}
{Fore.LIGHTGREEN_EX}💡 Все действия логируются в терминал и отправляются в Telegram!{Style.RESET_ALL}
{Fore.CYAN}{'=' * 90}{Style.RESET_ALL}
""")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # КОМАНДНЫЙ ЦИКЛ (АСИНХРОННЫЙ)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _read_input(self) -> Optional[str]:
        """Неблокирующее чтение ввода пользователя"""
        
        loop = asyncio.get_event_loop()
        
        try:
            cmd = await loop.run_in_executor(
                None,
                lambda: input(f"\n{Fore.CYAN}>>> {Style.RESET_ALL}").strip()
            )
            return cmd
        except EOFError:
            return "exit"
        except asyncio.CancelledError:
            return "exit"
        except Exception:
            return None
    
    async def run_command_loop(self):
        """
        Главный командный цикл (ПОЛНОСТЬЮ АСИНХРОННЫЙ)
        
        Позволяет:
        - Вводить команды в любой момент
        - Запускать несколько фоновых задач одновременно
        - Видеть статус задач и аккаунтов в реальном времени
        - Полностью контролировать все аккаунты
        """
        
        self.print_help()
        
        while not self.shutdown_event.is_set():
            try:
                # ─────────────────────────────────────────────────
                # НЕБЛОКИРУЮЩЕЕ ЧТЕНИЕ ВВОДА
                # ─────────────────────────────────────────────────
                
                cmd = await self._read_input()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                
                # ─────────────────────────────────────────────────
                # СПРАВК��
                # ─────────────────────────────────────────────────
                
                if cmd.lower() == "help":
                    self.print_help()
                
                # ─────────────────────────────────────────────────
                # ВЫХОД
                # ─────────────────────────────────────────────────
                
                elif cmd.lower() == "exit":
                    print(f"\n{Fore.YELLOW}🛑 Выход...{Style.RESET_ALL}")
                    self.shutdown_event.set()
                    break
                
                # ─────────────────────────────────────────────────
                # СТАТУС ВСЕХ
                # ─────────────────────────────────────────────────
                
                elif cmd.lower() == "status":
                    await self.cmd_status()
                
                # ─────────────────────────────────────────────────
                # ПРОВЕРКА ПРОКСИ
                # ─────────────────────────────────────────────────
                
                elif cmd.lower() == "proxy_check":
                    await self.cmd_proxy_check()
                
                # ─────────────────────────────────────────────────
                # КОМАНДЫ ПО АККАУНТАМ
                # ──────────────���──────────────────────────────────
                
                elif len(parts) >= 2:
                    num = parts[0]
                    action = parts[1].lower()
                    
                    acc_id = self.get_account_id(num)
                    
                    if action == "login":
                        await self.cmd_login(acc_id)
                    
                    elif action == "warmup":
                        await self.cmd_warmup(acc_id)
                    
                    elif action == "alive":
                        await self.cmd_alive(acc_id)
                    
                    elif action == "stop":
                        await self.cmd_stop_alive(acc_id)
                    
                    elif action == "close":
                        await self.cmd_close(acc_id)
                    
                    elif action == "reset":
                        await self.cmd_reset(acc_id)
                    
                    elif action == "status":
                        await self.cmd_status(acc_id)
                    
                    elif action == "night":
                        if len(parts) >= 3:
                            try:
                                hours = float(parts[2])
                                self.cmd_night_override(acc_id, hours)
                            except ValueError:
                                print(f"  {Fore.RED}❌ Неверный формат часов{Style.RESET_ALL}")
                        else:
                            print(f"  {Fore.RED}❌ Используйте: {num} night <часы>{Style.RESET_ALL}")
                    
                    elif action == "night_reset":
                        self.cmd_night_reset(acc_id)
                    
                    else:
                        print(f"  {Fore.RED}❌ Неизвестная команда: {action}{Style.RESET_ALL}")
                
                else:
                    if cmd:
                        print(f"  {Fore.RED}❌ Неизвестная команда{Style.RESET_ALL}")
                    print(f"  {Fore.CYAN}Введите 'help' для справки{Style.RESET_ALL}")
            
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}🛑 Выход...{Style.RESET_ALL}")
                self.shutdown_event.set()
                break
            
            except Exception as e:
                print(f"  {Fore.RED}❌ Ошибка: {e}{Style.RESET_ALL}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ЗАВЕРШЕНИЕ РАБОТЫ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def shutdown(self):
        """
        Корректное завершение работы бота
        
        Процесс:
        1. Останавливаем все Alive Modes
        2. Отменяем все фоновые задачи
        3. Закрываем все браузеры
        4. Отправляем финальное уведомление
        """
        
        print(f"\n{Fore.YELLOW}🛑 Завершаю работу...{Style.RESET_ALL}\n")
        
        # ─────────────────────────────────────────────────────
        # ОСТАНАВЛИВАЕМ ALIVE MODES
        # ─────────────────────────────────────────────────────
        
        print(f"  {Fore.CYAN}🤖 Останавливаю Alive Mode...{Style.RESET_ALL}")
        for acc_id in list(self.alive_modes.keys()):
            try:
                self.alive_modes[acc_id].stop()
            except Exception:
                pass
        
        # ─────────────────────────────────────────────────────
        # ОТМЕНЯЕМ ФОНОВЫЕ ЗАДАЧИ
        # ─────────────────────────────────────────────────────
        
        if self.running_tasks:
            print(f"  {Fore.CYAN}⏳ Отменяю {len(self.running_tasks)} фоновых задач...{Style.RESET_ALL}")
            for task_id, task in list(self.running_tasks.items()):
                try:
                    task.cancel()
                except Exception:
                    pass
            
            # Ждём завершения всех задач
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        # ─────────────────────────────────────────────────────
        # ЗАКРЫВАЕМ БРАУЗЕРЫ
        # ─────────────────────────────────────────────────────
        
        print(f"  {Fore.CYAN}🌐 Закрываю браузеры...{Style.RESET_ALL}")
        await self.browser_launcher.close_all()
        
        # ─────────────────────────────────────────────────────
        # ФИНАЛЬНОЕ УВЕДОМЛЕНИЕ
        # ─────────────────────────────────────────────────────
        
        try:
            if self.notifier:
                runtime = (datetime.now() - self.bot_start_time).total_seconds() / 3600
                await self.notifier.notify_bot_stopped(
                    self.total_logins,
                    self.total_warmups,
                    self.total_alive_starts,
                    runtime
                )
        except Exception:
            pass
        
        print(f"{Fore.GREEN}✅ Завершено{Style.RESET_ALL}\n")
        
        self.logger.system("Bot shutdown complete")


# ════════════════════════════════════════════════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ════════════════════════════════════════════════════════════════════════════════════

async def main():
    """Главная функция бота"""
    
    bot = AvitoBot()
    
    try:
        await bot.initialize()
        await bot.run_command_loop()
    finally:
        await bot.shutdown()


# ════════════════════════════════════════════════════════════════════════════════════
# ТОЧКА ВХОДА
# ════════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)