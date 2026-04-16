# core/human/behavior.py
"""
🤖 HUMAN BEHAVIOR 2030 — МАКСИМАЛЬНО РЕАЛИСТИЧНОЕ ПОВЕДЕНИЕ ЧЕЛОВЕКА
Динамическая усталость, mood по времени суток, deep_view, natural_favorite, тонкий контроль мыши/скролла
Production ready, без сокращений
"""

import asyncio
import random
import math
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
from colorama import Fore, Style

from playwright.async_api import Page

from core.browser.fingerprint import Fingerprint
from core.human.mouse import move_mouse, click_element, random_mouse_movement
from core.human.scroll import ScrollController
from core.human.keyboard import type_text, type_phone
from config.settings import settings


class MoodType(Enum):
    """Настроение пользователя"""
    EXCELLENT = "отличное"
    GOOD = "хорошее"
    NEUTRAL = "нейтральное"
    BAD = "плохое"
    TIRED = "усталое"


class TimeOfDayType(Enum):
    """Время суток"""
    EARLY_MORNING = "ночь_рано"        # 00:00-06:00
    MORNING = "утро"                    # 06:00-12:00
    AFTERNOON = "день"                  # 12:00-18:00
    EVENING = "вечер"                   # 18:00-00:00


class HumanBehavior:
    """
    🤖 HUMAN BEHAVIOR 2030
    
    Характеристики:
    - Динамическая усталость (растёт со временем)
    - Mood по времени суток
    - Интерес к контенту (случайный, может меняться)
    - Терпение (зависит от усталости и настроения)
    - Focus loss (потеря концентрации)
    - Mouse и скролл зависят от усталости
    """

    def __init__(self, fp: Optional[Fingerprint] = None, logger=None):
        """Инициализация человека"""
        self.fp = fp
        self.logger = logger
        
        # ─────────────────────────────────────────────────────
        # ВРЕМЯ И СОСТОЯНИЕ
        # ─────────────────────────────────────────────────────
        
        self.session_start = datetime.now()
        self.actions_performed = 0
        
        # ────────────────────────────────────────────��────────
        # ХАРАКТЕРИСТИКИ
        # ─────────────────────────────────────────────────────
        
        self.tiredness = 0.0  # 0.0-1.0 (растёт со временем)
        self.interest_level = random.uniform(0.6, 0.9)  # 0.0-1.0 (интерес к контенту)
        self.patience = random.uniform(0.7, 0.9)  # 0.0-1.0 (терпение при загрузке)
        self.mood = self._get_mood_for_time()  # Настроение зависит от времени суток
        self.focus_loss = 0.0  # 0.0-1.0 (потеря концентрации)
        self.boredom = 0.0  # 0.0-1.0 (скука, способна отвлечь)
        
        # ─────────────────────────────────────────────────────
        # ИНДИВИДУАЛЬНЫЕ ЧЕРТЫ
        # ─────────────────────────────────────────────────────
        
        self.reading_speed = random.choice(["fast_scroller", "average", "careful_reader"])
        self.click_accuracy = random.uniform(0.85, 0.99)  # Точность кликов
        self.scroll_style = random.choice(["smooth", "jerky", "natural"])
        self.mouse_speed = random.uniform(0.5, 1.5)  # Скорость мыши
        
        # ─────────────────────────────────────────────────────
        # СИСТЕМЫ КОНТРОЛЯ
        # ─────────────────────────────────────────────────────
        
        self.scroll_controller = ScrollController(fp)
        
        # ─────────────────────────────────────────────────────
        # СТАТИСТИКА
        # ─────────────────────────────────────────────────────
        
        self.daily_actions = 0
        self.clicks_performed = 0
        self.scrolls_performed = 0
        self.pages_viewed = 0
        self.cards_opened = 0

    # ════════════════════════════════════════════════════════════════
    # СОСТОЯНИЕ И ОБНОВЛЕНИЯ
    # ════════════════════════════════════════════════════════════════

    def _get_mood_for_time(self) -> MoodType:
        """Определить настроение в зависимости от времени суток"""
        hour = datetime.now().hour
        
        if hour >= 6 and hour < 10:
            return random.choice([MoodType.EXCELLENT, MoodType.GOOD])
        elif hour >= 10 and hour < 14:
            return random.choice([MoodType.GOOD, MoodType.NEUTRAL])
        elif hour >= 14 and hour < 18:
            return random.choice([MoodType.NEUTRAL, MoodType.GOOD])
        elif hour >= 18 and hour < 22:
            return random.choice([MoodType.GOOD, MoodType.NEUTRAL])
        elif hour >= 22 or hour < 6:
            return random.choice([MoodType.TIRED, MoodType.BAD])
        
        return MoodType.NEUTRAL

    def _get_time_of_day(self) -> TimeOfDayType:
        """Определить время суток"""
        hour = datetime.now().hour
        
        if hour >= 0 and hour < 6:
            return TimeOfDayType.EARLY_MORNING
        elif hour >= 6 and hour < 12:
            return TimeOfDayType.MORNING
        elif hour >= 12 and hour < 18:
            return TimeOfDayType.AFTERNOON
        else:
            return TimeOfDayType.EVENING

    def update_state(self) -> None:
        """
        Обновить состояние человека
        
        Вызывается регулярно во время сессии
        - Усталость растёт со временем
        - Интерес может падать
        - Терпение зависит от усталости
        - Mood может меняться
        - Focus loss растёт
        """
        elapsed_hours = (datetime.now() - self.session_start).total_seconds() / 3600
        
        # ─────────────────────────────────────────────────────
        # УСТАЛОСТЬ: линейно растёт (0% через 1 час, 100% через 8 часов)
        # ─────────────────────────────────────────────────────
        
        self.tiredness = min(1.0, elapsed_hours / 8.0)
        
        # ─────────────────────────────────────────────────────
        # ИНТЕРЕС: падает со временем + случайный компонент
        # ─────────────────────────────────────────────────────
        
        interest_decay = min(0.3, elapsed_hours * 0.05)  # -5% за час, макс -30%
        self.interest_level = max(0.2, self.interest_level - random.uniform(0, interest_decay))
        
        # ─────────────────────────────────────────────────────
        # ТЕРПЕНИЕ: снижается с усталостью и плохим настроением
        # ─────────────────────────────────────────────────────
        
        mood_penalty = 0.0
        if self.mood == MoodType.BAD:
            mood_penalty = 0.3
        elif self.mood == MoodType.TIRED:
            mood_penalty = 0.2
        
        self.patience = max(0.3, 0.9 - self.tiredness * 0.5 - mood_penalty)
        
        # ─────────────────────────────────────────────────────
        # ПОТЕРЯ КОНЦЕНТРАЦИИ: растёт с усталостью и скукой
        # ─────────────────────────────────────────────────────
        
        self.focus_loss = min(1.0, self.tiredness * 1.2 + self.boredom * 0.5)
        
        # ─────────────────────────────────────────────────────
        # СКУКА: может случайно вырасти (отвлекается от контента)
        # ─────────────────────────────────────────────────────
        
        if random.random() < 0.05:  # 5% шанс за каждый update
            self.boredom = min(1.0, self.boredom + random.uniform(0.05, 0.15))
        else:
            self.boredom = max(0.0, self.boredom - 0.05)  # Скука уменьшается

    # ════════════════════════════════════════════════════════════════
    # БАЗОВЫЕ ДЕЙСТВИЯ: КЛИКИ, ПЕЧАТЬ
    # ════════════════════════════════════════════════════════════════

    async def click(
        self,
        page: Page,
        selector: str,
        human_like: bool = True,
        double_click: bool = False
    ) -> bool:
        """
        Кликнуть на элемент как человек
        
        - Мышь движется к элементу с естественной траекторией
        - Может быть небольшая задержка перед кликом
        - После клика пауза зависит от усталости
        """
        self.update_state()
        
        try:
            if human_like:
                await click_element(
                    page=page,
                    selector=selector,
                    fp=self.fp,
                    double_click=double_click,
                    mouse_speed=self.mouse_speed
                )
            else:
                await page.locator(selector).first.click()
            
            # Пауза после клика зависит от усталости
            base_pause = random.uniform(0.4, 1.0)
            tiredness_multiplier = 1.0 + self.tiredness * 0.8
            pause = base_pause * tiredness_multiplier
            await asyncio.sleep(pause)
            
            self.clicks_performed += 1
            self.actions_performed += 1
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Click failed: {e}")
            return False

    async def type(
        self,
        page: Page,
        selector: str,
        text: str,
        typos: bool = True
    ) -> bool:
        """
        Печатать текст как человек
        
        - Опечатки (если typos=True)
        - Пауза между символами
        - Зависит от скорости чтения
        """
        self.update_state()
        
        try:
            await type_text(
                page=page,
                selector=selector,
                text=text,
                fp=self.fp,
                make_typos=typos and random.random() < 0.3
            )
            return True
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Type failed: {e}")
            return False

    async def type_phone_number(self, page: Page, selector: str, phone: str) -> bool:
        """Печатать телефон БЕЗ опечаток"""
        try:
            await type_phone(page=page, selector=selector, phone=phone, fp=self.fp)
            return True
        except Exception:
            return False

    # ════════════════════════════════════════════════════════════════
    # ПРОСМОТР КОНТЕНТА
    # ════════════════════════════════════════════════════════════════

    async def browse_page(
        self,
        page: Page,
        duration_seconds: float = 25.0
    ) -> bool:
        """
        Просмотреть страницу как живой человек
        
        - Время зависит от reading_speed
        - Во время просмотра может скролить
        - Может отвлекаться (потеря концентрации)
        """
        self.update_state()
        
        # Модифицируем время в зависимости от стиля чтения
        if self.reading_speed == "fast_scroller":
            duration_seconds *= 0.6
        elif self.reading_speed == "careful_reader":
            duration_seconds *= 1.8
        
        # Модифицируем время в зависимости от усталости
        tiredness_factor = 1.0 - self.tiredness * 0.3  # При 100% усталости -30% времени
        duration_seconds *= tiredness_factor
        
        deadline = datetime.now().timestamp() + duration_seconds
        
        try:
            while datetime.now().timestamp() < deadline:
                # Иногда скроллим (40% вероятность)
                if random.random() < 0.4:
                    await self.scroll_controller.pattern(page)
                    await asyncio.sleep(random.uniform(1.0, 4.5))
                
                # Иногда просто ждём (читаем)
                else:
                    pause = random.uniform(2.0, 8.0)
                    await asyncio.sleep(pause)
                
                # И��огда двигаем мышь (10% вероятность)
                if random.random() < 0.10:
                    try:
                        await random_mouse_movement(page, self.fp)
                    except Exception:
                        pass
            
            self.pages_viewed += 1
            self.actions_performed += 1
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Browse page failed: {e}")
            return False

    async def scroll_page(
        self,
        page: Page,
        max_scrolls: int = 10
    ) -> bool:
        """
        Скролить страницу как живой человек
        
        - Стиль скролла может быть smooth, jerky или natural
        - Пауза между скроллами зависит от усталости
        - Может прервать скролл если скучно
        """
        self.update_state()
        
        try:
            scrolls_done = 0
            
            for i in range(max_scrolls):
                # Если скучно, может остановиться раньше
                if self.boredom > 0.7 and random.random() < 0.3:
                    break
                
                # Патерн скролла
                await self.scroll_controller.pattern(page)
                scrolls_done += 1
                
                # Пауза между скроллами зависит от усталости
                base_pause = random.uniform(1.2, 4.8)
                tiredness_multiplier = 1.0 + self.tiredness * 0.6
                pause = base_pause * tiredness_multiplier
                
                await asyncio.sleep(pause)
                
                # Изредка уходит на другую часть страницы
                if random.random() < 0.08:
                    break
            
            self.scrolls_performed += scrolls_done
            self.actions_performed += 1
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Scroll failed: {e}")
            return False

    # ════════════════════════════════════════════════════════════════
    # СПЕЦИАЛЬНЫЕ ДЕЙСТВИЯ ДЛЯ AVITO
    # ════════════════════════════════════════════════════════════════

    async def view_card_photos(
        self,
        page: Page,
        duration_seconds: float = 30.0
    ) -> bool:
        """
        Просмотреть фото карточки объявления
        
        - Листать фото (если есть)
        - Зависит от интереса
        - Может долго рассматривать интересное фото
        """
        self.update_state()
        
        try:
            # Модифицируем время в зависимости от интереса
            duration_seconds *= (0.5 + self.interest_level)  # 0.5x-1.5x
            
            deadline = datetime.now().timestamp() + duration_seconds
            
            while datetime.now().timestamp() < deadline:
                # Попытка листать фото (если есть кнопка)
                try:
                    next_photo_btn = page.locator('[data-marker="gallery-navigation/next"]').first
                    if await next_photo_btn.is_visible(timeout=1000):
                        if random.random() < 0.4:  # 40% вероятность листать
                            await next_photo_btn.click()
                            await asyncio.sleep(random.uniform(1, 3))
                except Exception:
                    pass
                
                # Рассматриваем фото
                await asyncio.sleep(random.uniform(2, 5))
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"View photos failed: {e}")
            return False

    async def read_description(
        self,
        page: Page,
        duration_seconds: float = 20.0
    ) -> bool:
        """
        Читать описание объявления
        
        - Время зависит от reading_speed
        - Может скролить описание
        - Может пропустить если скучно
        """
        self.update_state()
        
        if self.reading_speed == "fast_scroller":
            duration_seconds *= 0.5
        elif self.reading_speed == "careful_reader":
            duration_seconds *= 2.0
        
        # Если скучно, может не читать
        if self.boredom > 0.8 and random.random() < 0.3:
            return True
        
        try:
            deadline = datetime.now().timestamp() + duration_seconds
            
            while datetime.now().timestamp() < deadline:
                # Иногда скроллим описание
                if random.random() < 0.3:
                    await page.evaluate("() => window.scrollY += 200")
                
                await asyncio.sleep(random.uniform(1, 4))
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Read description failed: {e}")
            return False

    async def scroll_card_details(self, page: Page) -> bool:
        """Скролить детали карточки (характеристики, отзывы)"""
        try:
            for _ in range(random.randint(2, 4)):
                await page.evaluate("() => window.scrollY += 300")
                await asyncio.sleep(random.uniform(1, 3))
            return True
        except Exception:
            return False

    async def deep_view_card(
        self,
        page: Page,
        selector_index: int = 0,
        duration_seconds: float = 45.0
    ) -> bool:
        """
        ГЛУБОКИЙ ПРОСМОТР КАРТОЧКИ (ГЛАВНАЯ ФИШКА)
        
        - Открыть карточку
        - Просмотреть фото 20-45 сек
        - Прочитать описание 10-25 сек
        - Посмотреть детали/отзывы
        - Вернуться назад
        """
        self.update_state()
        
        try:
            print(f"      [Deep View] Открываю карточку...", end=" ", flush=True)
            
            # Открываем карточку
            listings = await page.locator('[data-marker="item"]').count()
            if listings == 0:
                print(f"{Fore.RED}✗ (нет карточек){Style.RESET_ALL}")
                return False
            
            actual_idx = min(selector_index, listings - 1)
            await page.locator('[data-marker="item"]').nth(actual_idx).click()
            
            await asyncio.sleep(random.uniform(1.5, 3))
            print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
            
            # Просмотр фото
            photo_duration = random.uniform(20, 45)
            await self.view_card_photos(page, duration_seconds=photo_duration)
            
            # Чтение описания
            desc_duration = random.uniform(10, 25)
            await self.read_description(page, duration_seconds=desc_duration)
            
            # Иногда скроллим детали
            if random.random() < 0.6:
                await self.scroll_card_details(page)
            
            # Возвращаемся
            await page.go_back()
            await asyncio.sleep(random.uniform(1, 2))
            
            self.cards_opened += 1
            self.actions_performed += 1
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Deep view card failed: {e}")
            return False

    async def natural_favorite(
        self,
        page: Page,
        selector_index: int = 0
    ) -> bool:
        """
        ЕСТЕСТВЕННОЕ ДОБАВЛЕНИЕ В ИЗБРАННОЕ
        
        - Открыть карточку
        - Посмотреть её (short view)
        - Найти кнопку "в избранное"
        - Добавить с естественной паузой
        """
        self.update_state()
        
        try:
            # Открываем карточку
            listings = await page.locator('[data-marker="item"]').count()
            if listings == 0:
                return False
            
            actual_idx = min(selector_index, listings - 1)
            await page.locator('[data-marker="item"]').nth(actual_idx).click()
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Короткий просмотр
            await self.browse_page(page, duration_seconds=random.uniform(5, 12))
            
            # Ищем кнопку "в избранное"
            try:
                fav_btn = page.locator('[data-marker="favorite-button"]').first
                if await fav_btn.is_visible(timeout=2000):
                    # Паузы как у живого человека
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    # Наводим мышь (показываем раздумье)
                    await fav_btn.hover()
                    await asyncio.sleep(random.uniform(0.3, 0.8))
                    
                    # Кликаем
                    await fav_btn.click()
                    await asyncio.sleep(random.uniform(0.5, 1.2))
                    
                    # Возвращаемся
                    await page.go_back()
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    return True
            except Exception:
                pass
            
            await page.go_back()
            return False
            
        except Exception as e:
            if self.logger:
                self.logger.warning("human_behavior", f"Natural favorite failed: {e}")
            return False

    # ════════════════════════════════════════════════════════════════
    # ПОИСК И ДРУГОЕ
    # ════════════════════════════════════════════════════════════════

    async def fill_search(
        self,
        page: Page,
        query: str,
        selector: str = "input[data-marker='search-form/suggest']"
    ) -> bool:
        """Заполнить поисковое поле"""
        self.update_state()
        
        try:
            await self.click(page, selector)
            
            # Печатаем с паузами между словами
            words = query.split()
            for i, word in enumerate(words):
                await self.type(page, selector, word, typos=True)
                
                if i < len(words) - 1:
                    await asyncio.sleep(random.uniform(0.3, 0.8))
                    await page.keyboard.press(" ")
            
            return True
        except Exception:
            return False

    async def hover_element(self, page: Page, selector: str) -> bool:
        """Навести мышь на элемент"""
        try:
            element = page.locator(selector).first
            await element.hover()
            await asyncio.sleep(random.uniform(0.5, 2.0))
            return True
        except Exception:
            return False

    # ════════════════════════════════════════════════════════════════
    # ПАУЗЫ И СЛУЧАЙНОЕ
    # ══════════════════════════════════���═════════════════════════════

    async def get_natural_pause(
        self,
        min_sec: float = 1.0,
        max_sec: float = 5.0
    ) -> float:
        """
        Получить естественную паузу
        
        - Зависит от усталости (усталый движется медленнее)
        - Зависит от терпения (нетерпеливый быстрее)
        - Может быть случайная длинная пауза (думает)
        """
        self.update_state()
        
        # Базовая пауза
        base_pause = random.uniform(min_sec, max_sec)
        
        # Модификаторы
        tiredness_multiplier = 1.0 + self.tiredness * 0.5
        patience_multiplier = 2.0 - self.patience  # Нетерпеливый быстрее
        
        pause = base_pause * tiredness_multiplier * patience_multiplier
        
        # Иногда очень долгая пауза (отвлекся, думает)
        if random.random() < 0.05:  # 5% шанс
            pause *= random.uniform(3, 8)
        
        return pause

    async def random_human_action(self, page: Page) -> bool:
        """Выполнить случайное человеческое действие"""
        self.update_state()
        
        actions_weights = {
            "scroll": 0.30,
            "mouse_move": 0.20,
            "pause": 0.25,
            "refresh": 0.15,
            "back": 0.10,
        }
        
        action = random.choices(
            list(actions_weights.keys()),
            weights=list(actions_weights.values()),
            k=1
        )[0]
        
        try:
            if action == "scroll":
                await self.scroll_controller.random(page)
            elif action == "mouse_move":
                await random_mouse_movement(page, self.fp)
            elif action == "pause":
                pause = await self.get_natural_pause(min_sec=2, max_sec=5)
                await asyncio.sleep(pause)
            elif action == "refresh":
                await page.reload()
            elif action == "back":
                await page.go_back()
            
            return True
        except Exception:
            return False

    # ════════════════════════════════════════════════════════════════
    # СОСТОЯНИЕ И ДИАГНОСТИКА
    # ════════════════════════════════════════════════════════════════

    def get_state(self) -> Dict:
        """Получить текущее состояние"""
        self.update_state()
        return {
            "tiredness_percent": round(self.tiredness * 100),
            "interest_level_percent": round(self.interest_level * 100),
            "patience_percent": round(self.patience * 100),
            "focus_loss_percent": round(self.focus_loss * 100),
            "boredom_percent": round(self.boredom * 100),
            "mood": self.mood.value,
            "time_of_day": self._get_time_of_day().value,
            "reading_speed": self.reading_speed,
            "session_duration_hours": round(
                (datetime.now() - self.session_start).total_seconds() / 3600, 2
            ),
            "actions_performed": self.actions_performed,
            "clicks": self.clicks_performed,
            "scrolls": self.scrolls_performed,
            "pages_viewed": self.pages_viewed,
            "cards_opened": self.cards_opened,
        }

    def reset(self):
        """Сбросить состояние (новый день)"""
        self.session_start = datetime.now()
        self.tiredness = 0.0
        self.interest_level = random.uniform(0.6, 0.9)
        self.patience = random.uniform(0.7, 0.9)
        self.mood = self._get_mood_for_time()
        self.focus_loss = 0.0
        self.boredom = 0.0
        self.daily_actions = 0