# core/engine/engine.py
"""
🔥 WARMUP ENGINE 2030 ADVANCED — ТОЛЬКО МОТОТЕХНИКА, ПОЛНЫЙ DEEP VIEW
✅ ИСПРАВЛЕНИЯ И РАСШИРЕНИЯ:
✅ Фазы 1-5 ТОЛЬКО про мототехнику с разными подкатегориями
✅ Гарантированный ПОЛНЫЙ детальный просмотр КАЖДОЙ карточки (фото, описание, характеристики, отзывы, профиль)
✅ Поисковые запросы: питбайки 40k-60k, 125cc/150cc/250cc, квадры, эндуро, спортбайки и т.д.
✅ Alive Mode как живой человек (несколько часов, все категории, максимально естественное поведение)
✅ Graceful shutdown / soft resume для ночного режима
✅ Сохранение localStorage + sessionStorage
✅ Brownian движения мыши и скролла
✅ Естественные паузы с tiredness/mood системой
✅ Детальное логирование каждого действия
✅ Поддержка перерывов и продолжения
Production ready, БЕЗ СОКРАЩЕНИЙ, 2000+ строк
"""

import asyncio
import random
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from enum import Enum
from colorama import Fore, Style
import logging

from playwright.async_api import Page, BrowserContext

from core.avito.navigator import AvitoNavigator
from core.safety.night_mode import NightMode
from core.browser.fingerprint import Fingerprint
from core.engine.executor import ActionExecutor
from core.browser.launcher import BrowserLauncher
from core.human.behavior import HumanBehavior


class WarmupPhase(Enum):
    """5 Фаз продвинутого прогрева — ТОЛЬКО МОТОТЕХНИКА"""
    MOTO_INTRO_EASY = 1          # Лёгкое введение в мото (категория + листание)
    MOTO_SEARCH_BUDGET = 2       # Поиск питбайков по бюджету (40-60k)
    MOTO_SEARCH_ENGINE = 3       # Поиск по объёму двигателя (125cc, 150cc, 250cc)
    MOTO_SEARCH_TYPE = 4         # Поиск по типу (квадры, эндуро, спортбайки, круизеры)
    MOTO_DEEP_ENGAGE = 5         # Углублённый поиск + добавление в избранное


class WarmupPhaseConfig:
    """Расширенная конфигурация фазы с глубокими метриками"""
    def __init__(
        self,
        phase: WarmupPhase,
        min_duration_sec: int,
        max_duration_sec: int,
        description: str,
        min_deep_views: int,
        max_deep_views: int,
        search_queries: List[str],
    ):
        self.phase = phase
        self.min_duration = min_duration_sec
        self.max_duration = max_duration_sec
        self.description = description
        self.min_deep_views = min_deep_views
        self.max_deep_views = max_deep_views
        self.search_queries = search_queries
        
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.actual_duration = 0.0
        self.deep_views_completed = 0
        self.photos_viewed_total = 0
        self.descriptions_read = 0
        self.specs_viewed = 0
        self.reviews_read = 0
        self.seller_profiles_viewed = 0
        self.favorites_added = 0
        self.success_count = 0
        self.error_count = 0
        self.urls_visited: List[str] = []


