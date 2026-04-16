# services/metrics.py
"""
📊 METRICS — Сбор статистики и метрик
"""

from datetime import datetime
from typing import Dict, Any


class MetricsCollector:
    def __init__(self, logger):
        self.logger = logger
        self.metrics: Dict[str, Any] = {
            "started_at": datetime.now(),
            "total_logins": 0,
            "total_warmups": 0,
            "total_actions": 0,
            "total_errors": 0,
            "accounts": {},
        }

    def record_login(self, account_id: str):
        self.metrics["total_logins"] += 1
        if account_id not in self.metrics["accounts"]:
            self.metrics["accounts"][account_id] = {
                "logins": 0,
                "warmups": 0,
                "actions": 0,
                "errors": 0,
            }
        self.metrics["accounts"][account_id]["logins"] += 1

    def record_warmup(self, account_id: str):
        self.metrics["total_warmups"] += 1
        if account_id not in self.metrics["accounts"]:
            self.metrics["accounts"][account_id] = {
                "logins": 0,
                "warmups": 0,
                "actions": 0,
                "errors": 0,
            }
        self.metrics["accounts"][account_id]["warmups"] += 1

    def record_action(self, account_id: str, status: str):
        self.metrics["total_actions"] += 1
        if account_id not in self.metrics["accounts"]:
            self.metrics["accounts"][account_id] = {
                "logins": 0,
                "warmups": 0,
                "actions": 0,
                "errors": 0,
            }
        self.metrics["accounts"][account_id]["actions"] += 1

        if status != "SUCCESS":
            self.metrics["total_errors"] += 1
            self.metrics["accounts"][account_id]["errors"] += 1

    def get_summary(self) -> Dict:
        return {
            "uptime_hours": (
                datetime.now() - self.metrics["started_at"]
            ).total_seconds() / 3600,
            "total_logins": self.metrics["total_logins"],
            "total_warmups": self.metrics["total_warmups"],
            "total_actions": self.metrics["total_actions"],
            "total_errors": self.metrics["total_errors"],
            "accounts": self.metrics["accounts"],
        }