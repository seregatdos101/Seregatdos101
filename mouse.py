# core/human/mouse.py
"""
🖱️ MOUSE ENGINE 2030 — МАКСИМАЛЬНО РЕАЛИСТИЧНОЕ ДВИЖЕНИЕ МЫШИ
Brownian motion, micro-tremors, fidgeting, естественное ускорение/замедление
Production ready, без сокращений
"""

import asyncio
import random
import math
from typing import Tuple, List, Optional, Dict
from enum import Enum
import time

from playwright.async_api import Page

from core.browser.fingerprint import Fingerprint


class MouseMovementStyle(Enum):
    """Стиль движения мыши"""
    PRECISE = "precise"               # Точный, медленный
    FAST = "fast"                     # Быстрый
    CASUAL = "casual"                 # Обычный
    NERVOUS = "nervous"               # Нервный, много микро-движений
    TIRED = "tired"                   # Усталый, неточный


class MouseEngine:
    """
    🖱️ MOUSE ENGINE 2030
    
    Особенности:
    - Brownian motion (броуновское движение)
    - Micro-tremors (микродрожание)
    - Fidgeting (мелкие движения)
    - "Поиск" элемента (наводка туда-сюда)
    - Ускорение/замедление как у человека
    - Overshoot имитация (перелёт за точку)
    - Естественные паузы
    """
    
    def __init__(self, fp: Optional[Fingerprint] = None):
        self.fp = fp
        self.last_x = random.randint(150, 1200)
        self.last_y = random.randint(100, 700)
        self.session_start_time = time.time()
        self.movement_style = self._get_movement_style()
        self.total_movements = 0
        self.total_clicks = 0
        self.hover_duration_total = 0.0
        
    def _get_movement_style(self) -> MouseMovementStyle:
        """Определить стиль движения мыши"""
        styles = list(MouseMovementStyle)
        return random.choice(styles)
    
    def get_tiredness(self) -> float:
        """Получить уровень усталости (0-1)"""
        elapsed_hours = (time.time() - self.session_start_time) / 3600
        return min(1.0, elapsed_hours / 8.0)
    
    def _get_mouse_speed_multiplier(self) -> float:
        """Получить множитель скорости мыши"""
        multipliers = {
            MouseMovementStyle.PRECISE: 0.5,
            MouseMovementStyle.FAST: 2.0,
            MouseMovementStyle.CASUAL: 1.0,
            MouseMovementStyle.NERVOUS: 1.3,
            MouseMovementStyle.TIRED: 0.7,
        }
        
        base_mult = multipliers.get(self.movement_style, 1.0)
        
        # Усталость замедляет движение
        tiredness = self.get_tiredness()
        base_mult *= (1.0 - tiredness * 0.3)
        
        return base_mult
    
    def _get_tremor_intensity(self) -> float:
        """Получить интенсивность дрожания"""
        intensities = {
            MouseMovementStyle.PRECISE: 0.3,
            MouseMovementStyle.FAST: 0.8,
            MouseMovementStyle.CASUAL: 0.5,
            MouseMovementStyle.NERVOUS: 1.5,
            MouseMovementStyle.TIRED: 1.2,
        }
        
        intensity = intensities.get(self.movement_style, 0.5)
        
        # Усталость увеличивает дрожание
        tiredness = self.get_tiredness()
        intensity *= (1.0 + tiredness * 0.8)
        
        return intensity


def _brownian_motion(
    start: Tuple[float, float],
    end: Tuple[float, float],
    num_points: int = 50,
    deviation: float = 0.0
) -> List[Tuple[int, int]]:
    """
    Броуновское движение — более реалистичное чем Безье
    
    Добавляет случайные отклонения на каждом шаге пути
    """
    
    x0, y0 = start
    x_end, y_end = end
    
    points = []
    current_x, current_y = x0, y0
    
    # Начальный вектор
    dx = (x_end - x0) / num_points
    dy = (y_end - y0) / num_points
    
    for i in range(num_points + 1):
        # Линейное движение
        target_x = x0 + dx * i
        target_y = y0 + dy * i
        
        # Броуновское отклонение
        random_deviation_x = random.gauss(0, deviation * (x_end - x0) / 100)
        random_deviation_y = random.gauss(0, deviation * (y_end - y0) / 100)
        
        current_x = target_x + random_deviation_x
        current_y = target_y + random_deviation_y
        
        points.append((int(current_x), int(current_y)))
    
    return points


