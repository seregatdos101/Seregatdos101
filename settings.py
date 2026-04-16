# config/settings.py
"""
⚙️ SETTINGS 2030 — Полная конфигурация проекта из .env
ИСПРАВЛЕНИЯ И РАСШИРЕНИЯ:
✅ Полная поддержка всех параметров из .env
✅ Правильный парсинг аккаунтов и ��рокси
✅ Расширенная валидация
✅ Улучшенное логирование ошибок конфигурации
✅ Поддержка нескольких форматов прокси
✅ Правильная обработка тайм-зон и локализации
Production ready 2026
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Загружаем .env файл
load_dotenv(ENV_PATH)


def _parse_time(time_str: str) -> Tuple[int, int]:
    """
    Парсить время в формате HH:MM
    
    Args:
        time_str: Строка времени (например "23:00")
        
    Returns:
        Tuple (часы, минуты)
    """
    try:
        parts = time_str.strip().split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        
        # Валидация
        if not (0 <= hours < 24):
            raise ValueError(f"Часы должны быть от 0 до 23, получено: {hours}")
        if not (0 <= minutes < 60):
            raise ValueError(f"Минуты должны быть от 0 до 59, получено: {minutes}")
        
        return hours, minutes
    
    except Exception as e:
        print(f"⚠️ Ошибка парсинга времени '{time_str}': {e}")
        return 23, 7  # Default: 23:00 - 07:00


def _parse_accounts() -> Dict[str, dict]:
    """
    Парсить аккаунты из .env
    
    Поддерживаемые форматы:
    - ACCOUNT_1=+7XXXXXXXXXX:password
    - ACCOUNT_1_PHONE=+7XXXXXXXXXX
    - ACCOUNT_1_PASSWORD=password
    - ACCOUNT_1_NAME=Имя аккаунта
    """
    
    accounts = {}
    
    for i in range(1, 11):
        # Формат 1: ACCOUNT_N=phone:password
        raw = os.getenv(f"ACCOUNT_{i}", "").strip()
        
        if raw and ":" in raw:
            try:
                phone, password = raw.split(":", 1)
                accounts[f"account_{i}"] = {
                    "id": f"account_{i}",
                    "index": i,
                    "phone": phone.strip(),
                    "password": password.strip(),
                    "name": os.getenv(f"ACCOUNT_{i}_NAME", f"Аккаунт #{i}").strip(),
                }
                print(f"✅ Аккаунт {i}: {phone.strip()}")
                continue
            except Exception as e:
                print(f"❌ Ошибка парсинга ACCOUNT_{i}: {e}")
                continue
        
        # Формат 2: Отдельные переменные ACCOUNT_N_PHONE и ACCOUNT_N_PASSWORD
        phone = os.getenv(f"ACCOUNT_{i}_PHONE", "").strip()
        password = os.getenv(f"ACCOUNT_{i}_PASSWORD", "").strip()
        
        if phone:
            accounts[f"account_{i}"] = {
                "id": f"account_{i}",
                "index": i,
                "phone": phone,
                "password": password,
                "name": os.getenv(f"ACCOUNT_{i}_NAME", f"Аккаунт #{i}").strip(),
            }
            print(f"✅ Аккаунт {i}: {phone}")

    if not accounts:
        print("⚠️ Аккаунты не найдены в .env!")
    
    return accounts


def _parse_proxies() -> Dict[str, dict]:
    """
    Парсить прокси из .env
    
    Поддерживаемые форматы:
    - PROXY_1=http://user:pass@host:port
    - PROXY_1=host:port:user:pass
    - PROXY_1=host:port
    """
    
    proxies = {}
    
    for i in range(1, 11):
        raw = os.getenv(f"PROXY_{i}", "").strip().strip("'\"")
        
        if not raw:
            continue
        
        proxy = _parse_single_proxy(raw, index=i)
        
        if proxy:
            proxies[f"proxy_{i}"] = proxy
            proxy_display = f"{proxy['host']}:{proxy['port']}"
            if proxy['username']:
                proxy_display = f"{proxy['username']}:***@{proxy_display}"
            print(f"✅ Прокси {i}: {proxy_display}")
        else:
            print(f"❌ Не удалось парсить PROXY_{i}: {raw}")
    
    if not proxies:
        print("⚠️ Прокси не найдены в .env!")
    
    return proxies


def _parse_single_proxy(raw: str, index: int) -> Optional[dict]:
    """
    Парсить одну строку прокси
    
    Args:
        raw: Строка прокси
        index: Индекс для идентификации
        
    Returns:
        Dict с параметрами прокси или None
    """
    
    try:
        # Формат 1: http://user:pass@host:port
        if "://" in raw:
            from urllib.parse import urlparse
            
            parsed = urlparse(raw)
            
            return {
                "index": index,
                "protocol": parsed.scheme or "http",
                "host": parsed.hostname or "",
                "port": parsed.port or 0,
                "username": parsed.username or "",
                "password": parsed.password or "",
                "raw": raw,
            }
        
        # Формат 2: host:port:user:pass (4 части)
        parts = raw.split(":")
        
        if len(parts) == 4:
            try:
                return {
                    "index": index,
                    "protocol": "http",
                    "host": parts[0].strip(),
                    "port": int(parts[1]),
                    "username": parts[2].strip(),
                    "password": parts[3].strip(),
                    "raw": raw,
                }
            except ValueError:
                return None
        
        # Формат 3: host:port (2 части)
        if len(parts) == 2:
            try:
                return {
                    "index": index,
                    "protocol": "http",
                    "host": parts[0].strip(),
                    "port": int(parts[1]),
                    "username": "",
                    "password": "",
                    "raw": raw,
                }
            except ValueError:
                return None
        
        return None
    
    except Exception as e:
        print(f"⚠️ Ошибка парсинга прокси: {e}")
        return None


@dataclass
class Settings:
    """
    ⚙️ Основные настройки проекта
    
    Содержит:
    - Пути к директориям
    - Конфигурацию аккаунтов
    - Конфигурацию прокси
    - Telegram настройки
    - Параметры warmup и alive mode
    - Параметры ночного режима
    - Параметры безопасности
    """
    
    # ─────────────────────────────────────────────────────────────────
    # ПУТИ К ДИРЕКТОРИЯМ
    # ─────────────────────────────────────────────────────────────────
    
    project_root: Path = PROJECT_ROOT
    storage_dir: Path = PROJECT_ROOT / "storage"
    sessions_dir: Path = PROJECT_ROOT / "storage" / "sessions"
    logs_dir: Path = PROJECT_ROOT / "storage" / "logs"
    data_dir: Path = PROJECT_ROOT / "storage" / "data"
    fingerprints_dir: Path = PROJECT_ROOT / "storage" / "fingerprints"
    cache_dir: Path = PROJECT_ROOT / "storage" / "cache"

    # ─────────────────────────────────────────────────────────────────
    # АККАУНТЫ И ПРОКСИ
    # ─────────────────────────────────────────────────────────────────
    
    accounts: Dict[str, dict] = field(default_factory=_parse_accounts)
    proxies: Dict[str, dict] = field(default_factory=_parse_proxies)

    # ─────────────────────────────────────────────────────────────────
    # TELEGRAM
    # ─────────────────────────────────────────────────────────────────
    
    telegram_bot_token: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
    )
    telegram_chat_id: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", "")
    )
    telegram_enabled: bool = False
    
    tg_notify_login: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_LOGIN", "true").lower() == "true"
    )
    tg_notify_warmup: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_WARMUP", "true").lower() == "true"
    )
    tg_notify_ban: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_BAN", "true").lower() == "true"
    )
    tg_notify_captcha: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_CAPTCHA", "true").lower() == "true"
    )
    tg_notify_proxy_down: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_PROXY_DOWN", "true").lower() == "true"
    )
    tg_notify_errors: bool = field(
        default_factory=lambda: os.getenv("TG_NOTIFY_ERRORS", "true").lower() == "true"
    )

    # ─────────────────────────────────────────────────────────────────
    # WARMUP (ПРОГРЕВ)
    # ─────────────────────────────────────────────────────────────────
    
    warmup_duration_minutes: int = field(
        default_factory=lambda: int(os.getenv("WARMUP_DURATION_MINUTES", "90"))
    )
    warmup_categories: List[str] = field(
        default_factory=lambda: [
            c.strip()
            for c in os.getenv(
                "WARMUP_CATEGORIES", "мототехника,питбайки,квадроциклы"
            ).split(",")
        ]
    )
    warmup_deep_view_count: int = field(
        default_factory=lambda: int(os.getenv("WARMUP_DEEP_VIEW_COUNT", "7"))
    )
    warmup_add_to_favorites_probability: float = field(
        default_factory=lambda: float(os.getenv("WARMUP_ADD_TO_FAVORITES_PROB", "0.4"))
    )
    warmup_view_seller_probability: float = field(
        default_factory=lambda: float(os.getenv("WARMUP_VIEW_SELLER_PROB", "0.6"))
    )

    # ─────────────────────────────────────────────────────────────────
    # ALIVE MODE
    # ─────────────────────────────────────────────────────────────────
    
    alive_mode_min_hours: float = field(
        default_factory=lambda: float(os.getenv("ALIVE_MODE_MIN_HOURS", "3.0"))
    )
    alive_mode_max_hours: float = field(
        default_factory=lambda: float(os.getenv("ALIVE_MODE_MAX_HOURS", "6.0"))
    )
    alive_mode_pause_min_sec: int = field(
        default_factory=lambda: int(os.getenv("ALIVE_MODE_PAUSE_MIN_SEC", "600"))
    )
    alive_mode_pause_max_sec: int = field(
        default_factory=lambda: int(os.getenv("ALIVE_MODE_PAUSE_MAX_SEC", "2400"))
    )

    # ─────────────────────────────────────────────────────────────────
    # ДЕЙСТВИЯ ПО ЧАСАМ
    # ─────────────────────────────────────────────────────────────────
    
    max_actions_per_hour: int = field(
        default_factory=lambda: int(os.getenv("MAX_ACTIONS_PER_HOUR", "8"))
    )
    max_actions_per_day: int = field(
        default_factory=lambda: int(os.getenv("MAX_ACTIONS_PER_DAY", "100"))
    )

    # ─────────────────────────────────────────────────────────────────
    # НОЧНОЙ РЕЖИМ
    # ─────────────────────────────────────────────────────────────────
    
    night_mode_start: Tuple[int, int] = field(
        default_factory=lambda: _parse_time(os.getenv("NIGHT_MODE_START", "23:00"))
    )
    night_mode_end: Tuple[int, int] = field(
        default_factory=lambda: _parse_time(os.getenv("NIGHT_MODE_END", "07:00"))
    )
    night_mode_randomize_minutes: int = field(
        default_factory=lambda: int(os.getenv("NIGHT_MODE_RANDOMIZE_MINUTES", "60"))
    )
    night_mode_timezone: str = field(
        default_factory=lambda: os.getenv("NIGHT_MODE_TIMEZONE", "Europe/Moscow")
    )

    # ─────────────────────────────────────────────────────────────────
    # CIRCUIT BREAKER (ЗАЩИТА ОТ БЛОКИРОВОК)
    # ─────────────────────────────────────────────────────────────────
    
    circuit_breaker_threshold: int = field(
        default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    )
    circuit_breaker_cooldown_minutes: int = field(
        default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_COOLDOWN_MINUTES", "30"))
    )
    circuit_breaker_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("CIRCUIT_BREAKER_TIMEOUT_SEC", "300"))
    )

    # ─────────────────────────────────────────────────────────────────
    # БРАУЗЕР
    # ─────────────────────────────────────────────────────────────────
    
    headless: bool = field(
        default_factory=lambda: os.getenv("HEADLESS", "false").lower() == "true"
    )
    page_load_timeout: int = field(
        default_factory=lambda: int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))
    )
    browser_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("BROWSER_TIMEOUT_SEC", "60"))
    )

    # ─────────────────────────────────────────────────────────────────
    # RETRY И FALLBACK
    # ─────────────────────────────────────────────────────────────────
    
    retry_max_attempts: int = field(
        default_factory=lambda: int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    )
    retry_wait_seconds: int = field(
        default_factory=lambda: int(os.getenv("RETRY_WAIT_SEC", "2"))
    )
    retry_timeout_seconds: int = field(
        default_factory=lambda: int(os.getenv("RETRY_TIMEOUT_SEC", "30"))
    )

    # ─────────────────────────────────────────────────────────────────
    # FINGERPRINT И STEALTH
    # ─────────────────────────────────────────────────────────────────
    
    fingerprint_refresh_probability: float = field(
        default_factory=lambda: float(os.getenv("FINGERPRINT_REFRESH_PROB", "0.1"))
    )
    stealth_enabled: bool = field(
        default_factory=lambda: os.getenv("STEALTH_ENABLED", "true").lower() == "true"
    )

    # ─────────────────────────────────────────────────────────────────
    # ЛОГИРОВАНИЕ
    # ─────────────────────────────────────────────────────────────────
    
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    log_to_file: bool = field(
        default_factory=lambda: os.getenv("LOG_TO_FILE", "true").lower() == "true"
    )
    log_file_max_bytes: int = field(
        default_factory=lambda: int(os.getenv("LOG_FILE_MAX_BYTES", "10485760"))  # 10MB
    )
    log_file_backup_count: int = field(
        default_factory=lambda: int(os.getenv("LOG_FILE_BACKUP_COUNT", "5"))
    )

    def __post_init__(self):
        """Инициализация после создания объекта"""
        
        # Создаём все необходимые директории
        for dir_path in [
            self.storage_dir,
            self.sessions_dir,
            self.logs_dir,
            self.data_dir,
            self.fingerprints_dir,
            self.cache_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Включаем Telegram если оба параметра есть
        self.telegram_enabled = bool(self.telegram_bot_token and self.telegram_chat_id)
        
        # Валидация параметров
        self._validate_settings()

    def _validate_settings(self):
        """Валидировать критические параметры"""
        
        errors = []
        
        # Проверяем аккаунты
        if not self.accounts:
            errors.append("❌ Аккаунты не найдены! Добавьте ACCOUNT_X в .env")
        
        # Проверяем Telegram (если нужен)
        if not self.telegram_enabled:
            print("⚠️ Telegram отключен (TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не установлены)")
        
        # Проверяем warmup параметры
        if self.warmup_duration_minutes < 10:
            errors.append(f"❌ WARMUP_DURATION_MINUTES слишком мало ({self.warmup_duration_minutes}, минимум 10)")
        
        # Проверяем alive mode параметры
        if self.alive_mode_min_hours > self.alive_mode_max_hours:
            errors.append(
                f"❌ ALIVE_MODE_MIN_HOURS ({self.alive_mode_min_hours}) больше "
                f"ALIVE_MODE_MAX_HOURS ({self.alive_mode_max_hours})"
            )
        
        # Выводим ошибки
        if errors:
            print("\n".join(errors))
            sys.exit(1)

    def print_summary(self):
        """Вывести полную сводку конфигурации"""
        from colorama import Fore, Style
        
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'⚙️  КОНФИГУРАЦИЯ ПРОЕКТА':^80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
        
        # ─────────────────────────────────────────────────────────────
        # АККАУНТЫ
        # ─────────────────────────────────────────────────────────────
        
        print(f"{Fore.YELLOW}📱 АККАУНТЫ ({len(self.accounts)}){Style.RESET_ALL}")
        for acc_id, acc in self.accounts.items():
            proxy = self.get_proxy_for_account(acc_id)
            proxy_str = f"{proxy['host']}:{proxy['port']}" if proxy else "❌ нет"
            print(f"  {Fore.GREEN}{acc_id}{Style.RESET_ALL}: {acc['phone']} → {proxy_str}")
        
        # ─────────────────────────────────────────────────────────────
        # ПРОКСИ
        # ─────────────────────────────────────────────────────────────
        
        print(f"\n{Fore.YELLOW}🪜 ПРОКСИ ({len(self.proxies)}){Style.RESET_ALL}")
        if self.proxies:
            for proxy_id, proxy in self.proxies.items():
                proxy_display = f"{proxy['host']}:{proxy['port']}"
                if proxy['username']:
                    proxy_display = f"{proxy['username']}@{proxy_display}"
                print(f"  {Fore.GREEN}{proxy_id}{Style.RESET_ALL}: {proxy_display}")
        else:
            print(f"  {Fore.RED}Прокси не найдены{Style.RESET_ALL}")
        
        # ─────────────────────────────────────────────────────────────
        # TELEGRAM
        # ─────────────────────────────────────────────────────────────
        
        telegram_status = f"{Fore.GREEN}✅{Style.RESET_ALL}" if self.telegram_enabled else f"{Fore.RED}❌{Style.RESET_ALL}"
        print(f"\n{Fore.YELLOW}📨 TELEGRAM{Style.RESET_ALL}: {telegram_status}")
        if self.telegram_enabled:
            print(f"  Уведомления: login={self.tg_notify_login}, warmup={self.tg_notify_warmup}, "
                  f"ban={self.tg_notify_ban}, captcha={self.tg_notify_captcha}")
        
        # ─────────────────────────────────────────────────────────────
        # РАСПИСАНИЕ
        # ─────────────────────────────────────────────────────────────
        
        print(f"\n{Fore.YELLOW}🕐 РАСПИСАНИЕ{Style.RESET_ALL}")
        start_h, start_m = self.night_mode_start
        end_h, end_m = self.night_mode_end
        print(f"  Ночной режим: {start_h:02d}:{start_m:02d} — {end_h:02d}:{end_m:02d}")
        print(f"  Warmup: {self.warmup_duration_minutes} мин | Alive Mode: {self.alive_mode_min_hours:.1f}-{self.alive_mode_max_hours:.1f} часов")
        
        # ─────────────────────────────────────────────────────────────
        # БЕЗОПАСНОСТЬ
        # ─────────────────────────────────────────────────────────────
        
        print(f"\n{Fore.YELLOW}🛡️  БЕЗОПАСНОСТЬ{Style.RESET_ALL}")
        print(f"  Circuit Breaker: {self.circuit_breaker_threshold} ошибок → {self.circuit_breaker_cooldown_minutes} мин перерыва")
        print(f"  Max действий: {self.max_actions_per_hour}/час, {self.max_actions_per_day}/день")
        print(f"  Stealth: {Fore.GREEN}✅{Style.RESET_ALL}" if self.stealth_enabled else f"  Stealth: {Fore.RED}❌{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

    def get_proxy_for_account(self, account_id: str) -> Optional[dict]:
        """
        Получить прокси для конкретного аккаунта
        
        Стратегия:
        1. Ищем прокси с тем же индексом (account_1 → proxy_1)
        2. Если не найдена, циклим по доступным прокси
        """
        
        if not self.proxies:
            return None
        
        try:
            # Получаем индекс аккаунта
            acc_index = int(account_id.split("_")[1])
            
            # Ищем прокси с тем же индексом
            proxy_key = f"proxy_{acc_index}"
            if proxy_key in self.proxies:
                return self.proxies[proxy_key]
            
            # Если не найдена, циклим по доступным
            proxy_keys = sorted(self.proxies.keys())
            if proxy_keys:
                fallback_key = proxy_keys[(acc_index - 1) % len(proxy_keys)]
                return self.proxies[fallback_key]
        
        except Exception as e:
            print(f"⚠️ Ошибка при получении прокси для {account_id}: {e}")
        
        return None

    def get_account_by_id(self, account_id: str) -> Optional[dict]:
        """Получить конфигурацию аккаунта по ID"""
        return self.accounts.get(account_id)

    def get_all_account_ids(self) -> List[str]:
        """Получить список всех ID аккаунтов"""
        return list(self.accounts.keys())

    def get_all_proxy_ids(self) -> List[str]:
        """Получить список всех ID прокси"""
        return list(self.proxies.keys())

    def export_to_json(self, filepath: Path) -> bool:
        """
        Экспортировать конфигурацию в JSON (без чувствительных данных)
        """
        try:
            export_data = {
                "accounts_count": len(self.accounts),
                "proxies_count": len(self.proxies),
                "telegram_enabled": self.telegram_enabled,
                "warmup_duration_minutes": self.warmup_duration_minutes,
                "alive_mode_hours": f"{self.alive_mode_min_hours}-{self.alive_mode_max_hours}",
                "night_mode": f"{self.night_mode_start[0]:02d}:{self.night_mode_start[1]:02d} - {self.night_mode_end[0]:02d}:{self.night_mode_end[1]:02d}",
                "circuit_breaker": f"{self.circuit_breaker_threshold} errors → {self.circuit_breaker_cooldown_minutes} min",
                "max_actions": f"{self.max_actions_per_hour}/hour, {self.max_actions_per_day}/day",
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                import json
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"❌ Ошибка при экспорте конфигурации: {e}")
            return False


# Создаём глобальный объект settings
settings = Settings()