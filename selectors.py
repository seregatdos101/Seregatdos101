# core/avito/selectors.py
"""
🎯 AVITO SELECTORS — Селекторы для всех элементов Avito
"""


class AvitoUrls:
    """URL адреса Avito"""
    BASE = "https://www.avito.ru"
    LOGIN = "https://www.avito.ru/login"
    PROFILE = "https://www.avito.ru/profile"
    FAVORITES = "https://www.avito.ru/favorites"
    MESSAGES = "https://www.avito.ru/messages"
    SETTINGS = "https://www.avito.ru/profile/settings"
    MY_ITEMS = "https://www.avito.ru/profile/items"


class AvitoSelectors:
    """CSS селекторы элементов Avito"""
    
    # ──── ЛОГИН ────
    LOGIN_BUTTON = '[data-marker="login-button"]'
    LOGIN_BUTTON_ALT = 'a[href*="/login"]'
    LOGIN_PHONE_INPUT = 'input[data-marker="input/phone"]'
    LOGIN_PHONE_ALT = 'input[type="tel"]'
    LOGIN_SUBMIT = 'button[data-marker="submit-button"]'
    LOGIN_SUBMIT_ALT = 'button[type="submit"]'
    LOGIN_CODE_INPUT = 'input[data-marker="code-input"]'
    
    # ──── ОБЪЯВЛЕНИЯ ────
    LISTING_ITEM = '[data-marker="item"]'
    LISTING_TITLE = '[data-marker="item/title"]'
    LISTING_PRICE = '[data-marker="item/price"]'
    LISTING_IMAGE = '[data-marker="item/image"]'
    LISTING_LINK = '[data-marker="item/link"]'
    
    # ──── ПРОФИЛЬ ────
    PROFILE_NAME = '[data-marker="profile/name"]'
    PROFILE_RATING = '[data-marker="profile/rating"]'
    PROFILE_AVATAR = '[data-marker="profile/avatar"]'
    PROFILE_SETTINGS = 'a[href*="/profile/settings"]'
    
    # ──── ИЗБРАННОЕ ────
    FAVORITE_BUTTON = '[data-marker="favorite-button"]'
    FAVORITE_HEART = '.favorites-heart'
    FAVORITE_ADDED = '[data-marker="favorite/added"]'
    
    # ──── ПОИСК ────
    SEARCH_INPUT = 'input[data-marker="search-form/suggest"]'
    SEARCH_SUBMIT = 'button[data-marker="search-form/submit"]'
    SEARCH_FILTER = '[data-marker="filter"]'
    
    # ──── СООБЩЕНИЯ ���───
    MESSENGER_INPUT = '[data-marker="messenger/input"]'
    MESSENGER_SUBMIT = '[data-marker="messenger/submit"]'
    MESSENGER_MESSAGE = '[data-marker="messenger/message"]'
    
    # ──── КАТЕГОРИИ ────
    CATEGORY_LINK = '[data-marker="category-link"]'
    SUBCATEGORY_LINK = '[data-marker="subcategory-link"]'
    
    # ──── ИНФОРМАЦИЯ О ПРОДАВЦЕ ────
    SELLER_NAME = '[data-marker="seller-info/name"]'
    SELLER_RATING = '[data-marker="seller-info/rating"]'
    SELLER_REVIEWS = '[data-marker="seller-info/reviews"]'
    
    # ──── КАПЧА ────
    CAPTCHA_IFRAME = 'iframe[title="reCAPTCHA"]'
    CAPTCHA_CONTAINER = '.g-recaptcha'
    
    # ──── БЛОКИРОВКА ────
    BAN_MESSAGE = '[data-marker="error/ban"]'
    BLOCK_MESSAGE = '.blocked-account'
    VERIFICATION_MESSAGE = '[data-marker="verification"]'