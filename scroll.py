# core/human/scroll.py
"""
📜 SCROLL CONTROLLER 2030 — МАКСИМАЛЬНО РЕАЛИСТИЧНЫЙ СКРОЛЛ
15+ паттернов скролла, momentum, случайные остановки, имитация "прочитанного текста"
Production ready, без сокращений
"""

from __future__ import annotations  # ← ДОБАВЬ ЭТО

import asyncio
import random
import math
from typing import Optional, List, Callable, Dict  # ← ДОБАВЬ Dict СЮДА
from enum import Enum
import time

from playwright.async_api import Page

from core.browser.fingerprint import Fingerprint


class ScrollPattern(Enum):
    """Паттерны скролла"""
    SMOOTH = "smooth"                       # Плавный скролл
    JERKY = "jerky"                         # Рывистый
    SLOW_THEN_FAST = "slow_then_fast"       # Медленно потом быстро
    FAST_THEN_SLOW = "fast_then_slow"       # Быстро потом медленно
    RANDOM_STOPS = "random_stops"           # Случайные остановки
    CAREFUL = "careful"                     # Осторожный, медленный
    DISTRACTED = "distracted"               # Отвлекается, прерывается
    MOMENTUM = "momentum"                   # Импульс (инерция)
    OVERSHOOT = "overshoot"                 # Перелёт вверх/вниз
    MICROSCROLL = "microscroll"             # Микроскролл
    ZIGZAG = "zigzag"                       # Зигзаг
    WAVE = "wave"                           # Волнообразный
    ACCELERATING = "accelerating"           # Ускоряющийся
    DECELERATING = "decelerating"           # Замедляющийся
    RHYTHMIC = "rhythmic"                   # Ритмичный
    CHAOTIC = "chaotic"                     # Хаотичный


