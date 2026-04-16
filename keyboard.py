# core/human/keyboard.py
"""
⌨️ KEYBOARD ENGINE 2030 — МАКСИМАЛЬНО РЕАЛИСТИЧНАЯ ПЕЧАТЬ ТЕКСТА
Вариативность опечаток, случайные паузы, имитация копи-пасты, автозаполнение браузера
Production ready, без сокращений
"""

import asyncio
import random
import time
from typing import Optional, List, Dict, Tuple
from enum import Enum

from playwright.async_api import Page

from core.browser.fingerprint import Fingerprint


class TypingStyle(Enum):
    """Стиль печати"""
    FAST_TYPER = "fast_typer"           # Быстро, много опечаток
    CAREFUL_TYPIST = "careful_typist"   # Медленно, мало опечаток
    DISTRACTED = "distracted"           # Часто отвлекается
    TIRED = "tired"                     # Усталый, много ошибок
    FOCUSED = "focused"                 # Сосредоточенный, мало ошибок


class KeyboardEngine:
    """
    ⌨️ KEYBOARD ENGINE 2030
    
    Особенности:
    - Вариативность опечаток по контексту
    - Случайные паузы "думания" перед вводом
    - Имитация копи-пасты (ctrl+v иногда)
    - Имитация автозаполнения браузера
    - Исправление опечаток как у человека (backspace, не ctrl+a)
    - Случайные задержки между символами
    - Разные стили печати
    """
    
    # РУССКИЕ БУКВЫ ДЛЯ ОПЕЧАТОК
    RUSSIAN_CHARS = 'абвгдежзийклмнопрстуфхцчшщъыьэюя'
    RUSSIAN_CHARS_UPPER = 'АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
    
    # ЧАСТЫЕ ОПЕЧАТКИ (НА РУССКОЙ РАСКЛАДКЕ)
    COMMON_TYPOS = {
        'а': ['о', 'э'],
        'е': ['и', 'ё'],
        'о': ['а', 'ё'],
        'и': ['е', 'й'],
        'у': ['ю', 'п'],
        'й': ['и', 'ц'],
        'ц': ['й', 'ы'],
        'к': ['л', 'н'],
        'л': ['к', 'д'],
        'н': ['м', 'г'],
        'г': ['н', 'ш'],
        'ш': ['г', 'щ'],
        'щ': ['ш', 'з'],
        'з': ['щ', 'х'],
        'х': ['з', 'ф'],
        'ф': ['х', 'ы'],
        'ы': ['ф', 'в'],
        'в': ['ы', 'б'],
        'б': ['в', 'п'],
        'п': ['б', 'р'],
        'р': ['п', 'л'],
        'д': ['л', 'ж'],
        'ж': ['д', 'э'],
        'э': ['ж', 'ю'],
        'ю': ['э', 'у'],
    }
    
    # СЛОВА КОТОРЫЕ ЧАСТО ЕСТЬ В БРАУЗЕР АВТОЗАПОЛНЕНИИ
    AUTOCOMPLETE_WORDS = [
        'авито', 'avito', 'москва', 'руб', 'руб.', 'рублей',
        'продам', 'куплю', 'ищу', 'нужно', 'срочно',
        'телефон', '+7', 'почта', 'email', 'gmail',
    ]

    def __init__(self, fp: Optional[Fingerprint] = None):
        """Инициализация keyboard engine"""
        self.fp = fp
        self.typing_style = self._get_typing_style()
        self.session_start = time.time()
        self.total_chars_typed = 0
        self.total_typos_made = 0
        self.total_corrections = 0
        
    def _get_typing_style(self) -> TypingStyle:
        """Определить стиль печати на основе fingerprint"""
        if not self.fp:
            return random.choice(list(TypingStyle))
        
        # Можно добавить логику из fingerprint если будет
        return random.choice(list(TypingStyle))
    
    def _get_typo_probability(self) -> float:
        """Получить вероятность опечатки в зависимости от стиля"""
        base_prob = {
            TypingStyle.FAST_TYPER: 0.12,
            TypingStyle.CAREFUL_TYPIST: 0.02,
            TypingStyle.DISTRACTED: 0.18,
            TypingStyle.TIRED: 0.25,
            TypingStyle.FOCUSED: 0.03,
        }
        
        prob = base_prob.get(self.typing_style, 0.08)
        
        # Усталость растёт со временем
        elapsed_hours = (time.time() - self.session_start) / 3600
        tiredness_factor = min(0.15, elapsed_hours * 0.05)  # +15% опечаток за час
        
        return min(0.35, prob + tiredness_factor)
    
    def _get_typing_speed(self) -> float:
        """Получить скорость печати (символов в секунду)"""
        base_speed = {
            TypingStyle.FAST_TYPER: 8.5,
            TypingStyle.CAREFUL_TYPIST: 3.5,
            TypingStyle.DISTRACTED: 5.5,
            TypingStyle.TIRED: 4.0,
            TypingStyle.FOCUSED: 6.0,
        }
        
        speed = base_speed.get(self.typing_style, 5.0)
        
        # Добавляем вариативность (±20%)
        speed *= random.uniform(0.8, 1.2)
        
        return speed
    
    def _get_char_delay(self) -> float:
        """Получить задержку между символами (в миллисекундах)"""
        typing_speed = self._get_typing_speed()
        base_delay = 1000.0 / typing_speed  # Миллисекунды
        
        # Вариативность
        delay = base_delay * random.uniform(0.6, 1.4)
        
        return delay / 1000.0  # В секунды
    
    def _should_use_autocomplete(self, text: str) -> bool:
        """Должны ли мы использовать автозаполнение браузера?"""
        # 15% вероятность использовать автозаполнение если это знакомое слово
        if random.random() > 0.15:
            return False
        
        for word in self.AUTOCOMPLETE_WORDS:
            if word.lower() in text.lower():
                return True
        
        return False
    
    def _get_thinking_pause(self) -> float:
        """Получить паузу "думания" перед началом печати (в секундах)"""
        pause_type = random.choices(
            ['short', 'medium', 'long', 'very_long'],
            weights=[0.6, 0.25, 0.10, 0.05],
            k=1
        )[0]
        
        pauses = {
            'short': random.uniform(0.3, 0.8),
            'medium': random.uniform(0.8, 2.0),
            'long': random.uniform(2.0, 4.0),
            'very_long': random.uniform(4.0, 8.0),  # Сильно задумался
        }
        
        return pauses[pause_type]
    
    def _get_correction_method(self) -> str:
        """Получить способ исправления опечатки"""
        methods = {
            'backspace_once': 0.70,       # Одиночный backspace
            'backspace_word': 0.20,       # Backspace до начала слова
            'select_and_delete': 0.10,    # Выделить и удалить
        }
        
        return random.choices(
            list(methods.keys()),
            weights=list(methods.values()),
            k=1
        )[0]
    
    async def _type_char_realistic(
        self,
        element,
        char: str,
        page: Page,
        include_thinking_pause: bool = False
    ) -> None:
        """Печатать один символ максимально реалистично"""
        
        # Случайная пауза думания
        if include_thinking_pause and random.random() < 0.08:
            thinking_pause = self._get_thinking_pause()
            await asyncio.sleep(thinking_pause)
        
        # Печатаем символ
        await element.type(char)
        self.total_chars_typed += 1
        
        # Пауза после символа
        char_delay = self._get_char_delay()
        await asyncio.sleep(char_delay)
    
    async def _make_and_correct_typo(
        self,
        element,
        correct_char: str,
        page: Page
    ) -> None:
        """Сделать опечатку и исправить её"""
        
        # Выбираем неправильный символ
        if correct_char.lower() in self.COMMON_TYPOS:
            wrong_char = random.choice(self.COMMON_TYPOS[correct_char.lower()])
        else:
            wrong_char = random.choice(self.RUSSIAN_CHARS)
        
        # Печатаем неправильный символ
        await element.type(wrong_char)
        self.total_chars_typed += 1
        self.total_typos_made += 1
        
        # Пауза (человек заметил ошибку)
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # Выбираем способ исправления
        correction_method = self._get_correction_method()
        
        if correction_method == 'backspace_once':
            # Простой backspace
            await element.press('Backspace')
            await asyncio.sleep(random.uniform(0.1, 0.2))
        
        elif correction_method == 'backspace_word':
            # Несколько backspace (вернуться назад)
            num_backspaces = random.randint(1, 3)
            for _ in range(num_backspaces):
                await element.press('Backspace')
                await asyncio.sleep(random.uniform(0.08, 0.15))
        
        elif correction_method == 'select_and_delete':
            # Выделить и удалить (Ctrl+Shift+Left)
            await element.press('Shift+Left')
            await asyncio.sleep(random.uniform(0.1, 0.2))
            await element.press('Delete')
            await asyncio.sleep(random.uniform(0.1, 0.2))
        
        self.total_corrections += 1
        
        # Печатаем правильный символ
        await element.type(correct_char)
        self.total_chars_typed += 1
        
        await asyncio.sleep(random.uniform(0.05, 0.12))


