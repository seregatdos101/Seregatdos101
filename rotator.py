# core/proxy/rotator.py
"""
🔄 PROXY ROTATOR — Ротация прокси по аккаунтам
"""

from typing import Dict, Optional


class ProxyRotator:
    def __init__(self, proxy_manager):
        self.proxy_manager = proxy_manager
        self._current_index: Dict[str, int] = {}

    def get_next_proxy(self, account_id: str) -> Optional[dict]:
        """Получить следующий прокси в ротации"""
        available_proxies = [
            p for p in self.proxy_manager._proxies.keys()
            if p not in self.proxy_manager._failed_proxies
        ]

        if not available_proxies:
            return None

        if account_id not in self._current_index:
            self._current_index[account_id] = 0

        current_idx = self._current_index[account_id]
        proxy_key = available_proxies[current_idx % len(available_proxies)]

        # Переходим на следующий
        self._current_index[account_id] = (current_idx + 1) % len(available_proxies)

        return self.proxy_manager._proxies.get(proxy_key)

    def reset(self, account_id: str):
        """Сбросить ротацию"""
        self._current_index.pop(account_id, None)