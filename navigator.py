# core/avito/navigator.py
"""
🚀 NAVIGATOR v2.4 (ИСПРАВЛЕННАЯ)
ИСПРАВЛЕНИЯ:
✅ Менее строгая проверка контента
✅ Правильная обработка ошибок при goto
✅ Совместимость с launcher.py логикой
✅ Поддержка retry и fallback
"""

import asyncio
import random
from typing import Optional

from playwright.async_api import Page

from core.avito.detector import check_threats, ThreatType, ThreatInfo
from core.avito.selectors import AvitoUrls


class AvitoNavigator:
    def __init__(self, logger):
        self.logger = logger

    async def goto(
        self,
        page: Page,
        url: str,
        account_id: str = "system",
        attempts: int = 3,
        timeout_ms: int = 30000,
    ) -> Optional[ThreatInfo]:
        """
        Перейти на Avito с проверкой загрузки (с retry + fallback)
        """
        
        for attempt in range(1, attempts + 1):
            try:
                self.logger.info(account_id, f"🌐 [{attempt}/{attempts}] {url[:60]}")
                
                # Первая попытка: load
                try:
                    await asyncio.wait_for(
                        page.goto(url, wait_until="load", timeout=timeout_ms),
                        timeout=timeout_ms / 1000 + 5
                    )
                except asyncio.TimeoutError:
                    # Fallback: networkidle
                    self.logger.warning(account_id, f"⏱️ load timeout, пробую networkidle...")
                    try:
                        await asyncio.wait_for(
                            page.goto(url, wait_until="networkidle", timeout=timeout_ms),
                            timeout=timeout_ms / 1000 + 5
                        )
                    except asyncio.TimeoutError:
                        # Fallback: domcontentloaded
                        self.logger.warning(account_id, f"⏱️ networkidle timeout, пробую domcontentloaded...")
                        await asyncio.wait_for(
                            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms),
                            timeout=timeout_ms / 1000 + 5
                        )
                
                await asyncio.sleep(2)
                
                is_ok = await self._verify_page_loaded(page, account_id, url)
                
                if is_ok:
                    threat = await check_threats(page)
                    
                    if threat and not threat.is_safe:
                        self.logger.risk(
                            account_id,
                            threat.type.value.upper(),
                            threat.message,
                            score=50
                        )
                    
                    self.logger.success(account_id, f"✅ Загружена ({attempt})")
                    return threat
                
                if attempt < attempts:
                    delay = random.uniform(2, 5)
                    self.logger.info(account_id, f"⏳ Ожидаю {delay:.1f} сек перед повтором...")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(account_id, f"❌ Не удалось загрузить после {attempts} попыток", severity="HIGH")
                    return None
            
            except asyncio.TimeoutError:
                self.logger.warning(account_id, f"⏱️ TIMEOUT (попытка {attempt}/{attempts})")
                
                if attempt < attempts:
                    await asyncio.sleep(random.uniform(3, 6))
                else:
                    return None
            
            except Exception as e:
                self.logger.error(account_id, f"goto ошибка: {str(e)[:100]}", severity="MEDIUM")
                
                if attempt < attempts:
                    await asyncio.sleep(random.uniform(2, 5))
                else:
                    return None
        
        return None

    async def _verify_page_loaded(self, page: Page, account_id: str, url: str) -> bool:
        """
        Проверить что страница загружена (менее строгая проверка)
        """
        
        try:
            current_url = page.url
            page_content = await page.content()
            
            # Проверяем что хотя бы минимально загрузилось
            if not current_url:
                self.logger.warning(account_id, f"⚠️ Нет URL")
                return False
            
            if len(page_content) < 500:  # Уменьшили с 1000 на 500
                self.logger.warning(account_id, f"⚠️ Мало контента ({len(page_content)} символов)")
                return False
            
            if "html" not in page_content.lower():
                self.logger.warning(account_id, f"⚠️ Нет HTML")
                return False
            
            self.logger.success(account_id, f"✅ Контент: {len(page_content)} символов")
            return True
        
        except Exception as e:
            self.logger.warning(account_id, f"⚠️ Ошибка проверки: {str(e)[:80]}")
            return False

    async def is_logged_in(self, page: Page) -> bool:
        """Проверить авторизацию"""
        try:
            if "login" in page.url.lower():
                return False
            
            profile_selectors = [
                '[data-marker="header/profile"]',
                '[data-marker="user-profile-button"]',
                'a[href*="/profile"]',
            ]
            
            for selector in profile_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        return True
                except Exception:
                    pass
            
            return False
        except Exception:
            return False

    async def click_listing(self, page: Page, index: int = 0) -> bool:
        """Кликнуть на объявление"""
        try:
            listings = await page.locator('[data-marker="item"]').all()
            
            if index >= len(listings):
                return False
            
            listing = listings[index]
            await listing.click()
            await asyncio.sleep(2.0)
            
            return True
        except Exception:
            return False

    async def search(self, page: Page, query: str) -> bool:
        """Поиск"""
        try:
            search_input = page.locator('input[data-marker="search-form/suggest"]').first
            
            if not await search_input.is_visible():
                return False
            
            await search_input.click()
            await asyncio.sleep(0.5)
            await search_input.type(query)
            await asyncio.sleep(1.0)
            
            submit_button = page.locator('button[data-marker="search-form/submit"]').first
            await submit_button.click()
            
            await asyncio.sleep(3.0)
            return True
        except Exception:
            return False

    async def go_back(self, page: Page) -> bool:
        """Назад"""
        try:
            await page.go_back()
            await asyncio.sleep(1.5)
            return True
        except Exception:
            return False