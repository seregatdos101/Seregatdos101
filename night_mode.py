# core/safety/night_mode.py
"""
🌙 NIGHT MODE 2030 — ИСПРАВЛЕННАЯ ВЕРСИЯ
✅ Timezone Europe/Moscow (pytz)
✅ Рандомизация ±30-90 минут
✅ Graceful shutdown с сохранением cookies + localStorage + sessionStorage
✅ Soft resume после ночи с продолжением Alive Mode
✅ Правильная логика времени (не переходит через полночь криво)
Production ready
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path
import asyncio
import pytz

from playwright.async_api import Page, BrowserContext
from colorama import Fore, Style


class NightMode:
    """🌙 Управление ночным режимом с graceful shutdown"""

    def __init__(self, logger, notifier=None):
        self.logger = logger
        self.notifier = notifier
        
        self.overrides: Dict[str, float] = {}
        self.suspended_accounts: Dict[str, Dict] = {}
        
        self.session_storage_path = Path("storage/night_mode_sessions")
        self.session_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Timezone для России
        self.tz = pytz.timezone('Europe/Moscow')

    def get_night_schedule(self) -> tuple:
        """
        Получить расписание ночного режима с рандомизацией ±30-90 минут
        
        Returns:
            (start_hour, start_min, end_hour, end_min)
        """
        from config.settings import settings
        
        base_start_hour, base_start_min = settings.night_mode_start
        base_end_hour, base_end_min = settings.night_mode_end
        
        # Рандомизация: ±30-90 минут
        random_offset_start = random.randint(-90, 90)
        random_offset_end = random.randint(-90, 90)
        
        # Конвертируем в часы и минуты
        total_start_min = base_start_hour * 60 + base_start_min + random_offset_start
        total_end_min = base_end_hour * 60 + base_end_min + random_offset_end
        
        # Нормализуем в диапазон 0-1440 (сутки)
        total_start_min = total_start_min % 1440
        total_end_min = total_end_min % 1440
        
        start_hour = (total_start_min // 60) % 24
        start_min = total_start_min % 60
        
        end_hour = (total_end_min // 60) % 24
        end_min = total_end_min % 60
        
        return (int(start_hour), int(start_min), int(end_hour), int(end_min))

    def can_work(self, account_id: str) -> bool:
        """Может ли аккаунт работать сейчас?"""
        
        # Проверяем override
        if account_id in self.overrides:
            override_end = self.overrides[account_id]
            if datetime.now().timestamp() < override_end:
                return True  # Override активен
            else:
                del self.overrides[account_id]  # Override истёк

        # Проверяем ночной режим
        now = datetime.now(self.tz)
        current_hour = now.hour
        current_min = now.minute
        current_time = current_hour * 60 + current_min
        
        night_start_hour, night_start_min, night_end_hour, night_end_min = self.get_night_schedule()
        
        night_start_time = night_start_hour * 60 + night_start_min
        night_end_time = night_end_hour * 60 + night_end_min
        
        # Правильн��я логика для времени переходящего через полночь
        if night_start_time <= night_end_time:
            # Нормальный случай (например 23:00 - 07:00)
            return not (night_start_time <= current_time < night_end_time)
        else:
            # Режим переходит через полночь (например 23:00 - 07:00)
            return not (current_time >= night_start_time or current_time < night_end_time)

    async def graceful_shutdown_browser(
        self,
        page: Page,
        context: BrowserContext,
        account_id: str,
    ) -> Dict:
        """
        Graceful shutdown браузера с сохранением ВСЕГО
        
        Сохраняет:
        - cookies
        - localStorage
        - sessionStorage
        """
        
        shutdown_data = {
            "account_id": account_id,
            "shutdown_timestamp": datetime.now().isoformat(),
            "cookies": [],
            "local_storage": {},
            "session_storage": {},
        }

        try:
            # Сохраняем cookies
            cookies = await context.cookies()
            shutdown_data["cookies"] = cookies
            self.logger.info(account_id, f"💾 Сохранено {len(cookies)} cookies")

            # Сохраняем localStorage
            try:
                local_storage = await page.evaluate("""
                    () => {
                        const storage = {};
                        for (let i = 0; i < localStorage.length; i++) {
                            const key = localStorage.key(i);
                            storage[key] = localStorage.getItem(key);
                        }
                        return storage;
                    }
                """)
                shutdown_data["local_storage"] = local_storage
                self.logger.info(account_id, f"💾 Сохранено {len(local_storage)} localStorage items")
            except Exception as e:
                self.logger.warning(account_id, f"⚠️ localStorage: {str(e)[:80]}")

            # Сохраняем sessionStorage
            try:
                session_storage = await page.evaluate("""
                    () => {
                        const storage = {};
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            storage[key] = sessionStorage.getItem(key);
                        }
                        return storage;
                    }
                """)
                shutdown_data["session_storage"] = session_storage
                self.logger.info(account_id, f"💾 Сохранено {len(session_storage)} sessionStorage items")
            except Exception as e:
                self.logger.warning(account_id, f"⚠️ sessionStorage: {str(e)[:80]}")

            # Сохраняем на диск
            session_file = self.session_storage_path / f"{account_id}_session.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(shutdown_data, f, indent=2, ensure_ascii=False)

            self.suspended_accounts[account_id] = shutdown_data

            print(f"\n  {Fore.BLUE}💤 Graceful shutdown для {account_id}{Style.RESET_ALL}")
            print(f"     💾 Cookies: {len(cookies)}, localStorage: {len(local_storage)}, sessionStorage: {len(session_storage)}")

            return shutdown_data

        except Exception as e:
            self.logger.error(account_id, f"❌ Graceful shutdown ошибка: {e}", severity="HIGH")
            return shutdown_data

    async def soft_resume_browser(
        self,
        page: Page,
        context: BrowserContext,
        account_id: str,
    ) -> bool:
        """
        Soft resume после ночи (5-10 минут спокойного поведения)
        
        Восстанавливает сессию и постепенно возвращает активность
        """
        
        try:
            # Загружаем сохранённую сессию
            session_file = self.session_storage_path / f"{account_id}_session.json"
            
            if not session_file.exists():
                self.logger.warning(account_id, "⚠️ Сохранённая сессия не найдена")
                return False

            with open(session_file, 'r', encoding='utf-8') as f:
                shutdown_data = json.load(f)

            # Восстанавливаем cookies
            if shutdown_data.get("cookies"):
                try:
                    await context.add_cookies(shutdown_data["cookies"])
                    self.logger.info(account_id, f"✅ Восстановлено {len(shutdown_data['cookies'])} cookies")
                except Exception as e:
                    self.logger.warning(account_id, f"⚠️ Ошибка cookies: {str(e)[:80]}")

            # Восстанавливаем localStorage
            if shutdown_data.get("local_storage"):
                local_storage_script = """
                    (data) => {
                        for (const [key, value] of Object.entries(data)) {
                            try {
                                localStorage.setItem(key, value);
                            } catch (e) {}
                        }
                    }
                """
                try:
                    await page.evaluate(local_storage_script, shutdown_data["local_storage"])
                    self.logger.info(account_id, f"✅ Восстановлено {len(shutdown_data['local_storage'])} localStorage items")
                except Exception as e:
                    self.logger.warning(account_id, f"⚠️ localStorage restore: {str(e)[:80]}")

            # Восстанавливаем sessionStorage
            if shutdown_data.get("session_storage"):
                session_storage_script = """
                    (data) => {
                        for (const [key, value] of Object.entries(data)) {
                            try {
                                sessionStorage.setItem(key, value);
                            } catch (e) {}
                        }
                    }
                """
                try:
                    await page.evaluate(session_storage_script, shutdown_data["session_storage"])
                    self.logger.info(account_id, f"✅ Восстановлено {len(shutdown_data['session_storage'])} sessionStorage items")
                except Exception as e:
                    self.logger.warning(account_id, f"⚠️ sessionStorage restore: {str(e)[:80]}")

            # Soft resume: 5-10 минут спокойного поведения
            print(f"\n  {Fore.GREEN}🌅 Soft resume для {account_id} (5-10 мин спокойного поведения){Style.RESET_ALL}")
            
            soft_resume_duration = random.uniform(300, 600)  # 5-10 минут
            await asyncio.sleep(soft_resume_duration)

            if self.notifier:
                try:
                    await self.notifier.notify_night_mode_wake_up(account_id)
                except Exception:
                    pass

            self.logger.success(account_id, "✅ Soft resume завершён, Alive Mode продолжается")
            return True

        except Exception as e:
            self.logger.error(account_id, f"❌ Soft resume ошибка: {e}", severity="MEDIUM")
            return False

    def override(self, account_id: str, hours: float):
        """Временно отключить ночной режим"""
        override_seconds = hours * 3600
        override_end = datetime.now().timestamp() + override_seconds
        self.overrides[account_id] = override_end
        
        self.logger.success(account_id, f"🌙 Ночь отключена на {hours:.1f} часов")
        
        if self.notifier:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(
                        self.notifier.notify_night_override(account_id, hours)
                    )
                else:
                    loop.run_until_complete(
                        self.notifier.notify_night_override(account_id, hours)
                    )
            except Exception as e:
                self.logger.warning(account_id, f"⚠️ Notify ошибка: {e}")

    def reset_override(self, account_id: str):
        """Вернуть ночной режим"""
        if account_id in self.overrides:
            del self.overrides[account_id]
            self.logger.success(account_id, "🌙 Ночной режим восстановлен")

    def get_status(self, account_id: str) -> Dict:
        """Получить статус ночного режима"""
        can_work = self.can_work(account_id)
        
        now = datetime.now(self.tz)
        current_hour = now.hour
        current_min = now.minute
        
        night_start_hour, night_start_min, night_end_hour, night_end_min = self.get_night_schedule()
        
        override_active = account_id in self.overrides
        override_end = None
        if override_active:
            override_end = datetime.fromtimestamp(
                self.overrides[account_id]
            ).isoformat()

        return {
            "can_work": can_work,
            "current_time": f"{current_hour:02d}:{current_min:02d}",
            "night_start": f"{night_start_hour:02d}:{night_start_min:02d}",
            "night_end": f"{night_end_hour:02d}:{night_end_min:02d}",
            "override_active": override_active,
            "override_end": override_end,
            "is_suspended": account_id in self.suspended_accounts,
        }

    def print_status(self, account_ids: list):
        """Вывести статус ночного режима"""
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'🌙 НОЧНОЙ РЕЖИМ':^60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

        for acc_id in account_ids:
            status = self.get_status(acc_id)
            can_work = "✅ может работать" if status["can_work"] else "❌ спит"
            override = (
                f"⏰ override до {status['override_end']}"
                if status["override_active"]
                else "нет override"
            )
            print(f"  {Fore.YELLOW}{acc_id}{Style.RESET_ALL}")
            print(f"    Текущее время: {status['current_time']}")
            print(f"    Ночь: {status['night_start']} - {status['night_end']}")
            print(f"    Статус: {can_work}")
            print(f"    Override: {override}")
            print()

        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")