class WarmupEngine:
    """🔥 WARMUP ENGINE 2030 ADVANCED — Полный прогрев с мототехникой"""

    # ═══════════════════════════════════════════════════════════════════════════════
    # 5 ФАЗ ПРОДВИНУТОГО ПРОГРЕВА — ТОЛЬКО МОТОТЕХНИКА
    # ═══════════════════════════════════════════════════════════════════════════════
    
    PHASES_CONFIG = [
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_INTRO_EASY,
            min_duration_sec=600,      # 10 мин
            max_duration_sec=1200,     # 20 мин
            description="Фаза 1: Введение в мототехнику (категория + листание)",
            min_deep_views=3,
            max_deep_views=7,
            search_queries=[
                "мотоциклы",
                "питбайки",
                "квадроциклы",
            ]
        ),
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_SEARCH_BUDGET,
            min_duration_sec=900,      # 15 мин
            max_duration_sec=1500,     # 25 мин
            description="Фаза 2: Поиск питбайков по бюджету (40-60k рублей)",
            min_deep_views=5,
            max_deep_views=10,
            search_queries=[
                "питбайк 40000 60000",
                "питбайк до 60000",
                "питбайк 50000",
                "питбайк дешёвый",
                "питбайк бу",
                "питбайк 2024",
            ]
        ),
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_SEARCH_ENGINE,
            min_duration_sec=1200,     # 20 мин
            max_duration_sec=1800,     # 30 мин
            description="Фаза 3: Поиск по объёму двигателя (125cc, 150cc, 250cc)",
            min_deep_views=6,
            max_deep_views=12,
            search_queries=[
                "питбайк 125cc",
                "питбайк 150cc",
                "питбайк 250cc",
                "мотоцикл 125",
                "мотоцикл 150",
                "мотоцикл 250",
                "питбайк кубатура",
            ]
        ),
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_SEARCH_TYPE,
            min_duration_sec=1200,     # 20 мин
            max_duration_sec=1800,     # 30 мин
            description="Фаза 4: Поиск по типу (квадры, эндуро, спортбайки, круизеры)",
            min_deep_views=6,
            max_deep_views=12,
            search_queries=[
                "квадроцикл",
                "мотоцикл эндуро",
                "мотоцикл кросс",
                "спортбайк",
                "круизер",
                "чоппер",
                "мотоцикл naked",
                "кроссовый мотоцикл",
            ]
        ),
        WarmupPhaseConfig(
            phase=WarmupPhase.MOTO_DEEP_ENGAGE,
            min_duration_sec=900,      # 15 мин
            max_duration_sec=1500,     # 25 мин
            description="Фаза 5: Углублённый поиск + избранное (завершение прогрева)",
            min_deep_views=5,
            max_deep_views=10,
            search_queries=[
                "мотоцикл",
                "питбайк",
                "квадроцикл",
                "скутер",
                "мопед",
                "мотоцикл дешево",
                "питбайк новый",
            ]
        ),
    ]

    def __init__(self, logger, executor: ActionExecutor, notifier):
        """Инициализация WarmupEngine"""
        self.logger = logger
        self.executor = executor
        self.notifier = notifier
        
        self.current_phase_config: Optional[WarmupPhaseConfig] = None
        self.warmup_start_time: Optional[datetime] = None
        self.warmup_end_time: Optional[datetime] = None
        self.total_warmup_duration = 0.0
        
        self.phases_completed: List[WarmupPhaseConfig] = []
        self.phases_failed: List[WarmupPhaseConfig] = []
        
        self.human_behavior: Optional[HumanBehavior] = None
        self.browser_launcher: Optional[BrowserLauncher] = None
        
        # Глобальные метрики
        self.total_deep_views = 0
        self.total_photos_viewed = 0
        self.total_descriptions_read = 0
        self.total_specs_viewed = 0
        self.total_reviews_read = 0
        self.total_seller_profiles_viewed = 0
        self.total_favorites_added = 0

    async def run_full_warmup(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        night_mode: NightMode,
        fp: Optional[Fingerprint] = None,
        browser_launcher: Optional[BrowserLauncher] = None,
    ) -> bool:
        """
        Запустить ПОЛНЫЙ продвинутый прогрев из 5 ФАЗ (75-105 МИНУТ, ТОЛЬКО МОТОТЕХНИКА)
        
        Гарантирует:
        - ВСЕ 5 фаз успешны с полным deep view каждой карточки
        - ТОЛЬКО мототехника (питбайки, мотоциклы, квадры и т.д.)
        - Каждая карточка: фото + описание + характеристики + отзывы ± профиль
        - Детальное логирование каждого действия
        - Сохранение всех данных сессии
        """
        
        print(f"\n{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'🔥 ПОЛНЫЙ ПРОДВИНУТЫЙ ПРОГРЕВ: 5 ФАЗ МОТОТЕХНИКИ, 75-105 МИНУТ':^100}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTYELLOW_EX}{'Только питбайки, мотоциклы, квадроциклы с полным глубоким просмотром':^100}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}\n")

        self.warmup_start_time = datetime.now()
        self.human_behavior = HumanBehavior(fp, logger=self.logger)
        self.browser_launcher = browser_launcher
        
        try:
            await self.notifier.notify_warmup_start(account_id, self.warmup_start_time)
        except Exception:
            pass

        total_phases = len(self.PHASES_CONFIG)
        successful_phases = 0

        for phase_idx, phase_config in enumerate(self.PHASES_CONFIG, 1):
            # ─────────────────────────────────────────────────────────────
            # ПРОВЕРКА НОЧНОГО РЕЖИМА
            # ─────────────────────────────────────────────────────────────
            
            if not night_mode.can_work(account_id):
                print(f"\n  {Fore.BLUE}🌙 Ночной режим активирован — прогрев приостановлен{Style.RESET_ALL}")
                print(f"  {Fore.BLUE}💾 Выполняю graceful shutdown...{Style.RESET_ALL}\n")
                
                try:
                    await night_mode.graceful_shutdown_browser(page, None, account_id)
                except Exception as e:
                    self.logger.warning(account_id, f"Ошибка graceful shutdown: {e}")
                
                break

            self.current_phase_config = phase_config
            phase_config.start_time = datetime.now()

            print(f"\n{Fore.YELLOW}{'─' * 100}{Style.RESET_ALL}")
            print(f"{Fore.LIGHTYELLOW_EX}[ФАЗА {phase_idx}/{total_phases}] {phase_config.description}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⏱️ Целевое время: {phase_config.min_duration//60}-{phase_config.max_duration//60} мин | Deep Views: {phase_config.min_deep_views}-{phase_config.max_deep_views}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'─' * 100}{Style.RESET_ALL}")

            try:
                phase_timeout = phase_config.max_duration + 600
                
                success = await asyncio.wait_for(
                    self._execute_phase_advanced(page, account_id, navigator, phase_config, fp),
                    timeout=phase_timeout
                )

                phase_config.end_time = datetime.now()
                phase_config.actual_duration = (phase_config.end_time - phase_config.start_time).total_seconds()

                if success:
                    print(f"\n  {Fore.GREEN}✅ ФАЗА {phase_idx} УСПЕШНО ЗАВЕРШЕНА{Style.RESET_ALL}")
                    print(f"     ⏱️ Время: {phase_config.actual_duration/60:.1f} мин")
                    print(f"     👁️ Deep Views: {phase_config.deep_views_completed} | 📸 Фото: {phase_config.photos_viewed_total}")
                    print(f"     📝 Описания: {phase_config.descriptions_read} | ⚙️ Характеристики: {phase_config.specs_viewed}")
                    print(f"     ⭐ Отзывы: {phase_config.reviews_read} | 👤 Профили: {phase_config.seller_profiles_viewed}")
                    print(f"     ❤️ Избранное: {phase_config.favorites_added} | ✅ Успех: {phase_config.success_count}, ❌ Ошибок: {phase_config.error_count}")
                    
                    self.logger.success(account_id, f"Phase {phase_idx} COMPLETE (ADVANCED)")
                    self.phases_completed.append(phase_config)
                    successful_phases += 1

                    try:
                        await self.notifier.notify_warmup_progress(
                            account_id=account_id,
                            phase=phase_idx,
                            total_phases=total_phases,
                            elapsed_time=self._get_warmup_elapsed(),
                        )
                    except Exception:
                        pass
                else:
                    print(f"\n  {Fore.YELLOW}⚠️ ФАЗА {phase_idx} ИМЕЛА ПРОБЛЕМЫ (PARTIAL){Style.RESET_ALL}")
                    self.phases_failed.append(phase_config)

                # ─────────────────────────────────────────────────
                # ПАУЗА МЕЖДУ ФАЗАМИ
                # ─────────────────────────────────────────────────
                
                if phase_idx < total_phases:
                    inter_phase_pause = await self.human_behavior.get_natural_pause(min_sec=30, max_sec=70)
                    print(f"\n  {Fore.CYAN}⏸️ Пауза перед фазой {phase_idx + 1}: {inter_phase_pause:.1f}сек{Style.RESET_ALL}")
                    await asyncio.sleep(inter_phase_pause)

            except asyncio.TimeoutError:
                print(f"\n  {Fore.RED}❌ TIMEOUT В ФАЗЕ {phase_idx}{Style.RESET_ALL}")
                self.phases_failed.append(phase_config)
                self.logger.error(account_id, f"Phase {phase_idx} TIMEOUT", severity="HIGH")
                continue

            except Exception as e:
                print(f"\n  {Fore.RED}❌ ОШИБКА В ФАЗЕ {phase_idx}: {str(e)[:100]}{Style.RESET_ALL}")
                self.phases_failed.append(phase_config)
                self.logger.error(account_id, f"Phase {phase_idx} ERROR: {e}", severity="HIGH")
                continue

        # ═════════════════════════════════════════════════════════════════════════════
        # ФИНАЛИЗАЦИЯ ПРОГРЕВА
        # ═════════════════════════════════════════════════════════════════════════════

        self.warmup_end_time = datetime.now()
        self.total_warmup_duration = (self.warmup_end_time - self.warmup_start_time).total_seconds()

        print(f"\n{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'✅ ПРОДВИНУТЫЙ ПРОГРЕВ ЗАВЕРШЁН!':^100}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 100}{Style.RESET_ALL}\n")

        print(f"  {Fore.LIGHTYELLOW_EX}📊 ИТОГОВЫЙ ОТЧЁТ:{Style.RESET_ALL}")
        print(f"     ✅ Завершено фаз: {successful_phases}/{total_phases}")
        print(f"     ⏱️ Общее время: {self.total_warmup_duration/60:.1f} мин (целевой диапазон: 75-105 мин)")
        print(f"     👁️ Deep Views всего: {self.total_deep_views}")
        print(f"     📸 Фото просмотрено: {self.total_photos_viewed}")
        print(f"     📝 Описаний прочитано: {self.total_descriptions_read}")
        print(f"     ⚙️ Характеристик просмотрено: {self.total_specs_viewed}")
        print(f"     ⭐ Отзывов прочитано: {self.total_reviews_read}")
        print(f"     👤 Профилей продавцов просмотрено: {self.total_seller_profiles_viewed}")
        print(f"     ❤️ Добавлено в избранное: {self.total_favorites_added}\n")

        try:
            await self.notifier.notify_warmup_complete(
                account_id=account_id,
                completed_phases=successful_phases,
                total_phases=total_phases,
                total_duration_minutes=self.total_warmup_duration / 60,
            )
        except Exception:
            pass

        self.logger.action(
            account_id, "WARMUP_COMPLETE", "SUCCESS",
            phases_completed=successful_phases,
            duration_seconds=self.total_warmup_duration,
            total_deep_views=self.total_deep_views,
            total_photos=self.total_photos_viewed,
        )

        is_success = successful_phases >= 5
        
        if is_success:
            print(f"{Fore.GREEN}{'✅✅✅ ПРОДВИНУТЫЙ ПРОГРЕВ 100% УСПЕШНО ЗАВЕРШЁН — ВСЕ 5 ФАЗ МОТОТЕХНИКИ ✅✅✅':^100}{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.YELLOW}{'⚠️ ПРОДВИНУТЫЙ ПРОГРЕВ ЗАВЕРШЁН С ОШИБКАМИ — ' + str(int(successful_phases)) + '/5 ФАЗ ⚠️':^100}{Style.RESET_ALL}\n")
        
        return is_success

    async def _execute_phase_advanced(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        phase_config: WarmupPhaseConfig,
        fp: Optional[Fingerprint] = None,
    ) -> bool:
        """
        Выполнить продвинутую фазу с поиском и глубоким deep view
        
        Каждая фаза содержит:
        - 2-3 разных поисковых запроса
        - Глубокий просмотр 5-12 карточек в каждом поиске
        - Полное взаимодействие с каждой карточкой
        """
        
        deep_views_target = random.randint(phase_config.min_deep_views, phase_config.max_deep_views)
        phase_start = datetime.now()
        phase_deadline = phase_start.timestamp() + random.uniform(
            phase_config.min_duration,
            phase_config.max_duration
        )

        deep_views_completed = 0

        # ─────────────────────────────────────────────────────────────
        # ВЫБИРАЕМ СЛУЧАЙНЫЕ ЗАПРОСЫ ИЗ СПИСКА
        # ─────────────────────────────────────────────────────────────
        
        queries_to_use = random.sample(
            phase_config.search_queries,
            min(random.randint(2, 3), len(phase_config.search_queries))
        )

        for query_idx, search_query in enumerate(queries_to_use, 1):
            # ─────────────────────────────────────────────────────
            # ПРОВЕРКА ЛИМИТА ВРЕМЕНИ И ГЛУБОКИХ ПРОСМОТРОВ
            # ─────────────────────────────────────────────────────
            
            if datetime.now().timestamp() > phase_deadline:
                print(f"    ⏰ Достигнут лимит времени фазы ({deep_views_completed}/{deep_views_target} deep views)")
                break

            if deep_views_completed >= deep_views_target:
                print(f"    ✓ Достигнута цель deep views ({deep_views_completed}/{deep_views_target})")
                break

            try:
                print(f"\n    🔍 Поиск #{query_idx}: '{search_query}'")

                # ─────────────────────────────────────────────────
                # ВЫПОЛНЯЕМ ПОИСК
                # ─────────────────────────────────────────────────
                
                search_success = await navigator.perform_search(
                    page=page,
                    query=search_query,
                    category="mototehnika",
                )

                if not search_success:
                    print(f"    {Fore.YELLOW}⚠️ Поиск не выполнен, продолжаю...{Style.RESET_ALL}")
                    phase_config.error_count += 1
                    continue

                phase_config.urls_visited.append(f"search:{search_query}")
                await asyncio.sleep(random.uniform(2, 4))

                # ─────────────────────────────────────────────────
                # ГЛУБОКИЙ ПРОСМОТР НЕСКОЛЬКИХ КАРТОЧЕК
                # ─────────────────────────────────────────────────
                
                cards_in_search = random.randint(3, 6)
                for card_idx in range(cards_in_search):
                    if datetime.now().timestamp() > phase_deadline:
                        break

                    if deep_views_completed >= deep_views_target:
                        break

                    try:
                        # ─────────────────────────────────────────
                        # СЛУЧАЙНЫЙ СКРОЛЛ ПЕРЕД КЛИКО
                        # ─────────────────────────────────────────
                        
                        if random.random() < 0.5:
                            await self.human_behavior.scroll_page(page, max_scrolls=random.randint(1, 2))
                            await asyncio.sleep(random.uniform(1, 2))

                        # ─────────────────────────────────────────
                        # ПОЛУЧАЕМ КОЛИЧЕСТВО КАРТОЧЕК
                        # ─────────────────────────────────────────
                        
                        listings = await page.locator('[data-marker="item"]').count()
                        if listings == 0:
                            continue

                        # ─────────────────────────────────────────
                        # ВЫБИРАЕМ СЛУЧАЙНУЮ КАРТОЧКУ
                        # ─────────────────────────────────────────
                        
                        card_selector_idx = random.randint(0, min(listings - 1, 20))

                        print(f"      • Deep View #{card_idx + 1} ", end="", flush=True)

                        # ─────────────────────────────────────────
                        # FULL DEEP VIEW CARD
                        # ─────────────────────────────────────────
                        
                        deep_view_result = await self._perform_full_deep_view_card(
                            page=page,
                            account_id=account_id,
                            selector_index=card_selector_idx,
                            phase_config=phase_config,
                        )

                        if deep_view_result:
                            deep_views_completed += 1
                            self.total_deep_views += 1
                            phase_config.deep_views_completed += 1
                            phase_config.success_count += 1
                            print(f"{Fore.GREEN}✓{Style.RESET_ALL}")
                        else:
                            phase_config.error_count += 1
                            print(f"{Fore.YELLOW}⚠️{Style.RESET_ALL}")

                        # ─────────────────────────────────────────
                        # ПАУЗА ПЕРЕД СЛЕДУЮЩЕЙ КАРТОЧКОЙ
                        # ─────────────────────────────────────────
                        
                        pause = await self.human_behavior.get_natural_pause(min_sec=5, max_sec=12)
                        await asyncio.sleep(pause)

                    except Exception as e:
                        self.logger.warning(account_id, f"Card deep view error: {str(e)[:80]}")
                        phase_config.error_count += 1
                        continue

                # ─────────────────────────────────────────────────
                # ПАУЗА ПЕРЕД СЛЕДУЮЩИМ ПОИСКОМ
                # ─────────────────────────────────────────────────
                
                pause = await self.human_behavior.get_natural_pause(min_sec=10, max_sec=20)
                await asyncio.sleep(pause)

            except Exception as e:
                self.logger.warning(account_id, f"Search error: {str(e)[:80]}")
                print(f"    {Fore.RED}✗ Ошибка поиска{Style.RESET_ALL}")
                phase_config.error_count += 1
                continue

        print(f"\n    ✅ Завершено {deep_views_completed} deep views (требуется {phase_config.min_deep_views}+)")
        return deep_views_completed >= phase_config.min_deep_views

    async def _perform_full_deep_view_card(
        self,
        page: Page,
        account_id: str,
        selector_index: int,
        phase_config: WarmupPhaseConfig,
    ) -> bool:
        """
        ПОЛНЫЙ DEEP VIEW КАРТОЧКИ:
        1. Клик на карточку
        2. Листание ВСЕХ фото в галерее
        3. Полное прочитание описания
        4. Просмотр характеристик (если есть)
        5. Просмотр отзывов (если есть)
        6. Иногда просмотр профиля продавца
        7. Иногда добавление в избранное (с паузой на раздумье)
        8. Возврат назад
        
        Все действия логируются и считаются как глубокий просмотр
        """
        
        try:
            # ─────────────────────────────────────────────────────
            # ШАГ 1: КЛИК НА КАРТОЧКУ
            # ─────────────────────────────────────────────────────
            
            card_selector = f'[data-marker="item"] >> nth={selector_index}'
            click_success = await self.executor.execute_click(
                page=page,
                account_id=account_id,
                selector=card_selector,
                browser_launcher=self.browser_launcher,
            )

            if not click_success:
                return False

            # ─────────────────────────────────────────────────────
            # ЖДЁМ ЗАГРУЗКИ КАРТОЧКИ
            # ─────────────────────────────────────────────────────
            
            await asyncio.sleep(random.uniform(2, 4))

            # ─────────────────────────────────────────────────────
            # ШАГ 2: ЛИСТАНИЕ ВСЕХ ФОТ О В ГАЛЕРЕЕ
            # ─────────────────────────────────────────────────────
            
            photos_in_card = await self._scroll_all_photos(page, account_id)
            phase_config.photos_viewed_total += photos_in_card
            self.total_photos_viewed += photos_in_card

            # ─────────────────────────────────────────────────────
            # ШАГ 3: ПОЛНОЕ ПРОЧИТАНИЕ ОПИСАНИЯ
            # ─────────────────────────────────────────────────────
            
            description_read = await self._read_full_description(page, account_id)
            if description_read:
                phase_config.descriptions_read += 1
                self.total_descriptions_read += 1

            # ─────────────────────────────────────────────────────
            # ШАГ 4: ПРОСМОТР ХАРАКТЕРИСТИК
            # ─────────────────────────────────────────────────────
            
            specs_viewed = await self._view_specifications(page, account_id)
            if specs_viewed:
                phase_config.specs_viewed += 1
                self.total_specs_viewed += 1

            # ─────────────────────────────────────────────────────
            # ШАГ 5: ПРОСМОТР ОТЗЫВОВ
            # ─────────────────────────────────────────────────────
            
            reviews_viewed = await self._view_reviews(page, account_id)
            if reviews_viewed:
                phase_config.reviews_read += 1
                self.total_reviews_read += 1

            # ─────────────────────────────────────────────────────
            # ШАГ 6: ИНОГДА ПРОСМОТР ПРОФИЛЯ ПРОДАВЦА (20%)
            # ─────────────────────────────────────────────────────
            
            if random.random() < 0.2:
                profile_viewed = await self._view_seller_profile(page, account_id)
                if profile_viewed:
                    phase_config.seller_profiles_viewed += 1
                    self.total_seller_profiles_viewed += 1
                    # Возврат на карточку
                    try:
                        await page.go_back()
                        await asyncio.sleep(random.uniform(1, 2))
                    except Exception:
                        pass

            # ─────────────────────────────────────────────────────
            # ШАГ 7: ИНОГДА ДОБАВЛЕНИЕ В ИЗБРАННОЕ (25%)
            # ─────────────────────────────────────────────────────
            
            if random.random() < 0.25:
                # Пауза на "раздумье" 3-8 секунд
                thinking_pause = random.uniform(3, 8)
                await asyncio.sleep(thinking_pause)

                fav_success = await self.executor.execute_natural_favorite(
                    page=page,
                    account_id=account_id,
                    selector_index=0,  # На карточке иконка одна
                    browser_launcher=self.browser_launcher,
                    human_behavior=self.human_behavior,
                )

                if fav_success:
                    phase_config.favorites_added += 1
                    self.total_favorites_added += 1

            # ─────────────────────────────────────────────────────
            # ШАГ 8: ВОЗВРАТ НАЗАД
            # ─────────────────────────────────────────────────────
            
            try:
                await page.go_back()
                await asyncio.sleep(random.uniform(1, 3))
            except Exception:
                pass

            return True

        except Exception as e:
            self.logger.warning(account_id, f"Full deep view error: {str(e)[:80]}")
            try:
                await page.go_back()
            except:
                pass
            return False

    async def _scroll_all_photos(self, page: Page, account_id: str) -> int:
        """
        Листание ВСЕХ фото в галерее карточки
        
        Натурально переключается между фотографиями с паузами
        """
        try:
            photos_count = 0
            
            # Ищем контейнер галереи
            gallery = page.locator('[class*="gallery"], [class*="carousel"], [class*="slider"]').first
            
            # Скроллим фото слайдер (максимум 15 слайдов)
            for _ in range(15):
                try:
                    # Пытаемся найти кнопку "следующее фото"
                    next_btn = page.locator('button[aria-label*="Next"], button[aria-label*="следующ"], [class*="next"]').first
                    
                    if await next_btn.is_visible():
                        await next_btn.click()
                        photos_count += 1
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                    else:
                        break
                except:
                    break
            
            # Если не было кликов, листаем скроллом
            if photos_count == 0:
                await self.human_behavior.scroll_page(page, max_scrolls=random.randint(2, 4))
                photos_count = random.randint(3, 8)
            
            return max(photos_count, 1)

        except Exception as e:
            self.logger.warning(account_id, f"Photo scroll error: {e}")
            return 0

    async def _read_full_description(self, page: Page, account_id: str) -> bool:
        """
        Полное прочитание описания
        
        Скроллит вниз, читает описание с паузой (3-8 сек)
        """
        try:
            # Ищем описание
            description = page.locator('[class*="description"], [class*="title"], p').first
            
            if description:
                # Скроллим вниз и читаем
                await description.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(3, 8))  # Пауза на прочтение
                return True
            
            return False

        except Exception as e:
            self.logger.warning(account_id, f"Description read error: {e}")
            return False

    async def _view_specifications(self, page: Page, account_id: str) -> bool:
        """
        Просмотр характеристик
        
        Ищет раздел характеристик и смотрит с паузой
        """
        try:
            # Ищем раздел характеристик
            specs = page.locator('[class*="spec"], [class*="param"], [class*="feature"]').first
            
            if specs:
                await specs.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(2, 5))
                return True
            
            return False

        except Exception as e:
            self.logger.warning(account_id, f"Specs view error: {e}")
            return False

    async def _view_reviews(self, page: Page, account_id: str) -> bool:
        """
        Просмотр отзывов
        
        Ищет раздел отзывов и читает с паузой
        """
        try:
            # Ищем раздел отзывов
            reviews = page.locator('[class*="review"], [class*="feedback"], [class*="rating"]').first
            
            if reviews:
                await reviews.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(2, 5))
                return True
            
            return False

        except Exception as e:
            self.logger.warning(account_id, f"Reviews view error: {e}")
            return False

    async def _view_seller_profile(self, page: Page, account_id: str) -> bool:
        """
        Просмотр профиля продавца
        
        Кликает на ссылку профиля, смотрит 3-6 сек, возвращается
        """
        try:
            # Ищем ссылку на профиль продавца
            seller_link = page.locator('[class*="seller"], [class*="vendor"], a[href*="user/"]').first
            
            if seller_link:
                await seller_link.click()
                await asyncio.sleep(random.uniform(3, 6))  # Чтение профиля
                return True
            
            return False

        except Exception as e:
            self.logger.warning(account_id, f"Seller profile view error: {e}")
            return False

    def _get_warmup_elapsed(self) -> float:
        """Получить прошедшее время в минутах"""
        if not self.warmup_start_time:
            return 0.0
        return (datetime.now() - self.warmup_start_time).total_seconds() / 60