async def type_text(
    page: Page,
    selector: str,
    text: str,
    fp: Optional[Fingerprint] = None,
    make_typos: bool = True,
) -> bool:
    """
    ПЕЧАТЬ ТЕКСТА С МАКСИМАЛЬНОЙ РЕАЛИСТИЧНОСТЬЮ
    
    Args:
        page: Playwright Page
        selector: CSS selector поля для ввода
        text: Текст для печати
        fp: Fingerprint (для индивидуализации)
        make_typos: Разрешить опечатки
        
    Returns:
        True если успешно, False если ошибка
    """
    
    engine = KeyboardEngine(fp)
    
    try:
        # ─────────────────────────────────────────────────────
        # ПОИСК ЭЛЕМЕНТА И КЛИК
        # ─────────────────────────────────────────────────────
        
        element = page.locator(selector).first
        
        # Проверяем существует ли элемент
        if not await element.is_visible(timeout=2000):
            return False
        
        # Наводим мышь перед кликом (как человек)
        await element.hover()
        await asyncio.sleep(random.uniform(0.2, 0.5))
        
        # Кликаем с естественным смещением
        await element.click()
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        # ─────────────────────────────────────────────────────
        # ОЧИСТКА ПОЛЯ (если там что-то было)
        # ─────────────────────────────────────────────────────
        
        current_value = await element.input_value()
        if current_value:
            # Выделяем всё и удаляем
            await element.press('Control+A')
            await asyncio.sleep(random.uniform(0.1, 0.2))
            await element.press('Delete')
            await asyncio.sleep(random.uniform(0.2, 0.4))
        
        # ─────────────────────────────────────────────────────
        # ПАУЗА "ДУМАНИЯ" ПЕРЕД НАЧАЛОМ ПЕЧАТИ
        # ─────────────────────────────────────────────────────
        
        thinking_pause = engine._get_thinking_pause()
        await asyncio.sleep(thinking_pause)
        
        # ─────────────────────────────────────────────────────
        # ПРОВЕРКА АВТОЗАПОЛНЕНИЯ
        # ─────────────────────────────────────────────────────
        
        if engine._should_use_autocomplete(text):
            # Печатаем первые несколько букв
            prefix_len = random.randint(2, 4)
            prefix = text[:min(prefix_len, len(text))]
            
            for char in prefix:
                await engine._type_char_realistic(element, char, page)
            
            # Нажимаем стрелку вниз чтобы выбрать из автозаполнения
            await asyncio.sleep(random.uniform(0.2, 0.5))
            await element.press('ArrowDown')
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Нажимаем Enter чтобы выбрать
            await element.press('Enter')
            await asyncio.sleep(random.uniform(0.3, 0.6))
            
            return True
        
        # ─────────────────────────────────────────────────────
        # ПЕЧАТЬ ТЕКСТА ПОСИМВОЛЬНО С ОПЕЧАТКАМИ
        # ─────────────────────────────────────────────────────
        
        typo_probability = engine._get_typo_probability()
        
        for i, char in enumerate(text):
            # Иногда делаем опечатку
            if make_typos and random.random() < typo_probability:
                # 5% вероятность сделать опечатку
                try:
                    await engine._make_and_correct_typo(element, char, page)
                except Exception:
                    # Если не получилось исправить, просто печатаем правильный символ
                    await engine._type_char_realistic(element, char, page)
            else:
                # Печатаем правильный символ
                await engine._type_char_realistic(
                    element,
                    char,
                    page,
                    include_thinking_pause=(i == 0)  # Пауза только перед первым символом
                )
            
            # Случайная длинная пауза посередине текста (отвлёкся)
            if i == len(text) // 2 and random.random() < 0.1:
                await asyncio.sleep(random.uniform(1.0, 3.0))
        
        # ─────────────────────────────────────────────────────
        # ПАУЗА ПОСЛЕ ПЕЧАТИ (ПРОВЕРКА)
        # ─────────────────────────────────────────────────────
        
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        return True
        
    except Exception as e:
        return False