class ScrollController:
    """
    📜 SCROLL CONTROLLER 2030
    
    Особенности:
    - 15+ паттернов скролла
    - Momentum (инерция)
    - Случайные остановки (читает текст)
    - Имитация скролла вверх (вспомнил что-то)
    - Микроскролл (поиск нужного элемента)
    - Зависимость от усталости и настроения
    """
    
    def __init__(self, fp: Optional[Fingerprint] = None):
        self.fp = fp
        self.session_start = time.time()
        self.total_scrolls = 0
        self.total_distance = 0
        self.scroll_pattern = self._get_scroll_pattern()
        
    def _get_scroll_pattern(self) -> ScrollPattern:
        """Определить основной паттерн скролла"""
        return random.choice(list(ScrollPattern))
    
    def get_tiredness(self) -> float:
        """Получить уровень усталости"""
        elapsed_hours = (time.time() - self.session_start) / 3600
        return min(1.0, elapsed_hours / 8.0)
    
    def _get_scroll_speed(self) -> float:
        """Получить скорость скролла (пиксели за срок)"""
        base_speeds = {
            ScrollPattern.SMOOTH: 350,
            ScrollPattern.JERKY: 280,
            ScrollPattern.SLOW_THEN_FAST: 250,
            ScrollPattern.FAST_THEN_SLOW: 400,
            ScrollPattern.RANDOM_STOPS: 320,
            ScrollPattern.CAREFUL: 150,
            ScrollPattern.DISTRACTED: 290,
            ScrollPattern.MOMENTUM: 450,
            ScrollPattern.OVERSHOOT: 400,
            ScrollPattern.MICROSCROLL: 50,
            ScrollPattern.ZIGZAG: 200,
            ScrollPattern.WAVE: 300,
            ScrollPattern.ACCELERATING: 200,
            ScrollPattern.DECELERATING: 350,
            ScrollPattern.RHYTHMIC: 300,
            ScrollPattern.CHAOTIC: 280,
        }
        
        base_speed = base_speeds.get(self.scroll_pattern, 300)
        
        # Усталость замедляет скролл
        tiredness = self.get_tiredness()
        base_speed *= (1.0 - tiredness * 0.2)
        
        # Вариативность
        return base_speed * random.uniform(0.8, 1.2)

    async def scroll(
        self,
        page: Page,
        distance: int,
        duration: float = 0.5
    ) -> None:
        """
        Скролить на определённое расстояние за время
        
        Args:
            page: Playwright Page
            distance: Расстояние в пиксели
            duration: Длительность скролла в секунды
        """
        
        try:
            await page.evaluate(f"window.scrollBy(0, {distance})")
            self.total_scrolls += 1
            self.total_distance += abs(distance)
            
            await asyncio.sleep(duration)
        except Exception:
            pass

    async def to_bottom(
        self,
        page: Page,
        max_scrolls: int = 15,
        max_duration: float = 60.0
    ) -> bool:
        """
        Скролить до конца страницы
        
        Args:
            page: Playwright Page
            max_scrolls: Максимум действий скролла
            max_duration: Максимальное время в секундах
            
        Returns:
            True если успешно, False если ошибка
        """
        
        try:
            scroll_height = await page.evaluate("document.body.scrollHeight")
            start_time = time.time()
            
            for scroll_num in range(max_scrolls):
                if time.time() - start_time > max_duration:
                    break
                
                current_scroll = await page.evaluate("window.scrollY")
                
                if current_scroll >= scroll_height - 500:
                    break
                
                # Выбираем паттерн для этого скролла
                pattern = random.choice(list(ScrollPattern))
                await self.apply_pattern(page, pattern)
                
                # Случайная пауза (читает текст)
                if random.random() < 0.3:
                    pause_duration = random.uniform(0.5, 2.0)
                    await asyncio.sleep(pause_duration)
            
            return True
        except Exception:
            return False

    async def to_top(self, page: Page) -> bool:
        """Скролить вверх до начала страницы"""
        try:
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            return True
        except Exception:
            return False

    async def apply_pattern(
        self,
        page: Page,
        pattern: Optional[ScrollPattern] = None
    ) -> None:
        """
        Применить паттерн скролла
        
        Args:
            page: Playwright Page
            pattern: Конкретный паттерн (если None, выбираем случайно)
        """
        
        if pattern is None:
            pattern = random.choice(list(ScrollPattern))
        
        pattern_methods = {
            ScrollPattern.SMOOTH: self.smooth,
            ScrollPattern.JERKY: self.jerky,
            ScrollPattern.SLOW_THEN_FAST: self.slow_then_fast,
            ScrollPattern.FAST_THEN_SLOW: self.fast_then_slow,
            ScrollPattern.RANDOM_STOPS: self.random_stops,
            ScrollPattern.CAREFUL: self.careful,
            ScrollPattern.DISTRACTED: self.distracted,
            ScrollPattern.MOMENTUM: self.momentum,
            ScrollPattern.OVERSHOOT: self.overshoot,
            ScrollPattern.MICROSCROLL: self.microscroll,
            ScrollPattern.ZIGZAG: self.zigzag,
            ScrollPattern.WAVE: self.wave,
            ScrollPattern.ACCELERATING: self.accelerating,
            ScrollPattern.DECELERATING: self.decelerating,
            ScrollPattern.RHYTHMIC: self.rhythmic,
            ScrollPattern.CHAOTIC: self.chaotic,
        }
        
        method = pattern_methods.get(pattern)
        if method:
            await method(page)

    # ════════════════════════════════════════════════════════════════
    # ПАТТЕРНЫ СКРОЛЛА
    # ════════════════════════════════════════════════════════════════

    async def smooth(self, page: Page) -> None:
        """SMOOTH: Плавный скролл"""
        distance = random.randint(200, 400)
        await self.scroll(page, distance, duration=random.uniform(0.4, 0.8))

    async def jerky(self, page: Page) -> None:
        """JERKY: Рывистый скролл (несколько движений)"""
        num_jerks = random.randint(2, 5)
        
        for _ in range(num_jerks):
            distance = random.randint(80, 200)
            await self.scroll(page, distance, duration=random.uniform(0.1, 0.3))
            await asyncio.sleep(random.uniform(0.1, 0.3))

    async def slow_then_fast(self, page: Page) -> None:
        """SLOW_THEN_FAST: Медленно потом быстро"""
        await self.scroll(page, random.randint(100, 150), duration=random.uniform(0.5, 1.0))
        await asyncio.sleep(random.uniform(0.3, 0.6))
        await self.scroll(page, random.randint(250, 400), duration=random.uniform(0.2, 0.4))

    async def fast_then_slow(self, page: Page) -> None:
        """FAST_THEN_SLOW: Быстро потом медленно"""
        await self.scroll(page, random.randint(300, 450), duration=random.uniform(0.2, 0.4))
        await asyncio.sleep(random.uniform(0.3, 0.6))
        await self.scroll(page, random.randint(100, 150), duration=random.uniform(0.5, 1.0))

    async def random_stops(self, page: Page) -> None:
        """RANDOM_STOPS: Скролл с случайными остановками (читает)"""
        total_distance = random.randint(200, 400)
        num_segments = random.randint(2, 4)
        segment_distance = total_distance // num_segments
        
        for i in range(num_segments):
            await self.scroll(page, segment_distance, duration=random.uniform(0.2, 0.4))
            
            # Остановка чтобы прочитать
            await asyncio.sleep(random.uniform(0.5, 2.0))

    async def careful(self, page: Page) -> None:
        """CAREFUL: Осторожный медленный скролл"""
        distance = random.randint(50, 150)
        await self.scroll(page, distance, duration=random.uniform(1.0, 2.0))

    async def distracted(self, page: Page) -> None:
        """DISTRACTED: Отвлекается, прерывается"""
        # Скролим вниз
        await self.scroll(page, random.randint(200, 300), duration=random.uniform(0.3, 0.6))
        
        # Вспомнил что-то, скролим обратно
        if random.random() < 0.4:
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self.scroll(page, -random.randint(100, 200), duration=random.uniform(0.3, 0.5))

    async def momentum(self, page: Page) -> None:
        """MOMENTUM: Импульс (инерция скролла)"""
        # Быстрый скролл
        distance = random.randint(400, 600)
        await self.scroll(page, distance, duration=random.uniform(0.2, 0.3))
        
        # Замедление (инерция)
        for _ in range(3):
            distance = int(distance * 0.6)
            if distance < 30:
                break
            await self.scroll(page, distance, duration=random.uniform(0.1, 0.2))

    async def overshoot(self, page: Page) -> None:
        """OVERSHOOT: Перелёт вверх/вниз"""
        # Скролим в одну сторону
        distance = random.randint(250, 350)
        await self.scroll(page, distance, duration=random.uniform(0.3, 0.5))
        
        # Перелётели, скролим обратно
        await asyncio.sleep(random.uniform(0.2, 0.4))
        await self.scroll(page, -random.randint(50, 100), duration=random.uniform(0.2, 0.3))

    async def microscroll(self, page: Page) -> None:
        """MICROSCROLL: Микроскролл (поиск элемента)"""
        for _ in range(random.randint(3, 7)):
            distance = random.randint(10, 50)
            direction = random.choice([-1, 1])
            await self.scroll(page, direction * distance, duration=random.uniform(0.1, 0.2))
            await asyncio.sleep(random.uniform(0.2, 0.5))

    async def zigzag(self, page: Page) -> None:
        """ZIGZAG: Зигзаг (вверх-вниз-вверх)"""
        for _ in range(random.randint(2, 4)):
            await self.scroll(page, random.randint(100, 200), duration=random.uniform(0.2, 0.4))
            await asyncio.sleep(random.uniform(0.2, 0.4))
            await self.scroll(page, -random.randint(50, 100), duration=random.uniform(0.2, 0.3))
            await asyncio.sleep(random.uniform(0.2, 0.4))

    async def wave(self, page: Page) -> None:
        """WAVE: Волнообразный скролл"""
        # Волна вниз
        for _ in range(3):
            distance = random.randint(80, 160)
            await self.scroll(page, distance, duration=random.uniform(0.15, 0.25))
            await asyncio.sleep(random.uniform(0.1, 0.2))

    async def accelerating(self, page: Page) -> None:
        """ACCELERATING: Ускоряющийся скролл"""
        base_distance = 50
        for i in range(5):
            distance = base_distance * (i + 1)
            duration = 0.5 / (i + 1)
            await self.scroll(page, distance, duration=duration)
            await asyncio.sleep(random.uniform(0.1, 0.2))

    async def decelerating(self, page: Page) -> None:
        """DECELERATING: Замедляющийся скролл"""
        base_distance = 300
        for i in range(4):
            distance = int(base_distance * (1 - i * 0.2))
            duration = 0.2 * (i + 1)
            await self.scroll(page, distance, duration=duration)
            await asyncio.sleep(random.uniform(0.1, 0.2))

    async def rhythmic(self, page: Page) -> None:
        """RHYTHMIC: Ритмичный скролл"""
        for _ in range(random.randint(4, 6)):
            distance = random.randint(150, 250)
            await self.scroll(page, distance, duration=random.uniform(0.3, 0.4))
            await asyncio.sleep(random.uniform(0.4, 0.6))

    async def chaotic(self, page: Page) -> None:
        """CHAOTIC: Хаотичный скролл"""
        for _ in range(random.randint(5, 10)):
            distance = random.randint(-200, 400)
            await self.scroll(page, distance, duration=random.uniform(0.1, 0.5))
            await asyncio.sleep(random.uniform(0.1, 0.5))

    # ════════════════════════════════════════════════════════════════
    # СПЕЦИАЛЬНЫЕ МЕТОДЫ
    # ════════════════════════════════════════════════════════════════

    async def pattern(self, page: Page) -> bool:
        """Применить случайный паттерн"""
        try:
            await self.apply_pattern(page)
            return True
        except Exception:
            return False

    async def random(self, page: Page) -> bool:
        """Полностью случайный скролл"""
        try:
            pattern = random.choice(list(ScrollPattern))
            await self.apply_pattern(page, pattern)
            return True
        except Exception:
            return False

    async def to_element(
        self,
        page: Page,
        selector: str
    ) -> bool:
        """Скролить до видимости элемента"""
        try:
            element = page.locator(selector).first
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.5, 1.0))
            return True
        except Exception:
            return False

    def get_statistics(self) -> Dict:
        """Получить статистику скролла"""
        return {
            "total_scrolls": self.total_scrolls,
            "total_distance_pixels": self.total_distance,
            "session_duration": time.time() - self.session_start,
            "current_pattern": self.scroll_pattern.value,
            "tiredness": round(self.get_tiredness() * 100),
        }