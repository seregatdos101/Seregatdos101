"""
📋 LOGGER 2027 — Профессиональное логирование всех событий
JSON + консоль + файлы по аккаунтам
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional
from colorama import Fore, Style

from config.settings import settings


class Logger:
    """📋 Логгер со структурированным выводом"""

    def __init__(self):
        self.logs_dir = settings.logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Основной JSON логгер
        self.log_file = self.logs_dir / "avito_bot.log"
        
        # Настройка Python логгера
        self.logger = logging.getLogger("avito_bot")
        self.logger.setLevel(logging.DEBUG)
        
        # Handler для файла
        handler = logging.FileHandler(self.log_file, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _save_json_log(self, data: dict):
        """Сохранить в JSON формат"""
        try:
            with open(self.log_file.with_suffix(".jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────
    # ОСНОВНЫЕ МЕТОДЫ ЛОГИРОВАНИЯ
    # ─────────────────────────────────────────────────────────────

    def action(self, account_id: str, action: str, status: str, **kwargs):
        """Записать действие"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "account_id": account_id,
            "type": "action",
            "action": action,
            "status": status,
            **kwargs,
        }
        self.logger.info(f"[{account_id}] {action}: {status}")
        self._save_json_log(data)
        print(f"  {Fore.GREEN}[{account_id}]{Style.RESET_ALL} {action}: {status}")

    def error(self, account_id: str, message: str, severity: str = "MEDIUM", **kwargs):
        """Записать ошибку"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "account_id": account_id,
            "type": "error",
            "severity": severity,
            "message": message,
            **kwargs,
        }
        self.logger.error(f"[{account_id}] {severity}: {message}")
        self._save_json_log(data)
        color = Fore.RED if severity == "CRITICAL" else Fore.YELLOW
        print(f"  {color}[{account_id}]{Style.RESET_ALL} ❌ {message}")

    def warning(self, account_id: str, message: str, **kwargs):
        """Записать предупреждение"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "account_id": account_id,
            "type": "warning",
            "message": message,
            **kwargs,
        }
        self.logger.warning(f"[{account_id}] {message}")
        self._save_json_log(data)
        print(f"  {Fore.YELLOW}[{account_id}]{Style.RESET_ALL} ⚠️ {message}")

    def success(self, account_id: str, message: str, **kwargs):
        """Записать успех"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "account_id": account_id,
            "type": "success",
            "message": message,
            **kwargs,
        }
        self.logger.info(f"[{account_id}] ✅ {message}")
        self._save_json_log(data)
        print(f"  {Fore.GREEN}[{account_id}]{Style.RESET_ALL} ✅ {message}")

    def info(self, account_id: str, message: str, **kwargs):
        """Информационное сообщение"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "account_id": account_id,
            "type": "info",
            "message": message,
            **kwargs,
        }
        self.logger.info(f"[{account_id}] {message}")
        self._save_json_log(data)
        print(f"  {Fore.CYAN}[{account_id}]{Style.RESET_ALL} ℹ️ {message}")

    def risk(self, account_id: str, level: str, message: str, score: int = 0, **kwargs):
        """Записать анализ риска"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "account_id": account_id,
            "type": "risk",
            "level": level,
            "score": score,
            "message": message,
            **kwargs,
        }
        self.logger.warning(f"[{account_id}] RISK {level}: {message} (score: {score})")
        self._save_json_log(data)

    def proxy_test_success(self, proxy_id: str, latency_ms: int, ip: str, **kwargs):
        """Прокси успешно протестирован"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "type": "proxy_test",
            "proxy_id": proxy_id,
            "status": "success",
            "latency_ms": latency_ms,
            "ip": ip,
            **kwargs,
        }
        self.logger.info(f"PROXY {proxy_id}: OK ({latency_ms}ms) → {ip}")
        self._save_json_log(data)

    def proxy_test_failed(self, proxy_id: str, error: str, **kwargs):
        """Прокси не прошёл тест"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "type": "proxy_test",
            "proxy_id": proxy_id,
            "status": "failed",
            "error": error,
            **kwargs,
        }
        self.logger.error(f"PROXY {proxy_id}: FAILED - {error}")
        self._save_json_log(data)

    def system(self, message: str, **kwargs):
        """Системное сообщение"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "type": "system",
            "message": message,
            **kwargs,
        }
        self.logger.info(f"🔧 SYSTEM: {message}")
        self._save_json_log(data)
        print(f"  {Fore.MAGENTA}[SYSTEM]{Style.RESET_ALL} 🔧 {message}")