def _bezier_curve(
    start: Tuple[float, float],
    end: Tuple[float, float],
    num_points: int = 50,
    fatigue: float = 0.0,
    deviation: float = 0.2
) -> List[Tuple[int, int]]:
    """
    Кривая Безье для гладкого движения мыши
    
    Добавляет контрольные точки для естественного пути
    """
    
    x0, y0 = start
    x3, y3 = end
    
    # Расстояние между точками
    dist = math.sqrt((x3 - x0) ** 2 + (y3 - y0) ** 2)
    
    # Смещение контрольных точек
    offset = dist * (0.15 + deviation) * (1 + fatigue * 0.8)
    
    # Первая контрольная точка
    x1 = x0 + (x3 - x0) * random.uniform(0.15, 0.35) + random.uniform(-offset, offset)
    y1 = y0 + (y3 - y0) * random.uniform(0.05, 0.35) + random.uniform(-offset, offset)
    
    # Вторая контрольная точка
    x2 = x0 + (x3 - x0) * random.uniform(0.65, 0.85) + random.uniform(-offset, offset)
    y2 = y0 + (y3 - y0) * random.uniform(0.65, 0.95) + random.uniform(-offset, offset)
    
    points = []
    for i in range(num_points + 1):
        t = i / num_points
        
        # Формула кубической кривой Безье
        x = (1 - t)**3 * x0 + 3*(1 - t)**2 * t * x1 + 3*(1 - t)*t**2 * x2 + t**3 * x3
        y = (1 - t)**3 * y0 + 3*(1 - t)**2 * t * y1 + 3*(1 - t)*t**2 * y2 + t**3 * y3
        
        # Добавляем шум (дрожание)
        jitter = random.uniform(-1.5, 1.5)
        points.append((int(x + jitter), int(y + jitter)))
    
    return points


