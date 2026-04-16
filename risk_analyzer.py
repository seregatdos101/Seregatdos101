# core/safety/risk_analyzer.py
"""
🧠 RISK ANALYZER — Анализ рисков перед выполнением действия
"""

from datetime import datetime
from typing import Tuple, Dict
from enum import Enum

from config.settings import settings


class RiskLevel(Enum):
    LOW = "🟢 LOW"
    MEDIUM = "🟡 MEDIUM"
    HIGH = "🔴 HIGH"
    CRITICAL = "🚨 CRITICAL"


class RiskAnalyzer:
    def __init__(self, logger):
        self.logger = logger
        self._action_history: Dict[str, list] = {}

    def record_action(self, account_id: str):
        if account_id not in self._action_history:
            self._action_history[account_id] = []
        self._action_history[account_id].append(datetime.now())
        self._action_history[account_id] = self._action_history[account_id][-100:]

    async def analyze(self, account_id: str) -> Tuple[RiskLevel, Dict]:
        details = {"factors": {}}
        total_score = 0

        aph = self._actions_per_hour(account_id)
        aph_score = 0
        if aph > settings.max_actions_per_hour:
            aph_score = 40
        elif aph > settings.max_actions_per_hour * 0.7:
            aph_score = 20
        details["factors"]["actions_per_hour"] = {"value": aph, "score": aph_score}
        total_score += aph_score

        hour = datetime.now().hour
        time_score = 0
        if settings.night_mode_start[0] <= hour or hour < settings.night_mode_end[0]:
            time_score = 25
        details["factors"]["time_of_day"] = {"hour": hour, "score": time_score}
        total_score += time_score

        min_pause = self._min_pause_minutes(account_id)
        pause_score = 0
        if min_pause is not None:
            if min_pause < 1:
                pause_score = 35
            elif min_pause < 3:
                pause_score = 15
        details["factors"]["min_pause_minutes"] = {"value": min_pause, "score": pause_score}
        total_score += pause_score

        if total_score >= 80:
            level = RiskLevel.CRITICAL
        elif total_score >= 50:
            level = RiskLevel.HIGH
        elif total_score >= 25:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        details["total_score"] = total_score
        details["level"] = level.value

        return level, details

    async def get_recommended_pause(self, account_id: str) -> float:
        level, _ = await self.analyze(account_id)
        pauses = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 30,
            RiskLevel.HIGH: 120,
            RiskLevel.CRITICAL: 300,
        }
        return pauses.get(level, 0)

    def _actions_per_hour(self, account_id: str) -> int:
        history = self._action_history.get(account_id, [])
        cutoff = datetime.now().replace(minute=0, second=0, microsecond=0)
        from datetime import timedelta
        cutoff = cutoff - timedelta(hours=1)
        return sum(1 for ts in history if ts > cutoff)

    def _min_pause_minutes(self, account_id: str) -> float:
        history = self._action_history.get(account_id, [])
        if len(history) < 2:
            return None
        min_pause = float("inf")
        for i in range(1, len(history)):
            diff = (history[i] - history[i - 1]).total_seconds() / 60
            min_pause = min(min_pause, diff)
        return round(min_pause, 2) if min_pause != float("inf") else None