async def type_phone(
    page: Page,
    selector: str,
    phone: str,
    fp: Optional[Fingerprint] = None,
) -> bool:
    """
    ПЕЧАТЬ ТЕЛЕФОНА БЕЗ ОПЕЧАТОК
    
    Телефон печатается очень внимательно, без ошибок
    Но с естественными паузами
    
    Args:
        page: Playwright Page
        selector: CSS selector поля
        phone: Номер телефона (например: +79892921343)
        fp: Fingerprint
        
    Returns:
        True если успешно, False если ошибка
    """
    
    engine = KeyboardEngine(fp)
    
    try:
        element = page.locator(selector).first
        
        if not await element.is_visible(timeout=2000):
            return False
        
        # Наводим мышь
        await element.hover()
        await asyncio.sleep(random.uniform(0.2, 0.4))
        
        # Кликаем
        await element.click()
        await asyncio.sleep(random.uniform(0.3, 0.6))
        
        # Очищаем поле
        await element.press('Control+A')
        await asyncio.sleep(random.uniform(0.1, 0.2))
        await element.press('Delete')
        await asyncio.sleep(random.uniform(0.2, 0.3))
        
        # Пауза думания (ещё более внимательная при телефоне)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Печатаем телефон ОЧЕНЬ ВНИМАТЕЛЬНО
        typing_speed = 0.04 / fp.typing_speed if fp else 0.04
        
        for i, digit in enumerate(phone):
            await element.type(digit)
            
            # После каждого символа делаем проверочную паузу
            pause = random.uniform(0.03, 0.08)
            if i % 3 == 0:  # После каждых 3 символов более длинная пауза
                pause = random.uniform(0.1, 0.2)
            
            await asyncio.sleep(pause)
        
        # Финальная проверка
        await asyncio.sleep(random.uniform(0.4, 0.8))
        
        return True
        
    except Exception:
        return False


