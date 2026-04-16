# core/avito/login.py
"""
🔐 LOGIN ENGINE 2030 — АВТОРИЗАЦИЯ НА AVITO (ИСПРАВЛЕННАЯ)
Вход с сохранённой сессией, SMS, автоматическое определение статуса
Production ready, без сокращений
"""

import asyncio
from typing import Optional
from colorama import Fore, Style


async def login_with_session(
    page,
    account_id: str,
    navigator,
    logger,
    timeout: int = 30
) -> bool:
    """
    Попытка входа с сохранённой сессией
    
    ВАЖНО: launcher.py уже загрузил главную страницу!
    Здесь только ПРОВЕРЯЕМ авторизацию БЕЗ повторной навигации
    
    Args:
        page: Playwright Page
        account_id: ID аккаунта
        navigator: AvitoNavigator
        logger: Logger
        timeout: Таймаут в секундах
        
    Returns:
        True если авторизированы, False если нужна SMS
    """
    
    try:
        logger.info(account_id, "Проверяю сохранённую сессию")
        
        # ─────────────────────────────────────────────────────
        # ВАЖНО: НИКАКОЙ НАВИГАЦИИ! launcher.py уже загрузил страницу!
        # ─────────────────────────────────────────────────────
        
        await asyncio.sleep(2)
        
        # ─────────────────────────────────────────────────────
        # СПОСОБ 1: Проверяем кнопку профиля
        # ─────────────────────────────────────────────────────
        
        try:
            profile_button = page.locator('[data-marker="user-profile-button"]')
            if await profile_button.is_visible(timeout=3000):
                logger.success(account_id, "✅ Авторизирован (метод 1: кнопка профиля)")
                return True
        except Exception:
            pass
        
        # ─────────────────────────────────────────────────────
        # СПОСОБ 2: Проверяем URL (должен быть не login)
        # ─────────────────────────────────────────────────────
        
        try:
            current_url = page.url
            if "login" not in current_url.lower() and "avito.ru" in current_url.lower():
                logger.success(account_id, "✅ Авторизирован (метод 2: URL)")
                return True
        except Exception:
            pass
        
        # ─────────────────────────────────────────────────────
        # СПОСОБ 3: Проверяем элементы профиля
        # ─────────────────────────────────────────────────────
        
        try:
            user_name = page.locator('[data-marker="user-name"]')
            if await user_name.is_visible(timeout=2000):
                logger.success(account_id, "✅ Авторизирован (метод 3: имя пользователя)")
                return True
        except Exception:
            pass
        
        logger.warning(account_id, "⚠️ Не авторизирован, нужна SMS")
        return False
    
    except Exception as e:
        logger.error(account_id, f"Ошибка проверки сессии: {e}", severity="MEDIUM")
        return False