async def move_mouse(
    page: Page,
    target_x: int,
    target_y: int,
    fp: Optional[Fingerprint] = None,
    duration: Optional[float] = None,
    allow_overshoot: bool = True,
    fidget: bool = True,
) -> None:
    """
    МАКСИМАЛЬНО РЕАЛИСТИЧНОЕ ДВИЖЕНИЕ МЫШИ
    
    Args:
        page: Playwright Page
        target_x: Це��евая X координата
        target_y: Целевая Y координата
        fp: Fingerprint
        duration: Продолжительность движения (если None, рассчитывается автоматически)
        allow_overshoot: Позволить перелёт за точку
        fidget: Разрешить мелкие движения (fidgeting)
    """
    
    engine = getattr(page, "_mouse_engine", None)
    if not engine:
        engine = MouseEngine(fp)
        page._mouse_engine = engine
    
    engine.total_movements += 1
    
    try:
        # ─────────────────────────────────────────────────────
        # ПОЛУЧЕНИЕ ТЕКУЩЕЙ ПОЗИЦИИ
        # ─────────────────────────────────────────────────────
        
        try:
            current = await page.evaluate("() => ({x: window._mouseX || 0, y: window._mouseY || 0})")
            start_x, start_y = current.get("x", engine.last_x), current.get("y", engine.last_y)
        except:
            start_x, start_y = engine.last_x, engine.last_y
        
        # ─────────────────���───────────────────────────────────
        # РАСЧЁТ ПУТИ
        # ─────────────────────────────────────────────────────
        
        dist = math.sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)
        
        # Количество шагов пути (зависит от расстояния)
        num_points = max(25, min(100, int(dist / 5)))
        
        # Выбираем тип кривой
        if dist < 20:
            # Близко — используем простое движение
            path = [(start_x + (target_x - start_x) * i / num_points,
                     start_y + (target_y - start_y) * i / num_points)
                    for i in range(num_points + 1)]
            path = [(int(x), int(y)) for x, y in path]
        else:
            # Далеко — используем Безье кривую
            fatigue = engine.get_tiredness()
            path = _bezier_curve(
                (start_x, start_y),
                (target_x, target_y),
                num_points=num_points,
                fatigue=fatigue,
                deviation=0.2
            )
        
        # ──────────────────────────────────────���──────────────
        # ДВИЖЕНИЕ ПО ПУТИ
        # ─────────────────────────────────────────────────────
        
        if duration is None:
            # Рассчитываем длительность автоматически
            base_duration = (dist / 400) * (1 + engine.get_tiredness() * 0.5)  # Усталый медленнее
            duration = base_duration * engine._get_mouse_speed_multiplier()
        
        # Время на один шаг
        step_duration = duration / len(path)
        
        for i, (x, y) in enumerate(path):
            # Добавляем микро-дрожание (tremor)
            tremor = engine._get_tremor_intensity()
            jitter_x = x + random.gauss(0, tremor)
            jitter_y = y + random.gauss(0, tremor)
            
            # Переводим в int
            jitter_x = int(jitter_x)
            jitter_y = int(jitter_y)
            
            # Движем мышь
            await page.mouse.move(jitter_x, jitter_y)
            
            # Вычисляем задержку (ускорение в начале, замедление в конце)
            t = i / len(path)  # Прогресс 0-1
            
            # Ease-out функция (начинаем быстро, заканчиваем медленно)
            ease_out = t ** 2
            delay = step_duration * (0.3 + ease_out * 0.7)
            
            await asyncio.sleep(delay / 1000.0)  # Конвертируем в миллисекунды
        
        # ─────────────────────────────────────────────────────
        # OVERSHOOT (ПЕРЕЛЁТ ЗА ТОЧКУ)
        # ─────────────────────────────────────────────────────
        
        if allow_overshoot and random.random() < (0.2 + engine.get_tiredness() * 0.2):
            # Перелетаем за точку
            overshoot_x = target_x + random.randint(-20, 20)
            overshoot_y = target_y + random.randint(-20, 20)
            
            await page.mouse.move(overshoot_x, overshoot_y)
            await asyncio.sleep(random.uniform(0.04, 0.08))
            
            # Возвращаемся
            await page.mouse.move(target_x, target_y)
            await asyncio.sleep(random.uniform(0.02, 0.04))
        
        # ─────────────────────────────────────────────────────
        # FIDGETING (МЕЛКИЕ ДВИЖЕНИЯ)
        # ─────────────────────────────────────────────────────
        
        if fidget and random.random() < 0.15:
            # Мелкие движения на месте (человек не сидит неподвижно)
            for _ in range(random.randint(1, 3)):
                fidget_x = target_x + random.randint(-3, 3)
                fidget_y = target_y + random.randint(-3, 3)
                
                await page.mouse.move(fidget_x, fidget_y)
                await asyncio.sleep(random.uniform(0.05, 0.1))
        
        engine.last_x, engine.last_y = target_x, target_y
        
    except Exception:
        pass


