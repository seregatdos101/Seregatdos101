# core/proxy/checker.py
"""
✅ PROXY CHECKER — Проверка работоспособности прокси
"""

import asyncio
import aiohttp
from typing import Dict

from core.proxy.manager import ProxyManager


async def check_single_proxy(proxy_manager: ProxyManager, proxy_id: str, logger) -> Dict:
    """Проверить один прокси"""
    try:
        proxy_config = proxy_manager._proxies.get(proxy_id)
        if not proxy_config:
            return {"proxy_id": proxy_id, "ok": False, "error": "Not found"}

        proxy_url = f"{proxy_config['protocol']}://{proxy_config['host']}:{proxy_config['port']}"

        if proxy_config.get('username') and proxy_config.get('password'):
            proxy_url = f"{proxy_config['protocol']}://{proxy_config['username']}:{proxy_config['password']}@{proxy_config['host']}:{proxy_config['port']}"

        timeout = aiohttp.ClientTimeout(total=15)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                start = asyncio.get_event_loop().time()

                async with session.get(
                    "https://api.ipify.org?format=json",
                    proxy=proxy_url,
                    timeout=timeout,
                ) as resp:
                    elapsed = (asyncio.get_event_loop().time() - start) * 1000
                    
                    if resp.status == 200:
                        data = await resp.json()
                        ip = data.get("ip", "unknown")
                        proxy_manager.mark_proxy_success(proxy_id, int(elapsed), ip)
                        return {
                            "proxy_id": proxy_id,
                            "ok": True,
                            "ip": ip,
                            "latency_ms": int(elapsed),
                        }
                    else:
                        error = f"HTTP {resp.status}"
                        proxy_manager.mark_proxy_failed(proxy_id, error)
                        return {"proxy_id": proxy_id, "ok": False, "error": error}

            except asyncio.TimeoutError:
                proxy_manager.mark_proxy_failed(proxy_id, "Timeout")
                return {"proxy_id": proxy_id, "ok": False, "error": "Timeout"}

            except Exception as e:
                error = str(e)[:50]
                proxy_manager.mark_proxy_failed(proxy_id, error)
                return {"proxy_id": proxy_id, "ok": False, "error": error}

    except Exception as e:
        return {"proxy_id": proxy_id, "ok": False, "error": str(e)[:50]}


async def check_all_proxies(proxy_manager: ProxyManager, logger) -> Dict:
    """Проверить все прокси параллельно"""
    tasks = [
        check_single_proxy(proxy_manager, proxy_id, logger)
        for proxy_id in proxy_manager._proxies.keys()
    ]

    results = await asyncio.gather(*tasks)
    return {r["proxy_id"]: r for r in results}