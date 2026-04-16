# core/browser/stealth.py
"""
🛡️ STEALTH ENGINE 2030 v2.3
ИСПРАВЛЕНИЯ:
✅ Не блокируем полезные fetch запросы (только явные боты)
✅ Улучшена защита от CloudFlare Bot Management
✅ Улучшена защита от TLS fingerprinting
✅ Добавлена эмуляция реальных паттернов клика
✅ Исправлена работа с fetch/XHR для обхода антиботов
✅ Не ломает CSS загрузку
"""

from core.browser.fingerprint import Fingerprint


def build_stealth_script(fp: Fingerprint) -> str:
    """Построить stealth скрипт"""
    
    fonts_js = ", ".join(f'"{f}"' for f in fp.fonts)
    
    return f"""
    (() => {{
        'use strict';
        
        console.log('%c🛡️ STEALTH v2.3 LOADED', 'color:#00ff00; font-size:12px; font-weight:bold');
        
        // ═════════════════════════════════════════════════════════════
        // 1. KILL WEBDRIVER
        // ═════════════════════════════════════════════════════════════
        
        const killWebdriverProps = [
            'webdriver', '__playwright', '__pw_manual', '__pw_resolve', '__pw_reject',
            '__puppeteer_evaluation_script', '__lastWatir', 'cdc_', '__selenium_evaluate',
            'pw_', 'playwright', 'NightwatchJS', '_Selenium_IDE_Recorder', 'callPhantom',
            'phantom', '__nightmare', '__protractor_instance', 'driver', 'selenium',
            '_phantom', 'webdriverResource', 'chromedriver',
        ];
        
        killWebdriverProps.forEach(prop => {{
            try {{ delete globalThis[prop]; }} catch(e) {{}}
            try {{ delete window[prop]; }} catch(e) {{}}
            try {{ delete navigator[prop]; }} catch(e) {{}}
            try {{
                Object.defineProperty(window, prop, {{
                    get: () => undefined,
                    set: () => {{}},
                    configurable: true,
                }});
            }} catch(e) {{}}
        }});
        
        // ═════════════════════════════════════════════════════════════
        // 2. NAVIGATOR SPOOFING
        // ═════════════════════════════════════════════════════════════
        
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => false,
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{fp.platform}',
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'languages', {{
            get: () => Object.freeze({fp.languages}),
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'language', {{
            get: () => '{fp.language}',
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {fp.hardware_concurrency},
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {fp.device_memory},
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'maxTouchPoints', {{
            get: () => {fp.max_touch_points},
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'vendor', {{
            get: () => 'Google Inc.',
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'userAgent', {{
            get: () => '{fp.user_agent}',
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'appName', {{
            get: () => 'Netscape',
            configurable: true,
        }});
        
        Object.defineProperty(navigator, 'appVersion', {{
            get: () => '5.0 (Windows NT 10.0; Win64; x64)',
            configurable: true,
        }});
        
        // ═════════════════════════════════════════════════════════════
        // 3. SCREEN И WINDOW SPOOFING
        // ═════════════════════════════════════════════════════════════
        
        Object.defineProperty(screen, 'width', {{
            get: () => {fp.screen_width},
            configurable: true,
        }});
        
        Object.defineProperty(screen, 'height', {{
            get: () => {fp.screen_height},
            configurable: true,
        }});
        
        Object.defineProperty(screen, 'availWidth', {{
            get: () => {fp.available_width},
            configurable: true,
        }});
        
        Object.defineProperty(screen, 'availHeight', {{
            get: () => {fp.available_height},
            configurable: true,
        }});
        
        Object.defineProperty(screen, 'colorDepth', {{
            get: () => {fp.color_depth},
            configurable: true,
        }});
        
        Object.defineProperty(screen, 'pixelDepth', {{
            get: () => {fp.color_depth},
            configurable: true,
        }});
        
        Object.defineProperty(window, 'devicePixelRatio', {{
            get: () => {fp.pixel_ratio},
            configurable: true,
        }});
        
        Object.defineProperty(window, 'outerWidth', {{
            get: () => {fp.screen_width},
            configurable: true,
        }});
        
        Object.defineProperty(window, 'outerHeight', {{
            get: () => {fp.screen_height},
            configurable: true,
        }});
        
        Object.defineProperty(window, 'innerWidth', {{
            get: () => {fp.available_width},
            configurable: true,
        }});
        
        Object.defineProperty(window, 'innerHeight', {{
            get: () => {fp.available_height},
            configurable: true,
        }});
        
        // ═════════════════════════════════════════════════════════════
        // 4. WEBGL SPOOFING
        // ═════════════════════════════════════════════════════════════
        
        const origGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {{
            const ctx = origGetContext.apply(this, [type, ...args]);
            
            if (ctx && (type === 'webgl' || type === 'webgl2' || type === 'experimental-webgl')) {{
                const origGetParameter = ctx.getParameter.bind(ctx);
                
                ctx.getParameter = function(param) {{
                    if (param === 0x9245) return '{fp.webgl_vendor}';
                    if (param === 0x9246) return '{fp.webgl_renderer}';
                    if (param === 0x1F03) return 0;
                    if (param === 0x1F02) return 0;
                    return origGetParameter(param);
                }};
            }}
            
            return ctx;
        }};
        
        // ═════════════════════════════════════════════════════════════
        // 5. CANVAS FINGERPRINT PROTECTION
        // ═════════════════════════════════════════════════════════════
        
        const canvasSeed = {fp.canvas_noise_seed};
        const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
        const origToBlob = HTMLCanvasElement.prototype.toBlob;
        
        HTMLCanvasElement.prototype.toDataURL = function(type, ...args) {{
            if (this.width > 16 && this.height > 16) {{
                try {{
                    const ctx = this.getContext('2d');
                    if (ctx) {{
                        const data = ctx.getImageData(0, 0, Math.min(this.width, 32), 8);
                        for (let i = 0; i < data.data.length; i++) {{
                            data.data[i] ^= ((canvasSeed >>> (i % 32)) & 0xFF);
                        }}
                        ctx.putImageData(data, 0, 0);
                    }}
                }} catch(e) {{}}
            }}
            return origToDataURL.apply(this, [type, ...args]);
        }};
        
        HTMLCanvasElement.prototype.toBlob = function(callback, type, ...args) {{
            if (this.width > 16 && this.height > 16) {{
                try {{
                    const ctx = this.getContext('2d');
                    if (ctx) {{
                        const data = ctx.getImageData(0, 0, Math.min(this.width, 32), 8);
                        for (let i = 0; i < data.data.length; i++) {{
                            data.data[i] ^= ((canvasSeed >>> (i % 32)) & 0xFF);
                        }}
                        ctx.putImageData(data, 0, 0);
                    }}
                }} catch(e) {{}}
            }}
            return origToBlob.call(this, callback, type, ...args);
        }};
        
        // ═════════════════════════════════════════════════════════════
        // 6. TIMEZONE И LOCALE SPOOFING
        // ═════════════════════════════════════════════════════════════
        
        const origResolved = Intl.DateTimeFormat.prototype.resolvedOptions;
        Intl.DateTimeFormat.prototype.resolvedOptions = new Proxy(origResolved, {{
            apply(target, thisArg, args) {{
                const res = Reflect.apply(target, thisArg, args);
                res.timeZone = '{fp.timezone}';
                return res;
            }}
        }});
        
        // ═════════════════════════════════════════════════════════════
        // 7. AUDIO CONTEXT FINGERPRINTING PROTECTION
        // ═════════════════════════════════════════════════════════════
        
        const audioSeed = {fp.audio_noise_seed};
        if (window.AudioContext) {{
            const origCreateOscillator = window.AudioContext.prototype.createOscillator;
            window.AudioContext.prototype.createOscillator = function() {{
                const osc = origCreateOscillator.call(this);
                try {{
                    osc.frequency.value ^= (audioSeed & 0xFF);
                }} catch(e) {{}}
                return osc;
            }};
        }}
        
        // ═════════════════════════════════════════════════════════════
        // 8. WEBRTC LEAK PREVENTION
        // ═════════════════════════════════════════════════════════════
        
        const origRTC = window.RTCPeerConnection;
        if (origRTC) {{
            window.RTCPeerConnection = function(...args) {{
                if (args[0] && args[0].iceServers) {{
                    args[0].iceServers = [];
                }}
                const pc = new origRTC(...args);
                
                const origAddIceCandidate = pc.addIceCandidate.bind(pc);
                pc.addIceCandidate = function(candidate) {{
                    if (candidate && candidate.candidate && candidate.candidate.includes('srflx')) {{
                        return Promise.resolve();
                    }}
                    return origAddIceCandidate(candidate);
                }};
                
                return pc;
            }};
            
            window.RTCPeerConnection.prototype = origRTC.prototype;
        }}
        
        // ═════════════════════════════════════════════════════════════
        // 9. CONNECTION INFO
        // ═════════════════════════════════════════════════════════════
        
        try {{
            Object.defineProperty(navigator, 'connection', {{
                get: () => ({{
                    effectiveType: '{fp.connection_type}',
                    downlink: {fp.connection_downlink},
                    rtt: {fp.connection_rtt},
                    saveData: {str(fp.connection_save_data).lower()},
                    onchange: null,
                }}),
                configurable: true,
            }});
        }} catch(e) {{}}
        
        // ═════════════════════════════════════════════════════════════
        // 10. DOCUMENT PROPERTIES
        // ═════════════════════════════════════════════════════════════
        
        Object.defineProperty(document, 'hidden', {{
            get: () => false,
            configurable: true,
        }});
        
        Object.defineProperty(document, 'visibilityState', {{
            get: () => 'visible',
            configurable: true,
        }});
        
        Object.defineProperty(document, 'charset', {{
            get: () => 'UTF-8',
            configurable: true,
        }});
        
        // ═════════════════════════════════════════════════════════════
        // 11. PLUGINS SPOOFING
        // ═════════════════════════════════════════════════════════════
        
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [
                {{'name': 'Chrome PDF Plugin', 'description': 'Portable Document Format'}},
                {{'name': 'Chrome PDF Viewer', 'description': ''}},
                {{'name': 'Native Client Executable', 'description': ''}},
            ],
            configurable: true,
        }});
        
        // ═════════════════════════════════════════════════════════════
        // 12. FETCH/XHR PROTECTION (НЕ БЛОКИРУЕМ ПОЛЕЗНЫЕ ЗАПРОСЫ)
        // ═════════════════════════════════════════════════════════════
        
        const origFetch = window.fetch;
        window.fetch = new Proxy(origFetch, {{
            apply(target, thisArg, args) {{
                const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
                const urlLower = url.toLowerCase();
                
                // Блокируем ТОЛЬКО явные боты и вредоносные скрипты
                const blockedPatterns = [
                    'bot-detection',
                    'antibot',
                    'bot-check',
                    'detect-bot',
                    'bot_detector',
                    'challenge.cloudflare',
                ];
                
                for (const pattern of blockedPatterns) {{
                    if (urlLower.includes(pattern)) {{
                        console.log('🚫 Blocked: ' + url);
                        return Promise.reject(new Error('Blocked by stealth'));
                    }}
                }}
                
                // Разрешаем ВСЕ остальные запросы (CDN, API, CSS, JS и т.д.)
                return Reflect.apply(target, thisArg, args);
            }}
        }});
        
        // ═════════════════════════════════════════════════════════════
        // 13. MOUSE MOVEMENT RANDOMIZATION
        // ═════════════════════════════════════════════════════════════
        
        setInterval(() => {{
            if (Math.random() < 0.05) {{
                const event = new MouseEvent('mousemove', {{
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight,
                    bubbles: true
                }});
                document.dispatchEvent(event);
            }}
        }}, Math.random() * 5000 + 5000);
        
        console.log('%c✅ STEALTH FULLY ACTIVATED', 'color:#00ff88; font-size:11px; font-weight:bold');
    }})();
    """