async def login_with_sms(
    page,
    account_id: str,
    phone: str,
    navigator,
    logger,
    notifier,
    fp,
    timeout: int = 120
) -> bool:
    """
    Вход через SMS с АВТОМАТИЧЕСКИМ ОПРЕДЕЛЕНИЕМ СТАТУСА
    
    ВАЖНО: launcher.py уже загрузил главную страницу!
    Здесь только ЛОГИРУЕМСЯ, НЕ повторяя навигацию
    
    Процесс:
    1. Переходим на страницу логина (только если нужно)
    2. Вводим номер телефона
    3. Запрашиваем SMS
    4. ЖДЁМ АВТОМАТИЧЕСКОГО ВВОДА КОДА или вводим вручную
    5. Проверяем авторизацию
    
    Args:
        page: Playwright Page
        account_id: ID аккаунта
        phone: Номер телефона
        navigator: AvitoNavigator
        logger: Logger
        notifier: TelegramNotifier
        fp: Fingerprint
        timeout: Таймаут ввода кода в секундах
        
    Returns:
        True если авторизированы, False если ошибка
    """
    
    try:
        logger.info(account_id, f"Начинаю вход через SMS: {phone}")
        
        # ─────────────────────────────────────────────────────
        # 1. ПЕРЕХОДИМ НА СТРАНИЦУ ЛОГИНА (ТОЛЬКО ЕСЛИ НУЖНО)
        # ─────────────────────────────────────────────────────
        
        current_url = page.url
        
        # Если уже на логине или профиле, не переходим
        if "profile" not in current_url.lower() and "login" not in current_url.lower():
            try:
                logger.info(account_id, "Переходю на страницу профиля...")
                await asyncio.wait_for(
                    page.goto(
                        "https://www.avito.ru/profile",
                        wait_until="domcontentloaded",
                        timeout=15000
                    ),
                    timeout=20
                )
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(account_id, f"⚠️ Ошибка при переходе на профиль: {str(e)[:80]}")
                # Продолжаем, возможно страница там
        
        # ─────────────────────────────────────────────────────
        # 2. ПРОВЕРЯЕМ, МОЖЕТ ЛИ БЫТЬ УЖЕ АВТОРИЗИРОВАН
        # ─────────────────────────────────────────────────────
        
        try:
            profile_button = page.locator('[data-marker="user-profile-button"]')
            if await profile_button.is_visible(timeout=2000):
                logger.success(account_id, "✅ Уже авторизирован!")
                return True
        except Exception:
            pass
        
        # ─────────────────────────────────────────────────────
        # 3. ИЩЕМ И НАЖИМАЕМ КНОПКУ ВХОДА
        # ─────────────────────────────────────────────────────
        
        login_button = None
        
        # Вариант 1: "Войти"
        try:
            login_button = page.locator("button:has-text('Войти')").first
            if await login_button.is_visible(timeout=2000):
                await login_button.click()
                await asyncio.sleep(1)
                logger.info(account_id, "Нажал кнопку 'Войти' (вариант 1)")
        except Exception:
            pass
        
        # Вариант 2: "Мобильный номер"
        if not login_button or not await login_button.is_visible(timeout=500):
            try:
                phone_btn = page.locator("button:has-text('Мобильный номер')").first
                if await phone_btn.is_visible(timeout=2000):
                    await phone_btn.click()
                    await asyncio.sleep(1)
                    logger.info(account_id, "Нажал кнопку 'Мобильный номер' (вариант 2)")
            except Exception:
                pass
        
        # ─────────────────────────────────────────────────────
        # 4. ВВОДИМ НОМЕР ТЕЛЕФОНА
        # ─────────────────────────────────────────────────────
        
        phone_input = page.locator('input[type="tel"]').first
        
        for attempt in range(3):
            try:
                if await phone_input.is_visible(timeout=2000):
                    await phone_input.click()
                    await asyncio.sleep(0.3)
                    
                    # Очищаем
                    await phone_input.press("Control+A")
                    await asyncio.sleep(0.1)
                    await phone_input.press("Delete")
                    await asyncio.sleep(0.2)
                    
                    # Печатаем номер
                    await phone_input.type(phone, delay=50)
                    await asyncio.sleep(0.5)
                    
                    logger.info(account_id, f"✅ Ввёл номер: {phone}")
                    break
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                else:
                    logger.warning(account_id, f"Не удалось ввести номер: {e}")
                    return False
        
        # ─────────────────────────────────────────────────────
        # 5. НАЖИМАЕМ КНОПКУ "ОТПРАВИТЬ КОД"
        # ─────────────────────────────────────────────────────
        
        send_code_button = None
        
        # Вариант 1: "Отправить код"
        try:
            send_code_button = page.locator("button:has-text('Отправить код')").first
            if await send_code_button.is_visible(timeout=3000):
                await send_code_button.click()
                await asyncio.sleep(2)
                logger.info(account_id, "Нажал 'Отправить код'")
        except Exception:
            pass
        
        # Вариант 2: "Продолжить"
        if not send_code_button or not await send_code_button.is_visible(timeout=500):
            try:
                continue_btn = page.locator("button:has-text('Продолжить')").first
                if await continue_btn.is_visible(timeout=3000):
                    await continue_btn.click()
                    await asyncio.sleep(2)
                    logger.info(account_id, "Нажал 'Продолжить'")
            except Exception:
                pass
        
        # ─────────────────────────────────────────────────────
        # 6. ЖДЁМ ВВОДА КОДА (АВТОМАТИЧЕСКИ ИЛИ ВРУЧНУЮ)
        # ─────────────────────────────────────────────────────
        
        print(f"\n  {Fore.CYAN}╔════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}                                                        {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}  📱 SMS КОД ОЖИДАЕТСЯ                                 {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}  Avito может автоматически заполнить код             {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}  Или введите вручную в браузере                      {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}  Ожидание: {timeout} секунд                               {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}║{Style.RESET_ALL}                                                        {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}╚════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        
        if notifier:
            try:
                msg = f"""
📱 *ТРЕБУЕТСЯ SMS КОД*

📍 Аккаунт: `{account_id}`
📞 Телефон: {phone}

Код отправлен на телефон.
Введите код в браузере или он будет заполнен автоматически.

⏳ Ожидание: {timeout} сек
"""
                await notifier.send_message(msg, parse_mode="Markdown")
            except Exception:
                pass
        
        # ───────────────��─────────────────────────────────────
        # 7. ЖДЁМ ЗАПОЛНЕНИЯ КОДА
        # ─────────────────────────────────────────────────────
        
        start_time = asyncio.get_event_loop().time()
        code_filled = False
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                # Проверяем наличие заполненного кода
                code_inputs = await page.locator('input[type="text"]').all()
                
                for code_input in code_inputs:
                    try:
                        code_value = await code_input.input_value()
                        
                        # Если код заполнен (4+ символа)
                        if code_value and len(code_value) >= 4:
                            logger.success(account_id, f"✅ Код обнаружен: {code_value}")
                            code_filled = True
                            break
                    except Exception:
                        pass
                
                if code_filled:
                    break
                
                # Проверяем, авторизирован ли уже
                profile_button = page.locator('[data-marker="user-profile-button"]')
                if await profile_button.is_visible(timeout=500):
                    logger.success(account_id, "✅ Авторизирован автоматически!")
                    code_filled = True
                    break
                
                await asyncio.sleep(1)
            
            except Exception:
                await asyncio.sleep(1)
        
        # ─────────────────────────────────────────────────────
        # 8. ПРОВЕРЯЕМ АВТОРИЗАЦИЮ
        # ─────────────────────────────────────────────────────
        
        await asyncio.sleep(2)
        
        # Попытка 1: Кнопка профиля
        try:
            profile_button = page.locator('[data-marker="user-profile-button"]')
            if await profile_button.is_visible(timeout=3000):
                logger.success(account_id, "✅ Вход успешен (кнопка профиля)!")
                return True
        except Exception:
            pass
        
        # Попытка 2: URL
        current_url = page.url
        if "profile" in current_url and "login" not in current_url:
            logger.success(account_id, "✅ Вход успешен (URL check)!")
            return True
        
        # Попытка 3: Имя пользователя
        try:
            user_name = page.locator('[data-marker="user-name"]')
            if await user_name.is_visible(timeout=2000):
                logger.success(account_id, "✅ Вход успешен (имя пользователя)!")
                return True
        except Exception:
            pass
        
        # ─────────────────────────────────────────────────────
        # 9. ЕСЛИ КОД НЕ БЫЛ ЗАПОЛНЕН
        # ─────────────────────────────────────────────────────
        
        if not code_filled:
            print(f"\n  {Fore.YELLOW}⏱️ Таймаут! Код не был заполнен за {timeout} секунд{Style.RESET_ALL}")
            logger.warning(account_id, "Код не заполнен за отведённое время")
            return False
        
        logger.warning(account_id, "Авторизация не удалась")
        return False
    
    except Exception as e:
        logger.error(account_id, f"SMS login ошибка: {e}", severity="HIGH")
        return False