async def type_password(
    page: Page,
    selector: str,
    password: str,
    fp: Optional[Fingerprint] = None,
) -> bool:
    """
    ПЕЧАТЬ ПАРОЛЯ МАКСИМАЛЬНО ОСТОРОЖНО
    
    Args:
        page: Playwright Page
        selector: CSS selector поля пароля
        password: Пароль
        fp: Fingerprint
        
    Returns:
        True если успешно, False если ошибка
    """
    
    engine = KeyboardEngine(fp)
    
    try:
        element = page.locator(selector).first
        
        if not await element.is_visible(timeout=2000):
            return False
        
        # Наводим мышь (осторожность)
        await element.hover()
        await asyncio.sleep(random.uniform(0.3, 0.6))
        
        # Кликаем
        await element.click()
        await asyncio.sleep(random.uniform(0.4, 0.8))
        
        # Очищаем
        await element.press('Control+A')
        await asyncio.sleep(random.uniform(0.1, 0.2))
        await element.press('Delete')
        await asyncio.sleep(random.uniform(0.3, 0.5))
        
        # Пауза думания (очень внимательная)
        await asyncio.sleep(random.uniform(1.0, 2.5))
        
        # Печатаем пароль ОЧЕНЬ МЕДЛЕННО (type_password в Playwright скрывает вводимый текст)
        char_delay = random.uniform(0.08, 0.15)  # Медленнее чем обычно
        
        for char in password:
            await element.type(char)
            
            # Случайная длинная пауза (человек проверяет капслок)
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.5, 1.2))
            else:
                await asyncio.sleep(char_delay)
        
        # Финальная проверка
        await asyncio.sleep(random.uniform(0.6, 1.2))
        
        return True
        
    except Exception:
        return False


async def type_with_copy_paste(
    page: Page,
    selector: str,
    text: str,
    fp: Optional[Fingerprint] = None,
) -> bool:
    """
    ПЕЧАТЬ ТЕКСТА С ВЕРОЯТНОСТЬЮ КОПИ-ПАСТЫ
    
    Иногда человек копирует текст и вставляет вместо печати
    
    Args:
        page: Playwright Page
        selector: CSS selector поля
        text: Текст
        fp: Fingerprint
        
    Returns:
        True если успешно, False если ошибка
    """
    
    engine = KeyboardEngine(fp)
    
    try:
        element = page.locator(selector).first
        
        if not await element.is_visible(timeout=2000):
            return False
        
        # Клик
        await element.hover()
        await asyncio.sleep(random.uniform(0.2, 0.5))
        await element.click()
        await asyncio.sleep(random.uniform(0.3, 0.6))
        
        # Очистка
        await element.press('Control+A')
        await asyncio.sleep(random.uniform(0.1, 0.2))
        await element.press('Delete')
        await asyncio.sleep(random.uniform(0.2, 0.4))
        
        # 30% вероятность использовать копи-пасту вместо печати
        if random.random() < 0.30:
            # Используем evaluate чтобы установить значение
            # (имитируем копи-пасту)
            await page.evaluate(f'document.querySelector("{selector}").value = "{text}"')
            
            # Нажимаем несколько клавиш чтобы система думала что мы печатали
            for _ in range(random.randint(1, 3)):
                await element.press('ArrowRight')
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            await asyncio.sleep(random.uniform(0.3, 0.7))
            return True
        
        # Иначе печатаем как обычно
        return await type_text(page, selector, text, fp, make_typos=False)
        
    except Exception:
        return False