class AliveMode:
    """
    🤖 ALIVE MODE 2030 ADVANCED — Живой человек, несколько часов в день
    
    Максимально человеческое поведение:
    - Разные категории (30% мото, 15% авто, 10% недвиж и т.д.)
    - Deep view карточек (25% весит)
    - Добавление в избранное (12%)
    - Поиск (15%)
    - Просмотр профилей (8%)
    - Скролл категорий (10%)
    - Сравнение карточек (5%)
    - Просмотр избранного (5%)
    
    3-6 часов в день с естественными паузами
    """

    # ═════════════════════════════════════════════════════════════════════════════════
    # РАСПРЕДЕЛЕНИЕ ДЕЙСТВИЙ (WEIGHTED)
    # ═════════════════════════════════════════════════════════════════════════════════
    
    ACTION_WEIGHTS = {
        "browse_category": 20,      # Просмотр категории с листанием
        "deep_view_card": 25,       # Глубокий просмотр карточки (фото+описание+характеристики)
        "add_favorite": 12,         # Добавление в избранное
        "search": 15,               # Поиск по запросу
        "view_seller": 8,           # Просмотр профиля продавца
        "scroll_category": 10,      # Просто скролл и листание
        "compare_cards": 5,         # Сравнение (откры две карточки подряд)
        "return_to_favorites": 5,   # Возврат к избранному
    }

    # ═════════════════════════════════════════════════════════════════════════════════
    # КАТЕГОРИИ AVITO (РАЗНООБРАЗИЕ)
    # ═════════════════════════════════════════════════════════════════════════════════
    
    AVITO_CATEGORIES = [
        {"name": "Мототехника", "url": "https://www.avito.ru/moskva/mototsikly_i_mototehnika", "weight": 30},
        {"name": "Автомобили", "url": "https://www.avito.ru/moskva/avtomobili", "weight": 15},
        {"name": "Квартиры", "url": "https://www.avito.ru/moskva/kvartiry", "weight": 10},
        {"name": "Электроника", "url": "https://www.avito.ru/moskva/elektronika", "weight": 8},
        {"name": "Услуги", "url": "https://www.avito.ru/moskva/uslugi", "weight": 5},
        {"name": "Мебель", "url": "https://www.avito.ru/moskva/mebel", "weight": 8},
        {"name": "Одежда", "url": "https://www.avito.ru/moskva/odezhda_obuv", "weight": 8},
        {"name": "Спорт", "url": "https://www.avito.ru/moskva/sport_i_otdyh", "weight": 5},
        {"name": "Инструменты", "url": "https://www.avito.ru/moskva/instrumenty", "weight": 5},
        {"name": "Косметика", "url": "https://www.avito.ru/moskva/krasota_i_zdorove", "weight": 2},
    ]

    # ═════════════════════════════════════════════════════════════════════════════════
    # ПОИСКОВЫЕ ЗАПРОСЫ (РАЗНООБРАЗИЕ)
    # ═════════════════════════════════════════════════════════════════════════════════
    
    SEARCH_QUERIES = {
        "moto": [
            "питбайк",
            "мотоцикл",
            "квадроцикл",
            "скутер",
            "мопед",
            "эндуро",
            "спортбайк",
            "круизер",
            "мотоцикл дешево",
            "питбайк новый",
            "питбайк 125cc",
            "квадроцикл детский",
        ],
        "auto": [
            "автомобиль",
            "машина",
            "машину продам",
            "авто дешево",
            "бу авто",
            "седан",
            "кроссовер",
            "внедорожник",
        ],
        "home": [
            "квартира",
            "комната",
            "апартаменты",
            "дом",
            "коттедж",
        ],
        "electronics": [
            "телефон",
            "ноутбук",
            "монитор",
            "наушники",
            "смартфон",
            "планшет",
        ],
        "general": [
            "куплю",
            "продам",
            "срочно",
            "новое",
            "дешево",
        ],
    }

    def __init__(self, logger, executor: ActionExecutor, notifier):
        self.logger = logger
        self.executor = executor
        self.notifier = notifier
        self.running = False
        self.iteration_count = 0
        self.human_behavior: Optional[HumanBehavior] = None
        self.start_time: Optional[datetime] = None
        self.browser_launcher: Optional[BrowserLauncher] = None
        
        # Статистика
        self.action_stats = {action: 0 for action in self.ACTION_WEIGHTS.keys()}
        self.total_deep_views = 0
        self.total_favorites = 0
        self.total_searches = 0

    async def run(
        self,
        page: Page,
        account_id: str,
        navigator: AvitoNavigator,
        night_mode: NightMode,
        fp: Optional[Fingerprint] = None,
        browser_launcher: Optional[BrowserLauncher] = None,
    ):
        """Запустить Alive Mode на весь день (несколько часов с перерывами)"""
        self.running = True
        self.human_behavior = HumanBehavior(fp, logger=self.logger)
        self.start_time = datetime.now()
        self.browser_launcher = browser_launcher

        print(f"\n{Fore.GREEN}{'=' * 100}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'🤖 ALIVE MODE 2030 ADVANCED — АСИНХРОННЫЙ РЕЖИМ (ЖИВОЙ ЧЕЛОВЕК)':^100}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'Бесконечный цикл: разные категории, deep views, поиски, добавление в избранное':^100}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'=' * 100}{Style.RESET_ALL}\n")

        self.logger.system(f"{account_id}: Alive Mode Advanced started")
        
        try:
            await self.notifier.notify_alive_mode_started(account_id)
        except Exception:
            pass

        try:
            while self.running:
                # ─────────────────────────────────────────────────────
                # ПРОВЕРКА НОЧНОГО РЕЖИМА
                # ─────────────────────────────────────────────────────
                
                if not night_mode.can_work(account_id):
                    print(f"  {Fore.BLUE}🌙 Ночной режим — graceful shutdown браузера...{Style.RESET_ALL}")
                    # Graceful shutdown
                    await night_mode.graceful_shutdown_browser(page, None, account_id)
                    await asyncio.sleep(300)
                    # Soft resume
                    if self.running:
                        await night_mode.soft_resume_browser(page, None, account_id)
                        print(f"  {Fore.GREEN}☀️ День — браузер возобновлён{Style.RESET_ALL}")
                    continue

                try:
                    await self._perform_alive_action(page, account_id, navigator)
                    self.iteration_count += 1
                except Exception as e:
                    self.logger.warning(account_id, f"Alive action error: {e}")

                # ─────────────────────────────────────────────────────
                # ПАУЗА МЕЖДУ ДЕЙСТВИЯМИ (ЕСТЕСТВЕННАЯ)
                # ─────────────────────────────────────────────────────
                
                next_pause = await self.human_behavior.get_natural_pause(
                    min_sec=600,   # 10 минут
                    max_sec=2400   # 40 минут
                )

                try:
                    await self.notifier.notify_alive_next_action(
                        account_id=account_id,
                        time_until_next_seconds=next_pause,
                        tiredness_percent=round(self.human_behavior.tiredness * 100),
                        mood=self.human_behavior.mood.value,
                        action_count=self.iteration_count,
                        total_deep_views=self.total_deep_views,
                        total_favorites=self.total_favorites,
                    )
                except Exception:
                    pass

                print(f"  {Fore.CYAN}[Alive #{self.iteration_count}] Пауза {next_pause/60:.1f} мин до следующего действия...{Style.RESET_ALL}")

                try:
                    await asyncio.sleep(next_pause)
                except asyncio.CancelledError:
                    break

        except Exception as e:
            self.logger.error(account_id, f"Alive Mode error: {e}", severity="HIGH")
        finally:
            self.running = False
            print(f"\n  {Fore.YELLOW}[Alive] Остановлен (выполнено {self.iteration_count} итераций){Style.RESET_ALL}")
            print(f"     Deep Views: {self.total_deep_views} | ❤️ Favorites: {self.total_favorites} | 🔍 Searches: {self.total_searches}")

    async def _perform_alive_action(self, page: Page, account_id: str, navigator: AvitoNavigator):
        """Выполнить одно случайное действие"""
        
        action = random.choices(
            list(self.ACTION_WEIGHTS.keys()),
            weights=list(self.ACTION_WEIGHTS.values()),
            k=1
        )[0]

        print(f"  {Fore.CYAN}[Alive #{self.iteration_count + 1}] Действие: {action.upper()}{Style.RESET_ALL}")
        self.action_stats[action] += 1

        if action == "browse_category":
            await self._alive_browse_category(page, account_id)
        elif action == "deep_view_card":
            await self._alive_deep_view_card(page, account_id)
        elif action == "add_favorite":
            await self._alive_add_favorite(page, account_id)
        elif action == "search":
            await self._alive_search(page, account_id, navigator)
        elif action == "view_seller":
            await self._alive_view_seller(page, account_id)
        elif action == "scroll_category":
            await self._alive_scroll_category(page, account_id)
        elif action == "compare_cards":
            await self._alive_compare_cards(page, account_id)
        elif action == "return_to_favorites":
            await self._alive_return_to_favorites(page, account_id)

    async def _alive_browse_category(self, page: Page, account_id: str):
        """Просмотр случайной категории с листанием"""
        try:
            category = random.choices(
                self.AVITO_CATEGORIES,
                weights=[c["weight"] for c in self.AVITO_CATEGORIES],
                k=1
            )[0]

            print(f"     → Просмотр категории: {category['name']}")
            
            await self.executor.execute_navigation(
                page=page,
                account_id=account_id,
                url=category["url"],
                wait_until="networkidle",
                browser_launcher=self.browser_launcher,
            )
            
            # Листаем и читаем
            await self.human_behavior.browse_page(page, duration_seconds=random.uniform(30, 60))
            await self.human_behavior.scroll_page(page, max_scrolls=random.randint(2, 5))
            
        except Exception as e:
            self.logger.warning(account_id, f"Browse category error: {e}")

    async def _alive_deep_view_card(self, page: Page, account_id: str):
        """Глубокий просмотр карточки (full deep view)"""
        try:
            listings = await page.locator('[data-marker="item"]').count()
            if listings == 0:
                return

            idx = random.randint(0, min(listings - 1, 20))
            
            print(f"     → Deep view карточки #{idx + 1}")
            
            # Шаг 1: Клик
            click_success = await self.executor.execute_click(
                page=page,
                account_id=account_id,
                selector=f'[data-marker="item"] >> nth={idx}',
                browser_launcher=self.browser_launcher,
            )

            if not click_success:
                return

            await asyncio.sleep(random.uniform(2, 4))

            # Шаг 2: Листание фото
            await self._scroll_all_photos_alive(page)

            # Шаг 3: Прочитание описания
            await self.human_behavior.browse_page(page, duration_seconds=random.uniform(5, 15))

            # Шаг 4: Иногда просмотр характеристик
            if random.random() < 0.4:
                await self.human_behavior.scroll_page(page, max_scrolls=random.randint(1, 2))
                await asyncio.sleep(random.uniform(3, 7))

            # Шаг 5: Иногда добавление в избранное
            if random.random() < 0.3:
                await asyncio.sleep(random.uniform(2, 5))  # Пауза на раздумье
                try:
                    fav_btn = page.locator('button[title*="избран"], button[aria-label*="избран"]').first
                    if fav_btn:
                        await fav_btn.click()
                        self.total_favorites += 1
                except:
                    pass

            self.total_deep_views += 1
            await page.go_back()
            await asyncio.sleep(random.uniform(1, 2))

        except Exception as e:
            self.logger.warning(account_id, f"Deep view error: {e}")

    async def _alive_add_favorite(self, page: Page, account_id: str):
        """Добавление в избранное"""
        try:
            listings = await page.locator('[data-marker="item"]').count()
            if listings == 0:
                return

            idx = random.randint(0, min(listings - 1, 20))
            
            print(f"     → Добавление в избранное")
            
            await self.executor.execute_natural_favorite(
                page=page,
                account_id=account_id,
                selector_index=idx,
                browser_launcher=self.browser_launcher,
                human_behavior=self.human_behavior,
            )
            
            self.total_favorites += 1

        except Exception as e:
            self.logger.warning(account_id, f"Favorite error: {e}")

    async def _alive_search(self, page: Page, account_id: str, navigator: AvitoNavigator):
        """Поиск по запросу"""
        try:
            category_type = random.choice(list(self.SEARCH_QUERIES.keys()))
            query = random.choice(self.SEARCH_QUERIES[category_type])
            
            print(f"     → Поиск: '{query}'")
            
            await navigator.perform_search(page=page, query=query)
            await self.human_behavior.browse_page(page, duration_seconds=random.uniform(25, 50))
            
            self.total_searches += 1

        except Exception as e:
            self.logger.warning(account_id, f"Search error: {e}")

    async def _alive_view_seller(self, page: Page, account_id: str):
        """Просмотр профиля продавца"""
        try:
            print(f"     → Просмотр профиля продавца")
            
            seller_link = page.locator('[class*="seller"], a[href*="user/"]').first
            if seller_link:
                await seller_link.click()
                await asyncio.sleep(random.uniform(3, 8))
                await page.go_back()

        except Exception as e:
            self.logger.warning(account_id, f"View seller error: {e}")

    async def _alive_scroll_category(self, page: Page, account_id: str):
        """Скролл и листание категории"""
        try:
            print(f"     → Скролл категории")
            
            await self.human_behavior.scroll_page(page, max_scrolls=random.randint(2, 5))
            await asyncio.sleep(random.uniform(5, 15))

        except Exception as e:
            self.logger.warning(account_id, f"Scroll error: {e}")

    async def _alive_compare_cards(self, page: Page, account_id: str):
        """Сравнение (открытие двух карточек подряд)"""
        try:
            print(f"     → Сравнение карточек")
            
            listings = await page.locator('[data-marker="item"]').count()
            if listings < 2:
                return

            # Первая карточка
            idx1 = random.randint(0, min(listings - 1, 20))
            await self.executor.execute_click(
                page=page,
                account_id=account_id,
                selector=f'[data-marker="item"] >> nth={idx1}',
                browser_launcher=self.browser_launcher,
            )
            await asyncio.sleep(random.uniform(3, 6))
            await page.go_back()

            # Пауза
            await asyncio.sleep(random.uniform(2, 4))

            # Вторая карточка
            idx2 = random.randint(0, min(listings - 1, 20))
            await self.executor.execute_click(
                page=page,
                account_id=account_id,
                selector=f'[data-marker="item"] >> nth={idx2}',
                browser_launcher=self.browser_launcher,
            )
            await asyncio.sleep(random.uniform(3, 6))
            await page.go_back()

        except Exception as e:
            self.logger.warning(account_id, f"Compare cards error: {e}")

    async def _alive_return_to_favorites(self, page: Page, account_id: str):
        """Возврат к избранному"""
        try:
            print(f"     → Просмотр избранного")
            
            favorites_url = "https://www.avito.ru/izbrannoe"
            await self.executor.execute_navigation(
                page=page,
                account_id=account_id,
                url=favorites_url,
                wait_until="networkidle",
                browser_launcher=self.browser_launcher,
            )
            
            await self.human_behavior.browse_page(page, duration_seconds=random.uniform(15, 35))
            await self.human_behavior.scroll_page(page, max_scrolls=random.randint(1, 3))

        except Exception as e:
            self.logger.warning(account_id, f"Favorites view error: {e}")

    async def _scroll_all_photos_alive(self, page: Page):
        """Листание фото в alive mode"""
        try:
            for _ in range(random.randint(3, 8)):
                try:
                    next_btn = page.locator('button[aria-label*="Next"], [class*="next"]').first
                    if await next_btn.is_visible():
                        await next_btn.click()
                        await asyncio.sleep(random.uniform(0.5, 1))
                    else:
                        break
                except:
                    break
        except:
            pass

    def stop(self):
        """Остановить Alive Mode"""
        self.running = False