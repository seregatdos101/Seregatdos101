# core/avito/detector.py
"""
🔍 DETECTOR — Детектирование угроз (капча, бан, блокировка)
ИСПРАВЛЕНИЯ:
✅ Улучшенное детектирование капч
✅ Лучшая обработка ошибок
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass

from playwright.async_api import Page


class ThreatType(Enum):
    """Типы угроз"""
    NONE = "none"
    CAPTCHA = "captcha"
    BAN = "ban"
    BLOCK = "block"
    VERIFICATION = "verification"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


@dataclass
class ThreatInfo:
    """Информация об угрозе"""
    type: ThreatType
    is_safe: bool
    message: str = ""
    action_needed: str = ""


async def check_threats(page: Page) -> Optional[ThreatInfo]:
    """Проверить наличие угроз на странице"""
    try:
        # Получить текст и URL страницы
        text = (await page.text_content("body") or "").lower()
        url = page.url.lower()
        
        # ──── КАПЧА ────
        try:
            captcha_elements = [
                'iframe[src*="captcha"]',
                'iframe[title="recaptcha"]',
                'iframe[title="reCAPTCHA"]',
                '.g-recaptcha',
                '[data-marker="captcha"]',
            ]
            
            for selector in captcha_elements:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        return ThreatInfo(
                            type=ThreatType.CAPTCHA,
                            is_safe=False,
                            message="Обнаружена капча",
                            action_needed="Решите капчу вручную"
                        )
                except Exception:
                    pass
        except Exception:
            pass
        
        # ──── БАН ────
        ban_keywords = [
            "аккаунт заблокирован",
            "account blocked",
            "ваш аккаунт удален",
            "your account has been deleted",
            "banned",
            "заблокирован",
        ]
        
        for keyword in ban_keywords:
            if keyword in text:
                return ThreatInfo(
                    type=ThreatType.BAN,
                    is_safe=False,
                    message="Аккаунт заблокирован",
                    action_needed="Требуется новый аккаунт"
                )
        
        # ──── БЛОКИРОВКА IP ────
        block_keywords = [
            "ip заблокирован",
            "ip blocked",
            "доступ запрещен",
            "access denied",
            "блокирова",
            "429",
            "too many requests",
        ]
        
        for keyword in block_keywords:
            if keyword in text:
                return ThreatInfo(
                    type=ThreatType.BLOCK,
                    is_safe=False,
                    message="IP адрес заблокирован",
                    action_needed="Используйте другой прокси"
                )
        
        # ──── ВЕРИФИКАЦИЯ ────
        verify_keywords = [
            "подтвердить",
            "verify",
            "verify your",
            "verification",
            "верификация",
            "подтверждение",
        ]
        
        for keyword in verify_keywords:
            if keyword in text and "login" not in text:
                return ThreatInfo(
                    type=ThreatType.VERIFICATION,
                    is_safe=False,
                    message="Требуется верификация",
                    action_needed="Пройдите верификацию"
                )
        
        # ──── RATE LIMIT ────
        if "429" in text or "too many requests" in text.lower():
            return ThreatInfo(
                type=ThreatType.RATE_LIMIT,
                is_safe=False,
                message="Rate limit достигнут",
                action_needed="Подождите перед следующим действием"
            )
        
        # ──── ВСЁ ОК ────
        return ThreatInfo(
            type=ThreatType.NONE,
            is_safe=True,
            message="Угроз не обнаружено"
        )
        
    except Exception as e:
        return ThreatInfo(
            type=ThreatType.UNKNOWN,
            is_safe=False,
            message=f"Ошибка проверки: {e}",
            action_needed="Попробуйте снова"
        )