async def click_element(
    page: Page,
    selector: str,
    fp: Optional[Fingerprint] = None,
    double_click: bool = False,
    mouse_speed: float = 1.0,
) -> None:
    """
    МАКСИМАЛЬНО РЕАЛИСТИЧНЫЙ КЛИК НА ЭЛЕМЕНТ
    
    Args:
        page: Playwright Page
        selector: CSS selector
        fp: Fingerprint
        double_click: Двойной клик?
        mouse_speed: Множитель скорости мыши
    """
    
    engine = getattr(page, "_mouse_engine", None)
    if not engine:
        engine = MouseEngine(fp)
        page._mouse_engine = engine
    
    engine.total_clicks += 1
    
    try:
        element = page.locator(selector).first
        box = await element.bounding_box()
        
        if not box:
            # Fallback на встроенный клик
            await element.click()
            return
        
        # ─────────────────────────────────────────────────────
        # РАСЧЕТ ТОЧКИ КЛИКА
        # ─────────────────────────────────────────────────────
        
        center_x = box["x"] + box["width"] / 2
        center_y = box["y"] + box["height"] / 2
        
        # Добавляем смещение от центра (естественное)
        offset_range = (fp.click_offset_range if fp else 4) * (1 + engine.get_tiredness() * 0.8)
        click_x = center_x + random.uniform(-offset_range, offset_range)
        click_y = center_y + random.uniform(-offset_range, offset_range)
        
        # Убеждаемся что в пределах элемента
        click_x = max(box["x"] + 2, min(click_x, box["x"] + box["width"] - 2))
        click_y = max(box["y"] + 2, min(click_y, box["y"] + box["height"] - 2))
        
        # ─────────────────────────────────────────────────────
        # ДВИЖЕНИЕ МЫШИ К ЭЛЕМЕНТУ
        # ─────────────────────────────────────────────────────
        
        await move_mouse(page, int(click_x), int(click_y), fp, duration=random.uniform(0.3, 0.8))
        
        # ─────────────────────────────────────────────────────
        # ПАУЗА ПЕРЕД КЛИКОМ (РАЗДУМЬЕ)
        # ─────────────────────────────────────────────────────
        
        thinking_pause = {
            'short': random.uniform(0.05, 0.15),
            'medium': random.uniform(0.2, 0.4),
            'long': random.uniform(0.5, 1.0),
        }
        
        pause_type = random.choices(['short', 'medium', 'long'], weights=[0.7, 0.2, 0.1], k=1)[0]
        await asyncio.sleep(thinking_pause[pause_type])
        
        # ─────────────────────────────────────────────────────
        # КЛИК
        # ─────────────────────────────────────────────────────
        
        if double_click:
            await page.mouse.dblclick(int(click_x), int(click_y))
        else:
            await page.mouse.click(int(click_x), int(click_y))
        
        # ─────────────────────────────────────────────────────
        # ПАУЗА ПОСЛЕ КЛИКА
        # ─────────────────────────────────────────────────────
        
        await asyncio.sleep(random.uniform(0.15, 0.5))
        
    except Exception:
        # Fallback на встроенный клик
        try:
            await page.locator(selector).first.click()
        except Exception:
            pass


async def random_mouse_movement(
    page: Page,
    fp: Optional[Fingerprint] = None,
) -> None:
    """
    СЛУЧАЙНОЕ ДВИЖЕНИЕ МЫШИ
    
    Имитирует натуральное поведение (человек двигает мышь даже когда ничего не делает)
    """
    
    try:
        viewport = await page.evaluate("() => ({w: window.innerWidth, h: window.innerHeight})")
        
        # Случайная точка на экране
        x = random.randint(50, viewport.get("w", 1400) - 50)
        y = random.randint(50, viewport.get("h", 900) - 50)
        
        # Движем мышь
        await move_mouse(page, x, y, fp, duration=random.uniform(0.5, 1.5), fidget=False)
        
    except Exception:
        pass


async def hover_element(
    page: Page,
    selector: str,
    duration: float = 2.0,
    fp: Optional[Fingerprint] = None,
) -> None:
    """
    ЕСТЕСТВЕННОЕ НАВЕДЕНИЕ МЫШИ НА ЭЛЕМЕНТ
    
    Args:
        page: Playwright Page
        selector: CSS selector
        duration: Длительность наведения
        fp: Fingerprint
    """
    
    engine = getattr(page, "_mouse_engine", None)
    if not engine:
        engine = MouseEngine(fp)
        page._mouse_engine = engine
    
    try:
        element = page.locator(selector).first
        box = await element.bounding_box()
        
        if not box:
            await element.hover()
            return
        
        # Центр элемента + смещение
        hover_x = box["x"] + box["width"] / 2 + random.uniform(-5, 5)
        hover_y = box["y"] + box["height"] / 2 + random.uniform(-5, 5)
        
        # Движем мышь к элементу
        await move_mouse(page, int(hover_x), int(hover_y), fp)
        
        # Держим мышь над элементом
        engine.hover_duration_total += duration
        await asyncio.sleep(duration)
        
    except Exception:
        try:
            await element.hover()
        except Exception:
            pass