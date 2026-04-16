# core/browser/launcher.py
"""
🌐 BROWSER LAUNCHER 2030 — стабильный запуск браузера с восстановлением сессий

Что делает этот модуль:
- Инициализирует Playwright и Chromium
- Создаёт контекст браузера для конкретного аккаунта
- **ПРАВИЛЬНО** восстанавливает cookies ДО создания контекста
- Восстанавливает localStorage через storage_state
- Восстанавливает sessionStorage отдельно
- Поддерживает прокси
- Позволяет безопасно закрывать и сбрасывать сессию
- Даёт диагностическое логирование по загрузке страницы

ВАЖНО! ГЛАВНОЕ УЛУЧШЕНИЕ:
- Cookies загружаются ПОСЛЕ создания контекста, но ДО первой загрузки
- Добавлена повторная попытка загрузки cookies если нужно
- Улучшена совместимость с разными форматами cookies
- Добавлено восстановление cookies из account_X.json если они есть
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from colorama import Fore, Style

from core.browser.fingerprint import Fingerprint, FingerprintStore
from core.browser.stealth import build_stealth_script
from config.settings import settings


class BrowserLauncher:
    """
    Запуск браузера и управление сессиями аккаунтов.
    """

    def __init__(self, logger, proxy_manager):
        self.logger = logger
        self.proxy_manager = proxy_manager

        self._pw: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}

        self.fingerprint_store = FingerprintStore()

        self.sessions_dir = Path("storage/sessions")
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self.cookies_dir = self.sessions_dir / "cookies"
        self.cookies_dir.mkdir(parents=True, exist_ok=True)

        self.storage_state_dir = self.sessions_dir / "storage_state"
        self.storage_state_dir.mkdir(parents=True, exist_ok=True)

        self.session_storage_dir = self.sessions_dir / "session_storage"
        self.session_storage_dir.mkdir(parents=True, exist_ok=True)

        self.total_launched = 0
        self.total_closed = 0
        self.total_errors = 0

    # ════════════════════════════════════════════════════════════════
    # ИНИЦИАЛИЗАЦИЯ
    # ════════════════════════════════════════════════════════════════

    async def initialize(self) -> None:
        """Инициализация Playwright и Chromium."""
        if self._browser is not None:
            return

        try:
            self.logger.system("Запускаю Playwright...")
            self._pw = await async_playwright().start()

            args = [
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
            ]

            self.logger.system(f"Запускаю Chromium (headless={settings.headless})...")

            self._browser = await self._pw.chromium.launch(
                headless=settings.headless,
                args=args,
                timeout=30000,
            )

            self.logger.system("✅ Playwright и Chromium инициализированы")

        except Exception as e:
            self.total_errors += 1
            self.logger.error(
                "launcher",
                f"❌ Не удалось инициализировать браузер: {str(e)[:150]}",
                severity="CRITICAL",
            )
            raise

    # ════════════════════════════════════════════════════════════════
    # ВОССТАНОВЛЕНИЕ COOKIES (ГЛАВНАЯ ФИКСАЦИЯ)
    # ════════════════════════════════════════════════════════════════

    def _get_all_available_cookies(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Получает cookies из ВСЕХ доступных источников:
        1. Из storage_state (приоритет)
        2. Из файла cookies
        3. Из account_X.json в storage/
        4. Комбинирует их в правильный формат
        """
        all_cookies: Dict[str, Dict[str, Any]] = {}

        # ─────────────────────────────────────────────────────────
        # 1. COOKIES ИЗ storage_state (высший приоритет)
        # ─────────────────────────────────────────────────────────

        storage_state_path = self._get_storage_state_path(account_id)
        if storage_state_path.exists():
            try:
                with open(storage_state_path, "r", encoding="utf-8") as f:
                    storage_data = json.load(f)

                if isinstance(storage_data, dict) and "cookies" in storage_data:
                    cookies_from_storage = storage_data["cookies"]
                    if isinstance(cookies_from_storage, list):
                        for cookie in cookies_from_storage:
                            if isinstance(cookie, dict) and "name" in cookie:
                                all_cookies[cookie["name"]] = cookie
                        self.logger.info(
                            account_id,
                            f"✅ Загружено {len(cookies_from_storage)} cookies из storage_state"
                        )
            except Exception as e:
                self.logger.warning(
                    account_id,
                    f"⚠️ Ошибка чтения cookies из storage_state: {str(e)[:120]}"
                )

        # ─────────────────────────────────────────────────────────
        # 2. COOKIES ИЗ ФАЙЛА cookies.json
        # ─────────────────────────────────────────────────────────

        cookies_file = self._get_cookies_path(account_id)
        if cookies_file.exists():
            try:
                with open(cookies_file, "r", encoding="utf-8") as f:
                    cookies_data = json.load(f)

                if isinstance(cookies_data, list):
                    for cookie in cookies_data:
                        if isinstance(cookie, dict) and "name" in cookie:
                            all_cookies[cookie["name"]] = cookie
                    self.logger.info(
                        account_id,
                        f"✅ Загружено {len(cookies_data)} cookies из файла"
                    )
            except Exception as e:
                self.logger.warning(
                    account_id,
                    f"⚠️ Ошибка чтения cookies из файла: {str(e)[:120]}"
                )

        # ─────────────────────────────────────────────────────────
        # 3. COOKIES ИЗ account_X.json в storage/
        # ─────────────────────────────────────────────────────────

        account_json_path = Path("storage") / f"{account_id}.json"
        if account_json_path.exists():
            try:
                with open(account_json_path, "r", encoding="utf-8") as f:
                    account_data = json.load(f)

                if isinstance(account_data, list):
                    for cookie in account_data:
                        if isinstance(cookie, dict) and "name" in cookie:
                            all_cookies[cookie["name"]] = cookie
                    self.logger.info(
                        account_id,
                        f"✅ Загружено {len(account_data)} cookies из {account_json_path}"
                    )
            except Exception as e:
                self.logger.warning(
                    account_id,
                    f"⚠️ Ошибка чтения cookies из {account_json_path}: {str(e)[:120]}"
                )

        # ─────────────────────────────────────────────────────────
        # 4. ДЕДУПЛИКАЦИЯ И ВОЗВРАТ
        # ─────────────────────────────────────────────────────────

        result_cookies = list(all_cookies.values())
        if result_cookies:
            self.logger.info(
                account_id,
                f"🎯 ИТОГО ЗАГРУЖЕНО COOKIES: {len(result_cookies)} штук"
            )

        return result_cookies

    async def _apply_cookies_to_context(
        self,
        context: BrowserContext,
        page: Page,
        account_id: str,
        cookies: List[Dict[str, Any]],
    ) -> bool:
        """
        Применяет cookies к контексту и странице с валидацией
        """
        if not cookies:
            self.logger.warning(account_id, "⚠️ Нет cookies для применения")
            return False

        # ─────────────────────────────────────────────────────────
        # ФИЛЬТРУЕМ COOKIES (удаляем невалидные)
        # ─────────────────────────────────────────────────────────

        valid_cookies = []
        for cookie in cookies:
            try:
                if not isinstance(cookie, dict):
                    continue

                # Обязательные поля
                if "name" not in cookie or "value" not in cookie:
                    continue

                # Очищаем от лишних полей
                clean_cookie = {
                    "name": str(cookie["name"]),
                    "value": str(cookie["value"]),
                    "domain": str(cookie.get("domain", ".avito.ru")),
                    "path": str(cookie.get("path", "/")),
                }

                # Опциональные поля
                if "expires" in cookie:
                    try:
                        clean_cookie["expires"] = float(cookie["expires"])
                    except:
                        pass

                if "httpOnly" in cookie:
                    clean_cookie["httpOnly"] = bool(cookie.get("httpOnly", False))

                if "secure" in cookie:
                    clean_cookie["secure"] = bool(cookie.get("secure", False))

                if "sameSite" in cookie:
                    same_site = str(cookie.get("sameSite", "Lax")).lower()
                    if same_site in {"strict", "lax", "none"}:
                        clean_cookie["sameSite"] = same_site

                valid_cookies.append(clean_cookie)

            except Exception as e:
                self.logger.warning(
                    account_id,
                    f"⚠️ Ошибка валидации cookie {cookie.get('name', 'unknown')}: {str(e)[:100]}"
                )
                continue

        if not valid_cookies:
            self.logger.warning(account_id, "❌ После валидации cookies не осталось")
            return False

        # ─────────────────────────────────────────────────────────
        # ПРИМЕНЯЕМ COOKIES К КОНТЕКСТУ
        # ─────────────────────────────────────────────────────────

        try:
            await context.add_cookies(valid_cookies)
            self.logger.action(
                account_id,
                "APPLY_COOKIES",
                "SUCCESS",
                count=len(valid_cookies)
            )
            self.logger.info(
                account_id,
                f"✅ Применено {len(valid_cookies)} cookies к контексту"
            )
            return True

        except Exception as e:
            self.logger.error(
                account_id,
                f"❌ Ошибка применения cookies: {str(e)[:150]}",
                severity="MEDIUM"
            )
            return False

    # ════════════════════════════════════════════════════════════════
    # ОСНОВНОЙ ЗАПУСК
    # ══════════════════════════════════════��═════════════════════════

    async def launch(self, account_id: str) -> Optional[Page]:
        """
        Запускает браузер для аккаунта и восстанавливает сессию.

        Порядок:
        1. Инициализация браузера
        2. Проверка существующей страницы
        3. Получение fingerprint
        4. Создание контекста с storage_state если он есть
        5. Создание страницы
        6. Подключение init script (stealth)
        7. **ЗАГРУЗКА И ПРИМЕНЕНИЕ COOKIES** (ГЛАВНОЕ!)
        8. Переход на домен
        9. Восстановление sessionStorage
        10. Повторная загрузка страницы
        11. Установка заголовка окна
        """

        if not self._browser:
            await self.initialize()

        existing_page = self._pages.get(account_id)
        if existing_page:
            try:
                if not existing_page.is_closed():
                    self.logger.info(account_id, "✅ Использую уже существующую страницу")
                    return existing_page
            except Exception:
                pass

        fp = self.fingerprint_store.get_or_create(account_id)

        account_num = account_id.split("_")[-1]
        account_config = settings.accounts.get(account_id, {})
        phone = account_config.get("phone", "unknown")

        self.logger.info(account_id, "📋 Получаю fingerprint и параметры аккаунта...")
        self.logger.info(account_id, f"📱 Телефон: {phone}")

        proxy_cfg = self.proxy_manager.get_playwright_proxy(account_id)
        proxy_address = self.proxy_manager.get_proxy_address(account_id)

        if proxy_address:
            self.logger.info(account_id, f"🪜 Прокси: {proxy_address}")

        context_kwargs: Dict[str, Any] = {
            "viewport": {"width": 1366, "height": 768},
            "locale": "ru-RU",
            "timezone_id": fp.timezone,
            "user_agent": fp.user_agent,
            "ignore_https_errors": True,
            "permissions": [],
            "extra_http_headers": {
                "Accept-Language": "ru-RU,ru;q=0.9",
                "DNT": "1",
            },
        }

        if proxy_cfg:
            context_kwargs["proxy"] = proxy_cfg

        # ─────────────────────────────────────────────────────────
        # ДОБАВЛЯЕМ storage_state если он есть
        # ─────────────────────────────────────────────────────────

        storage_state_path = self._get_storage_state_path(account_id)
        if storage_state_path.exists():
            context_kwargs["storage_state"] = str(storage_state_path)
            self.logger.info(account_id, "✅ Найден storage_state, подключаю при создании контекста")

        context = None
        page = None

        for attempt in range(1, 4):
            try:
                self.logger.info(account_id, f"🔧 [Попытка {attempt}/3] Создаю контекст...")

                context = await asyncio.wait_for(
                    self._browser.new_context(**context_kwargs),
                    timeout=35,
                )

                try:
                    stealth_script = build_stealth_script(fp)
                    await context.add_init_script(stealth_script)
                    self.logger.info(account_id, "✅ Init script (stealth) подключён")
                except Exception as e:
                    self.logger.warning(
                        account_id,
                        f"⚠️ Не удалось подключить init script: {str(e)[:120]}"
                    )

                page = await context.new_page()
                self._attach_page_diagnostics(page, account_id)

                self.logger.success(
                    account_id,
                    f"✅ Контекст и страница созданы (попытка {attempt})"
                )
                break

            except asyncio.TimeoutError:
                self.logger.warning(
                    account_id,
                    f"⏱️ Timeout при создании контекста (попытка {attempt}/3)"
                )
                if attempt < 3:
                    await asyncio.sleep(2)
                else:
                    self.total_errors += 1
                    self.logger.error(
                        account_id,
                        "❌ Не удалось создать контекст после 3 попыток",
                        severity="HIGH"
                    )
                    return None

            except Exception as e:
                error_str = str(e).lower()

                if "proxy" in error_str or "err_proxy" in error_str:
                    self.total_errors += 1
                    self.logger.error(
                        account_id,
                        "❌ Проблема с прокси при создании контекста",
                        severity="HIGH"
                    )
                    return None

                self.logger.warning(
                    account_id,
                    f"⚠️ Ошибка создания контекста: {str(e)[:150]}"
                )
                if attempt < 3:
                    await asyncio.sleep(2)
                else:
                    self.total_errors += 1
                    self.logger.error(
                        account_id,
                        "❌ Контекст не создан",
                        severity="HIGH"
                    )
                    return None

        if not context or not page:
            return None

        # ═════════════════════════════════════════════════════════
        # 🎯 ГЛАВНАЯ ЧАСТЬ: ПРИМЕНЕНИЕ COOKIES
        # ═════════════════════════════════════════════════════════

        self.logger.info(account_id, "🍪 Восстанавливаю cookies из всех источников...")

        all_cookies = self._get_all_available_cookies(account_id)

        if all_cookies:
            cookies_applied = await self._apply_cookies_to_context(
                context,
                page,
                account_id,
                all_cookies
            )
        else:
            cookies_applied = False
            self.logger.warning(account_id, "⚠️ Cookies не найдены в файлах")

        # ═════════════════════════════════════════════════════════

        # Сначала идём на домен, потом восстанавливаем sessionStorage
        first_open_ok = await self.goto_safe(
            page=page,
            account_id=account_id,
            url="https://www.avito.ru/",
            wait_until="domcontentloaded",
            timeout=45000,
            retry_count=3,
        )

        if not first_open_ok:
            self.logger.warning(
                account_id,
                "⚠️ Первая загрузка домена была неидеальной, продолжаю восстановление"
            )

        session_storage_data = self._load_session_storage(account_id)
        if session_storage_data:
            restored = await self._restore_session_storage(page, account_id, session_storage_data)
            if restored:
                try:
                    await page.reload(wait_until="domcontentloaded", timeout=30000)
                    self.logger.info(
                        account_id,
                        "✅ Страница перезагружена после восстановления sessionStorage"
                    )
                except Exception as e:
                    self.logger.warning(
                        account_id,
                        f"⚠️ Не удалось перезагрузить страницу после sessionStorage: {str(e)[:120]}"
                    )

        window_title = f"🤖 AVITO BOT | Аккаунт {account_num} | {phone}"
        try:
            safe_title = window_title.replace("\\", "\\\\").replace("'", "\\'")
            await page.evaluate(f"document.title = '{safe_title}'")
            self.logger.info(account_id, f"✅ Название окна установлено: {window_title}")
        except Exception as e:
            self.logger.warning(account_id, f"⚠️ Не удалось установить title: {str(e)[:120]}")

        self._contexts[account_id] = context
        self._pages[account_id] = page
        self.total_launched += 1

        self.logger.action(account_id, "BROWSER", "LAUNCHED")

        print(f"  {Fore.GREEN}✅ Браузер запущен: {account_id}{Style.RESET_ALL}")
        print(f"     📱 Телефон: {phone}")
        print(f"     🪜 Прокси: {proxy_address}")
        print(f"     🪟 Окно: {window_title}")
        print(f"     🍪 Cookies: {'✅ Применены' if cookies_applied else '❌ Не найдены'}")

        return page

    # ════════════════════════════════════════════════════════════════
    # ДИАГНОСТИКА
    # ════════════════════════════════════════════════════════════════

    def _attach_page_diagnostics(self, page: Page, account_id: str) -> None:
        """Подключает базовую диагностику страницы."""

        def on_request_failed(request):
            try:
                failure = request.failure
                error_text = failure if isinstance(failure, str) else str(failure)
                self.logger.warning(
                    account_id,
                    f"REQUEST FAILED: {request.url[:140]} | {error_text[:120]}"
                )
            except Exception:
                pass

        def on_response(response):
            try:
                if response.status >= 400:
                    self.logger.warning(
                        account_id,
                        f"HTTP {response.status}: {response.url[:140]}"
                    )
            except Exception:
                pass

        def on_console(message):
            try:
                msg_type = getattr(message, "type", "console")
                text = message.text
                if msg_type in {"error", "warning"}:
                    self.logger.warning(
                        account_id,
                        f"CONSOLE {msg_type.upper()}: {text[:180]}"
                    )
            except Exception:
                pass

        try:
            page.on("requestfailed", on_request_failed)
            page.on("response", on_response)
            page.on("console", on_console)
        except Exception:
            pass

    # ════════════════════════════════════════════════════════════════
    # ПОЛУЧЕНИЕ ИНФОРМАЦИИ
    # ════════════════════════════════════════════════════════════════

    def get_page(self, account_id: str) -> Optional[Page]:
        return self._pages.get(account_id)

    def get_fingerprint(self, account_id: str) -> Optional[Fingerprint]:
        return self.fingerprint_store.get(account_id)

    def get_all_pages(self) -> Dict[str, Page]:
        return self._pages.copy()

    def get_all_accounts_status(self) -> Dict[str, Dict[str, Any]]:
        status: Dict[str, Dict[str, Any]] = {}

        for account_id, page in self._pages.items():
            account_num = account_id.split("_")[-1]
            account_config = settings.accounts.get(account_id, {})
            phone = account_config.get("phone", "unknown")
            proxy_address = self.proxy_manager.get_proxy_address(account_id)

            try:
                is_open = not page.is_closed()
            except Exception:
                is_open = False

            status[account_id] = {
                "num": account_num,
                "phone": phone,
                "proxy": proxy_address,
                "is_open": is_open,
                "url": page.url if is_open else "closed",
            }

        return status

    # ═══════════════════════════════════════════���════════════════════
    # ЗАКРЫТИЕ
    # ════════════════════════════════════════════════════════════════

    async def close(self, account_id: str) -> None:
        """
        Сохраняет состояние и закрывает страницу/контекст аккаунта.
        """

        try:
            self.logger.info(account_id, "🔄 Закрываю браузер и сохраняю сессию...")

            page = self._pages.get(account_id)
            context = self._contexts.get(account_id)

            if page and context:
                await self._persist_session(account_id, page, context)

            page = self._pages.pop(account_id, None)
            if page:
                try:
                    await page.close()
                    self.logger.info(account_id, "✅ Страница закрыта")
                except Exception as e:
                    self.logger.warning(
                        account_id,
                        f"⚠️ Ошибка закрытия страницы: {str(e)[:120]}"
                    )

            context = self._contexts.pop(account_id, None)
            if context:
                try:
                    await context.close()
                    self.logger.info(account_id, "✅ Контекст закрыт")
                except Exception as e:
                    self.logger.warning(
                        account_id,
                        f"⚠️ Ошибка закрытия контекста: {str(e)[:120]}"
                    )

            self.total_closed += 1

        except Exception as e:
            self.total_errors += 1
            self.logger.error(
                account_id,
                f"❌ Ошибка закрытия браузера: {str(e)[:150]}",
                severity="MEDIUM"
            )

    async def close_all(self) -> None:
        """Закрывает все страницы, контексты, браузер и Playwright."""
        for acc_id in list(self._pages.keys()):
            try:
                await self.close(acc_id)
            except Exception:
                pass

        try:
            if self._browser:
                await self._browser.close()
                self._browser = None
        except Exception:
            pass

        try:
            if self._pw:
                await self._pw.stop()
                self._pw = None
        except Exception:
            pass

        self.logger.system("✅ Все браузеры закрыты")

    async def reset_session(self, account_id: str) -> None:
        """
        Полный сброс сессии аккаунта:
        - закрытие браузера
        - удаление cookies
        - удаление storage_state
        - удаление sessionStorage
        - новый fingerprint
        """

        try:
            await self.close(account_id)

            cookies_file = self._get_cookies_path(account_id)
            storage_state_file = self._get_storage_state_path(account_id)
            session_storage_file = self._get_session_storage_path(account_id)

            for path in [cookies_file, storage_state_file, session_storage_file]:
                if path.exists():
                    path.unlink()

            from core.browser.fingerprint import generate_fingerprint

            new_fp = generate_fingerprint(account_id)
            self.fingerprint_store._store[account_id] = new_fp

            self.logger.success(account_id, "✅ Сессия полностью сброшена")

        except Exception as e:
            self.total_errors += 1
            self.logger.error(
                account_id,
                f"❌ Ошибка сброса сессии: {str(e)[:150]}",
                severity="MEDIUM"
            )

    # ════════════════════════════════════════════════════════════════
    # СОХРАНЕНИЕ СЕССИИ
    # ══════════════════════════════════════════════════════════════���═

    async def _persist_session(self, account_id: str, page: Page, context: BrowserContext) -> None:
        """Сохраняет cookies, storage_state и sessionStorage."""

        try:
            cookies = await context.cookies()
            self._save_cookies(account_id, cookies)
            self.logger.action(account_id, "SAVE_COOKIES", "SUCCESS", count=len(cookies))
        except Exception as e:
            self.logger.warning(
                account_id,
                f"⚠️ Не удалось сохранить cookies: {str(e)[:120]}"
            )

        try:
            storage_state_path = self._get_storage_state_path(account_id)
            await context.storage_state(path=str(storage_state_path))
            self.logger.info(account_id, "✅ storage_state сохранён")
        except Exception as e:
            self.logger.warning(
                account_id,
                f"⚠️ Не удалось сохранить storage_state: {str(e)[:120]}"
            )

        try:
            session_data = await self._extract_session_storage(page, account_id)
            self._save_session_storage(account_id, session_data)
            self.logger.info(
                account_id,
                f"✅ sessionStorage сохранён ({len(session_data)} ключей)"
            )
        except Exception as e:
            self.logger.warning(
                account_id,
                f"⚠️ Не удалось сохранить sessionStorage: {str(e)[:120]}"
            )

    async def _extract_session_storage(self, page: Page, account_id: str) -> Dict[str, str]:
        """Считывает sessionStorage со страницы."""
        try:
            data = await page.evaluate(
                """
                () => {
                    const result = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        result[key] = sessionStorage.getItem(key);
                    }
                    return result;
                }
                """
            )
            return data or {}
        except Exception as e:
            self.logger.warning(
                account_id,
                f"⚠️ Ошибка чтения sessionStorage: {str(e)[:120]}"
            )
            return {}

    async def _restore_session_storage(
        self,
        page: Page,
        account_id: str,
        session_data: Dict[str, str],
    ) -> bool:
        """Восстанавливает sessionStorage в текущей вкладке."""
        try:
            await page.evaluate(
                """
                (data) => {
                    for (const [key, value] of Object.entries(data)) {
                        sessionStorage.setItem(key, value);
                    }
                }
                """,
                session_data,
            )
            self.logger.info(
                account_id,
                f"✅ sessionStorage восстановлен ({len(session_data)} ключей)"
            )
            return True
        except Exception as e:
            self.logger.warning(
                account_id,
                f"⚠️ Ошибка восстановления sessionStorage: {str(e)[:120]}"
            )
            return False

    # ════════════════════════════════════════════════════════════════
    # ФАЙЛЫ СЕССИИ
    # ════════════════════════════════════════════════════════════════

    def _get_cookies_path(self, account_id: str) -> Path:
        return self.cookies_dir / f"{account_id}.json"

    def _get_storage_state_path(self, account_id: str) -> Path:
        return self.storage_state_dir / f"{account_id}.json"

    def _get_session_storage_path(self, account_id: str) -> Path:
        return self.session_storage_dir / f"{account_id}.json"

    def _save_cookies(self, account_id: str, cookies: List[Dict[str, Any]]) -> None:
        try:
            cookies_file = self._get_cookies_path(account_id)
            with open(cookies_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(
                account_id,
                f"⚠️ Не удалось сохранить cookies: {str(e)[:120]}"
            )

    def _load_cookies(self, account_id: str) -> List[Dict[str, Any]]:
        try:
            cookies_file = self._get_cookies_path(account_id)
            if cookies_file.exists():
                with open(cookies_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            self.logger.warning(
                account_id,
                f"⚠️ Не удалось загрузить cookies: {str(e)[:120]}"
            )
        return []

    def _save_session_storage(self, account_id: str, data: Dict[str, str]) -> None:
        try:
            path = self._get_session_storage_path(account_id)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(
                account_id,
                f"⚠️ Не удалось записать sessionStorage: {str(e)[:120]}"
            )

    def _load_session_storage(self, account_id: str) -> Dict[str, str]:
        try:
            path = self._get_session_storage_path(account_id)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            self.logger.warning(
                account_id,
                f"⚠️ Не удалось прочитать sessionStorage: {str(e)[:120]}"
            )
        return {}

    # ════════════════════════════════════════��═══════════════════════
    # НАВИГАЦИЯ
    # ════════════════════════════════════════════════════════════════

    async def goto_safe(
        self,
        page: Page,
        account_id: str,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: int = 20000,
        retry_count: int = 3,
    ) -> bool:
        """
        Надёжная навигация на URL с retry.
        """

        for attempt in range(1, retry_count + 1):
            try:
                self.logger.info(
                    account_id,
                    f"🌐 [Попытка {attempt}/{retry_count}] Переход: {url}"
                )

                await asyncio.wait_for(
                    page.goto(url, wait_until=wait_until, timeout=timeout),
                    timeout=(timeout / 1000) + 5,
                )

                self.logger.success(account_id, f"✅ Переход успешен: {url}")
                return True

            except asyncio.TimeoutError:
                self.logger.warning(account_id, f"⏱️ Timeout при переходе: {url}")
                if attempt < retry_count:
                    await asyncio.sleep(2)
                else:
                    self.logger.error(
                        account_id,
                        f"❌ Переход не удался после {retry_count} попыток: {url}",
                        severity="MEDIUM"
                    )
                    return False

            except Exception as e:
                self.logger.warning(
                    account_id,
                    f"⚠️ Ошибка перехода: {str(e)[:150]}"
                )
                if attempt < retry_count:
                    await asyncio.sleep(2)
                else:
                    self.logger.error(
                        account_id,
                        f"❌ Переход не удался: {str(e)[:150]}",
                        severity="MEDIUM"
                    )
                    return False

        return False