"""
💰 TeleCoin Pro — Premium FinTech Market Terminal
Version: 6.4 — 40 markets + Auto-Update
File: 1.py
"""
import tkinter as tk
from tkinter import font as tkfont, ttk
import customtkinter as ctk
from PIL import Image
import requests
import threading
import re
import os
import json
import queue
import time
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


# ═══════════════════════════════════════════════════════════════
# 🔔 NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════
try:
    from plyer import notification as plyer_notify
    HAS_PLYER = True
except Exception:
    HAS_PLYER = False

try:
    from win10toast import ToastNotifier
    _toaster = ToastNotifier()
    HAS_WIN10 = True
except Exception:
    HAS_WIN10 = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except Exception:
    HAS_BS4 = False


# ═══════════════════════════════════════════════════════════════
# 🔊 SOUND MANAGER
# ═══════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "sounds")
os.makedirs(SOUNDS_DIR, exist_ok=True)

try:
    import pygame
    try:
        pygame.mixer.init()
        HAS_PYGAME = True
    except Exception:
        HAS_PYGAME = False
except Exception:
    HAS_PYGAME = False

try:
    import winsound
    HAS_WINSOUND = True
except Exception:
    HAS_WINSOUND = False


class SoundManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.enabled = True
        self.volume = 0.7
        self._last_play = 0
        self._min_interval = 0.6

    def _find(self, name):
        for ext in [".mp3", ".wav", ".ogg", ".m4a"]:
            p = os.path.join(SOUNDS_DIR, name + ext)
            if os.path.exists(p):
                return p
        return None

    def play(self, name="update", blocking=False):
        if not self.enabled or self.volume <= 0.0:
            return
        now = time.time()
        if now - self._last_play < self._min_interval:
            return
        self._last_play = now
        path = self._find(name)
        if not path:
            self._beep()
            return
        if blocking:
            self._play(path)
        else:
            threading.Thread(target=self._play, args=(path,), daemon=True).start()

    def _play(self, path):
        if HAS_PYGAME:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(40)
                return
            except Exception:
                pass
        if HAS_WINSOUND and path.lower().endswith(".wav"):
            try:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            except Exception:
                pass
        self._beep()

    def _beep(self):
        try:
            if HAS_WINSOUND:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def set_enabled(self, v):
        self.enabled = bool(v)

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, float(v)))
        if HAS_PYGAME:
            try:
                pygame.mixer.music.set_volume(self.volume)
            except Exception:
                pass


sound = SoundManager()


# ═══════════════════════════════════════════════════════════════
# 🎨 DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════
C = {
    "bg":            "#05070D",
    "bg2":           "#080C14",
    "bg3":           "#0D1220",
    "card":          "#0E1421",
    "card_hover":    "#131B2C",
    "card_active":   "#172138",
    "card_border":   "#1A2438",
    "inner":         "#0A1018",
    "inner_border":  "#182238",
    "gold":          "#D4AF37",
    "gold_hi":       "#F5C542",
    "gold_dark":     "#A67C00",
    "cyan":          "#22D3EE",
    "cyan_dark":     "#0891B2",
    "success":       "#10B981",
    "success_dark":  "#059669",
    "danger":        "#F43F5E",
    "danger_dark":   "#E11D48",
    "warning":       "#F59E0B",
    "purple":        "#A855F7",
    "text":          "#F1F5F9",
    "text2":         "#CBD5E1",
    "text3":         "#7B8AA8",
    "text4":         "#495672",
    "divider":       "#1A2438",
    "scroll":        "#1A2438",
    "topbar":        "#0B111C",
}


# ═══════════════════════════════════════════════════════════════
# 🔤 FONTS
# ═══════════════════════════════════════════════════════════════
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)

VAZIR_FONTS = {
    "Vazirmatn-Regular.ttf":
        "https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Regular.ttf",
    "Vazirmatn-Bold.ttf":
        "https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Bold.ttf",
}


def download_fonts_if_needed():
    for fname, url in VAZIR_FONTS.items():
        path = os.path.join(FONTS_DIR, fname)
        if os.path.exists(path):
            continue
        try:
            print(f"  ⬇  دانلود {fname} ...")
            r = requests.get(url, timeout=20)
            if r.ok:
                with open(path, "wb") as f:
                    f.write(r.content)
        except Exception as e:
            print(f"  ✕ خطا: {e}")


def register_fonts():
    try:
        import ctypes
        FR_PRIVATE = 0x10
        for fname in os.listdir(FONTS_DIR):
            if fname.lower().endswith((".ttf", ".otf")):
                path = os.path.join(FONTS_DIR, fname)
                ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0)
    except Exception:
        pass


def detect_font():
    try:
        families = set(tkfont.families())
    except Exception:
        families = set()
    for name in ["Vazirmatn", "Vazir", "IRANSans", "Shabnam",
                 "Sahel", "Segoe UI", "Tahoma", "Arial"]:
        if name in families:
            return name
    return "Tahoma"


FONT = "Tahoma"

def F(size=11, weight="normal"):
    return (FONT, size, weight)


# ═══════════════════════════════════════════════════════════════
# 💾 CONFIG
# ═══════════════════════════════════════════════════════════════
ICONS_DIR = os.path.join(BASE_DIR, "icons")
UI_ICONS_DIR = os.path.join(ICONS_DIR, "ui")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(UI_ICONS_DIR, exist_ok=True)


def load_config():
    defaults = {
        "favorites": [],
        "notifications": True,
        "sound": True,
        "volume": 70,
        "auto_refresh": 60,
    }
    try:
        if not os.path.exists(CONFIG_FILE):
            return defaults
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        favs = data.get("favorites", [])
        if not isinstance(favs, list):
            favs = []
        favs = [f for f in favs if isinstance(f, str)]

        def safe_bool(v, d):
            try:
                return bool(v)
            except Exception:
                return d

        def safe_int(v, d, lo=None, hi=None):
            try:
                n = int(v)
                if lo is not None:
                    n = max(n, lo)
                if hi is not None:
                    n = min(n, hi)
                return n
            except Exception:
                return d

        return {
            "favorites": favs,
            "notifications": safe_bool(data.get("notifications", True), True),
            "sound": safe_bool(data.get("sound", True), True),
            "volume": safe_int(data.get("volume", 70), 70, 0, 100),
            "auto_refresh": safe_int(data.get("auto_refresh", 60), 60, 0, 3600),
        }
    except Exception:
        return defaults


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
# 🖼️ ICONS
# ═══════════════════════════════════════════════════════════════
_icon_cache = {}

def load_icon(key, size=(40, 40), subfolder=None):
    ck = f"{subfolder or ''}_{key}_{size[0]}x{size[1]}"
    if ck in _icon_cache:
        return _icon_cache[ck]
    base = os.path.join(ICONS_DIR, subfolder) if subfolder else ICONS_DIR
    for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
        path = os.path.join(base, key + ext)
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA")
                img = img.resize(size, Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=size)
                _icon_cache[ck] = ctk_img
                return ctk_img
            except Exception:
                pass
    return None


# ═══════════════════════════════════════════════════════════════
# 🔧 UTILS
# ═══════════════════════════════════════════════════════════════
FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

def to_en(s):
    if s is None:
        return ""
    return str(s).translate(FA_DIGITS)

def to_fa(s):
    if s is None:
        return ""
    return str(s).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def hex_alpha(hex_color, alpha=0.5, bg="#05070D"):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    bh = bg.lstrip("#")
    br, bg_, bb = int(bh[0:2], 16), int(bh[2:4], 16), int(bh[4:6], 16)
    nr = int(r * alpha + br * (1 - alpha))
    ng = int(g * alpha + bg_ * (1 - alpha))
    nb = int(b * alpha + bb * (1 - alpha))
    return f"#{nr:02x}{ng:02x}{nb:02x}"

def fmt_price(n):
    if n is None:
        return "—"
    try:
        if isinstance(n, float) and not n.is_integer():
            s = f"{n:,.2f}"
        else:
            s = f"{int(n):,}"
    except Exception:
        s = str(n)
    return to_fa(s)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36",
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
}

_session = requests.Session()
_session.headers.update(HEADERS)
_session.mount("https://", requests.adapters.HTTPAdapter(
    pool_connections=20, pool_maxsize=20, max_retries=1
))


# ═══════════════════════════════════════════════════════════════
# 📱 NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════
def send_native_notification(title, message, timeout=5):
    try:
        if HAS_PLYER:
            plyer_notify.notify(title=title, message=message,
                                 app_name="TeleCoin Pro", timeout=timeout)
            return True
    except Exception:
        pass
    try:
        if HAS_WIN10:
            _toaster.show_toast(title, message, duration=timeout, threaded=True)
            return True
    except Exception:
        pass
    return False


# ═══════════════════════════════════════════════════════════════
# 🌐 NOBITEX API (Crypto)
# ═══════════════════════════════════════════════════════════════
def get_nobitex_stats(symbol):
    try:
        url = f"https://apiv2.nobitex.ir/market/stats?srcCurrency={symbol}&dstCurrency=rls"
        r = _session.get(url, headers={"Accept": "application/json"}, timeout=10)
        if not r.ok:
            return None
        data = r.json()
        if data.get("status") != "ok":
            return None
        stats = data.get("stats", {}).get(f"{symbol}-rls")
        if not stats:
            return None

        def to_toman(v):
            try:
                return int(float(v)) // 10
            except Exception:
                return None

        latest = to_toman(stats.get("latest"))
        if not latest:
            return None
        change_pct = float(stats.get("dayChange", 0) or 0)
        return {
            "price": latest,
            "change_pct": change_pct,
            "high": to_toman(stats.get("dayHigh")),
            "low": to_toman(stats.get("dayLow")),
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# 🌐 ARZDIGITAL — منبع اصلی قیمت
# ═══════════════════════════════════════════════════════════════
ARZDIGITAL_MAP = {
    # ── ارزهای اصلی ──
    "dolar":    ("currencies", "united-states-dollar"),
    "eur":      ("currencies", "euro"),
    "gbp":      ("currencies", "pound-sterling"),
    "chf":      ("currencies", "swiss-franc"),

    # ── ارزهای محبوب ──
    "aed":      ("currencies", "united-arab-emirates-dirham"),
    "try":      ("currencies", "turkish-lira"),
    "cny":      ("currencies", "chinese-yuan"),
    "cad":      ("currencies", "canadian-dollar"),
    "jpy":      ("currencies", "japanese-yen"),
    "aud":      ("currencies", "australian-dollar"),
    "iqd":      ("currencies", "iraqi-dinar"),

    # ── سایر ارزها ──
    "krw":      ("currencies", "south-korean-won"),
    "nzd":      ("currencies", "new-zealand-dollar"),
    "sgd":      ("currencies", "singapore-dollar"),
    "inr":      ("currencies", "indian-rupee"),
    "pkr":      ("currencies", "pakistani-rupee"),
    "rub":      ("currencies", "russian-ruble"),
    "gel":      ("currencies", "georgian-lari"),
    "sar":      ("currencies", "saudi-riyal"),
    "qar":      ("currencies", "qatari-rial"),
    "omr":      ("currencies", "omani-rial"),
    "tnd":      ("currencies", "tunisian-dinar"),
    "mad":      ("currencies", "moroccan-dirham"),
    "khr":      ("currencies", "cambodian-riel"),
    "ves":      ("currencies", "sovereign-bolivar"),
    "jod":      ("currencies", "jordanian-dinar"),
    "bhd":      ("currencies", "bahraini-dinar"),
    "kwd":      ("currencies", "kuwaiti-dinar"),
    "afn":      ("currencies", "afghan-afghani"),
    "azn":      ("currencies", "azerbaijani-manat"),
    "nok":      ("currencies", "norwegian-krone"),

    # ── طلا و سکه ──
    "gold":     ("gold", "gold-gerami-18"),
    "sekeb":    ("gold-coins", "azadi-gold-full"),
}


def parse_numeric_price(value):
    if value is None:
        return None
    v = to_en(str(value))
    v = v.replace("٫", ".").replace("٬", "").replace(",", "")
    v = re.sub(r"[^0-9.]", "", v)
    if not v or v == ".":
        return None
    try:
        if v.count(".") > 1:
            parts = v.split(".")
            v = parts[0] + "." + "".join(parts[1:])
        n = float(v)
        return n if n > 0 else None
    except ValueError:
        return None


def get_arzdigital_data(item_key):
    """Returns: (price, change_pct) یا (None, None)"""
    try:
        info = ARZDIGITAL_MAP.get(item_key)
        if not info:
            return None, None

        path_type, az_slug = info
        url = f"https://arzdigital.com/{path_type}/{az_slug}/"
        r = _session.get(url, timeout=(6, 15))
        if not r.ok:
            return None, None
        r.encoding = "utf-8"
        html = r.text

        price = None
        change_pct = None

        if HAS_BS4:
            soup = BeautifulSoup(html, "lxml")

            meta = soup.find("meta", property="og:description")
            if meta:
                content = meta.get("content", "")
                m = re.search(
                    r'([\d۰-۹][\d۰-۹,٬\.]*)\s*(?:تومان|ت\b)', content
                )
                if m:
                    n = parse_numeric_price(m.group(1))
                    if n and n > 0.01:
                        price = n
                m2 = re.search(r'(-?[\d۰-۹\.]+)\s*%', content)
                if m2:
                    try:
                        change_pct = float(to_en(m2.group(1)))
                    except Exception:
                        pass

            if price is None:
                for el in soup.find_all(attrs={"data-price": True}):
                    n = parse_numeric_price(el.get("data-price"))
                    if n and 0.01 < n < 1_000_000_000:
                        price = n
                        break

            if price is None:
                for cls in ["arz-main-price", "main-price", "price-value",
                            "arz-price", "current-price", "price-box"]:
                    el = soup.find(class_=cls)
                    if el:
                        n = parse_numeric_price(el.get_text(strip=True))
                        if n and 0.01 < n < 1_000_000_000:
                            price = n
                            break

            if price is None:
                for tag in soup.find_all(["h1", "h2", "span"], limit=100):
                    txt = tag.get_text(strip=True)
                    m = re.search(
                        r'([\d۰-۹][\d۰-۹,٬\.]{1,})\s*(?:تومان|ت\b)', txt
                    )
                    if m:
                        n = parse_numeric_price(m.group(1))
                        if n and 0.01 < n < 1_000_000_000:
                            price = n
                            break

            if price is None:
                m = re.search(
                    r'قیمت[^<]{0,120}?([\d۰-۹][\d۰-۹,٬\.]{1,})\s*(?:تومان|ت\b)',
                    html
                )
                if m:
                    n = parse_numeric_price(m.group(1))
                    if n and 0.01 < n < 1_000_000_000:
                        price = n

            if change_pct is None:
                for tag in soup.find_all(["span", "div"], limit=200):
                    txt = tag.get_text(strip=True)
                    m = re.search(r'^(-?[\d۰-۹]+\.?[\d۰-۹]*)\s*%$', txt)
                    if m:
                        try:
                            val = float(to_en(m.group(1)))
                            if abs(val) < 100:
                                change_pct = val
                                break
                        except Exception:
                            pass

            if change_pct is None:
                m = re.search(r'(-?[\d۰-۹\.]+)\s*%\s*(?:تغییر|تغیر)', html)
                if m:
                    try:
                        change_pct = float(to_en(m.group(1)))
                    except Exception:
                        pass

        else:
            m = re.search(
                r'([\d۰-۹][\d۰-۹,٬\.]{1,})\s*(?:تومان|ت\b)', html
            )
            if m:
                n = parse_numeric_price(m.group(1))
                if n and 0.01 < n < 1_000_000_000:
                    price = n

        return price, change_pct
    except Exception as e:
        print(f"[ArzDigital:{item_key}] خطا: {e}")
        return None, None


# ═══════════════════════════════════════════════════════════════
# 📋 MARKETS DATA — ۴۰ بازار
# ═══════════════════════════════════════════════════════════════
ITEMS = [
    # ── اصلی (major) ──
    {"key":"dolar",  "code":"USD", "name":"دلار آمریکا",     "unit":"۱ دلار",          "cat":"major",  "type":"fiat","accent":"#10B981"},
    {"key":"eur",    "code":"EUR", "name":"یورو",             "unit":"۱ یورو",           "cat":"major",  "type":"fiat","accent":"#3B82F6"},
    {"key":"gbp",    "code":"GBP", "name":"پوند انگلیس",      "unit":"۱ پوند",           "cat":"major",  "type":"fiat","accent":"#DC2626"},
    {"key":"chf",    "code":"CHF", "name":"فرانک سوئیس",      "unit":"۱ فرانک",          "cat":"major",  "type":"fiat","accent":"#DC2626"},

    # ── محبوب (popular) ──
    {"key":"aed",    "code":"AED", "name":"درهم امارات",      "unit":"۱ درهم",           "cat":"popular","type":"fiat","accent":"#059669"},
    {"key":"try",    "code":"TRY", "name":"لیر ترکیه",        "unit":"۱ لیر",            "cat":"popular","type":"fiat","accent":"#EF4444"},
    {"key":"cny",    "code":"CNY", "name":"یوان چین",         "unit":"۱ یوان",           "cat":"popular","type":"fiat","accent":"#EF4444"},
    {"key":"cad",    "code":"CAD", "name":"دلار کانادا",       "unit":"۱ دلار کانادا",   "cat":"popular","type":"fiat","accent":"#DC2626"},
    {"key":"jpy",    "code":"JPY", "name":"ین ژاپن",          "unit":"۱۰۰ ین",           "cat":"popular","type":"fiat","accent":"#DC2626"},
    {"key":"aud",    "code":"AUD", "name":"دلار استرالیا",     "unit":"۱ دلار استرالیا", "cat":"popular","type":"fiat","accent":"#059669"},
    {"key":"iqd",    "code":"IQD", "name":"دینار عراق",        "unit":"۱ دینار",          "cat":"popular","type":"fiat","accent":"#DC2626"},

    # ── سایر ارزها (fiat) ──
    {"key":"krw",    "code":"KRW", "name":"وون کره جنوبی",    "unit":"۱ وون",            "cat":"fiat",   "type":"fiat","accent":"#3B82F6"},
    {"key":"nzd",    "code":"NZD", "name":"دلار نیوزیلند",     "unit":"۱ دلار نیوزیلند", "cat":"fiat",   "type":"fiat","accent":"#0284C7"},
    {"key":"sgd",    "code":"SGD", "name":"دلار سنگاپور",      "unit":"۱ دلار سنگاپور",  "cat":"fiat",   "type":"fiat","accent":"#DC2626"},
    {"key":"inr",    "code":"INR", "name":"روپیه هند",        "unit":"۱ روپیه",          "cat":"fiat",   "type":"fiat","accent":"#F59E0B"},
    {"key":"pkr",    "code":"PKR", "name":"روپیه پاکستان",     "unit":"۱ روپیه",          "cat":"fiat",   "type":"fiat","accent":"#059669"},
    {"key":"rub",    "code":"RUB", "name":"روبل روسیه",        "unit":"۱ روبل",           "cat":"fiat",   "type":"fiat","accent":"#3B82F6"},
    {"key":"gel",    "code":"GEL", "name":"لاری گرجستان",      "unit":"۱ لاری",           "cat":"fiat",   "type":"fiat","accent":"#DC2626"},
    {"key":"sar",    "code":"SAR", "name":"ریال عربستان",      "unit":"۱ ریال",           "cat":"fiat",   "type":"fiat","accent":"#059669"},
    {"key":"qar",    "code":"QAR", "name":"ریال قطر",         "unit":"۱ ریال",           "cat":"fiat",   "type":"fiat","accent":"#7F1D1D"},
    {"key":"omr",    "code":"OMR", "name":"ریال عمان",         "unit":"۱ ریال",           "cat":"fiat",   "type":"fiat","accent":"#DC2626"},
    {"key":"tnd",    "code":"TND", "name":"دینار تونس",        "unit":"۱ دینار",          "cat":"fiat",   "type":"fiat","accent":"#DC2626"},
    {"key":"mad",    "code":"MAD", "name":"درهم مراکش",        "unit":"۱ درهم",           "cat":"fiat",   "type":"fiat","accent":"#DC2626"},
    {"key":"khr",    "code":"KHR", "name":"ریل کامبوج",        "unit":"۱ ریل",            "cat":"fiat",   "type":"fiat","accent":"#3B82F6"},
    {"key":"ves",    "code":"VES", "name":"بولیوار ونزوئلا",   "unit":"۱ بولیوار",        "cat":"fiat",   "type":"fiat","accent":"#F59E0B"},
    {"key":"jod",    "code":"JOD", "name":"دینار اردن",        "unit":"۱ دینار",          "cat":"fiat",   "type":"fiat","accent":"#059669"},
    {"key":"bhd",    "code":"BHD", "name":"دینار بحرین",       "unit":"۱ دینار",          "cat":"fiat",   "type":"fiat","accent":"#DC2626"},
    {"key":"kwd",    "code":"KWD", "name":"دینار کویت",        "unit":"۱ دینار",          "cat":"fiat",   "type":"fiat","accent":"#059669"},
    {"key":"afn",    "code":"AFN", "name":"افغانی",           "unit":"۱ افغانی",         "cat":"fiat",   "type":"fiat","accent":"#3B82F6"},
    {"key":"azn",    "code":"AZN", "name":"منات آذربایجان",    "unit":"۱ منات",           "cat":"fiat",   "type":"fiat","accent":"#059669"},
    {"key":"nok",    "code":"NOK", "name":"کرون نروژ",         "unit":"۱ کرون",           "cat":"fiat",   "type":"fiat","accent":"#DC2626"},

    # ── طلا و سکه (metal) ──
    {"key":"gold",   "code":"XAU", "name":"طلای ۱۸ عیار",      "unit":"۱ گرم",            "cat":"metal",  "type":"fiat","accent":"#FBBF24"},
    {"key":"sekeb",  "code":"SEK", "name":"سکه بهار آزادی",   "unit":"۱ سکه",            "cat":"metal",  "type":"fiat","accent":"#FBBF24"},

    # ── رمزارزها (crypto) — ۸ مورد ──
    {"key":"tether", "code":"USDT","name":"تتر",              "unit":"۱ تتر",            "cat":"crypto", "type":"crypto","symbol":"usdt","accent":"#26A17B"},
    {"key":"btc",    "code":"BTC", "name":"بیت‌کوین",          "unit":"۱ بیت‌کوین",       "cat":"crypto", "type":"crypto","symbol":"btc","accent":"#F7931A"},
    {"key":"eth",    "code":"ETH", "name":"اتریوم",            "unit":"۱ اتریوم",         "cat":"crypto", "type":"crypto","symbol":"eth","accent":"#627EEA"},
    {"key":"bnb",    "code":"BNB", "name":"بی‌ان‌بی",           "unit":"۱ BNB",            "cat":"crypto", "type":"crypto","symbol":"bnb","accent":"#F3BA2F"},
    {"key":"gram",   "code":"GRAM","name":"گرام (TON)",       "unit":"۱ گرام",           "cat":"crypto", "type":"crypto","symbol":"gram","accent":"#0098EA"},
    {"key":"xrp",    "code":"XRP", "name":"ریپل",              "unit":"۱ ریپل",           "cat":"crypto", "type":"crypto","symbol":"xrp","accent":"#23292F"},
    {"key":"sol",    "code":"SOL", "name":"سولانا",            "unit":"۱ سولانا",         "cat":"crypto", "type":"crypto","symbol":"sol","accent":"#9945FF"},
]


def fetch_price(item):
    """Returns: (price, change_pct) یا (None, None)"""
    try:
        if item["type"] == "fiat":
            return get_arzdigital_data(item["key"])
        if item["type"] == "crypto":
            r = get_nobitex_stats(item["symbol"])
            if r:
                return r["price"], r.get("change_pct")
            return None, None
    except Exception:
        pass
    return None, None


# ═══════════════════════════════════════════════════════════════
# ⏰ WORLD CLOCKS
# ═══════════════════════════════════════════════════════════════
CITIES = [
    ("تهران",   "Asia/Tehran",      "IR"),
    ("دبی",     "Asia/Dubai",       "AE"),
    ("استانبول","Europe/Istanbul",  "TR"),
    ("لندن",    "Europe/London",    "GB"),
    ("نیویورک", "America/New_York", "US"),
    ("توکیو",   "Asia/Tokyo",       "JP"),
]


def get_city_time(tz_name):
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        offsets = {
            "Asia/Tehran": 3.5, "Asia/Dubai": 4,
            "Europe/London": 0, "America/New_York": -5,
            "Asia/Tokyo": 9, "Europe/Istanbul": 3,
        }
        tz = timezone(timedelta(hours=offsets.get(tz_name, 0)))
    return datetime.now(tz).strftime("%H:%M")


# ═══════════════════════════════════════════════════════════════
# 🧩 COMPONENT: TOAST NOTIFICATION
# ═══════════════════════════════════════════════════════════════
class ToastNotification(ctk.CTkToplevel):
    _active = []

    def __init__(self, master, message, kind="info", duration=3000):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass

        palette = {
            "success": (C["success"], "✓"),
            "error":   (C["danger"],  "✕"),
            "warning": (C["warning"], "!"),
            "info":    (C["cyan"],    "i"),
        }
        color, sym = palette.get(kind, palette["info"])

        outer = ctk.CTkFrame(self, fg_color=color, corner_radius=14)
        outer.pack(fill="both", expand=True)

        frame = ctk.CTkFrame(outer, fg_color=C["card"], corner_radius=12)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=13)

        icon_box = ctk.CTkFrame(inner,
                                 fg_color=hex_alpha(color, 0.18, C["card"]),
                                 width=36, height=36, corner_radius=10)
        icon_box.pack(side="right", padx=(0, 12))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=sym, font=(FONT, 16, "bold"),
                     text_color=color).pack(expand=True)

        ctk.CTkLabel(inner, text=message, font=F(12, "bold"),
                     text_color=C["text"], anchor="e", justify="right",
                     wraplength=240).pack(side="right", fill="x", expand=True)

        self.update_idletasks()
        w, h = 360, 66
        try:
            self.master.update_idletasks()
            mx = self.master.winfo_rootx() + self.master.winfo_width()
            my = self.master.winfo_rooty() + self.master.winfo_height()
        except Exception:
            mx, my = 1400, 900
        offset_y = sum(1 for t in ToastNotification._active
                       if t.winfo_exists()) * (h + 10)
        x = mx - w - 24
        y = my - h - 24 - offset_y
        self.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")

        ToastNotification._active.append(self)
        self._fade_in()
        self.after(duration, self._close)

    def _fade_in(self, a=0.0):
        try:
            a = min(a + 0.18, 1.0)
            self.attributes("-alpha", a)
            if a < 1.0:
                self.after(20, lambda: self._fade_in(a))
        except Exception:
            pass

    def _close(self):
        try:
            self.destroy()
        except Exception:
            pass
        try:
            if self in ToastNotification._active:
                ToastNotification._active.remove(self)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
# 🧩 COMPONENT: STATUS BADGE
# ═══════════════════════════════════════════════════════════════
class StatusBadge(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=C["inner"], corner_radius=10,
                          border_width=1, border_color=C["divider"])
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=12, pady=7)

        self.dot = ctk.CTkLabel(inner, text="●", font=(FONT, 11),
                                 text_color=C["text3"])
        self.dot.pack(side="right", padx=(0, 6))

        self.lbl = ctk.CTkLabel(inner, text="آفلاین", font=F(10, "bold"),
                                 text_color=C["text3"])
        self.lbl.pack(side="right")

    def set_state(self, state):
        states = {
            "connected": ("متصل", C["success"]),
            "updating":  ("در حال بروزرسانی", C["warning"]),
            "offline":   ("آفلاین", C["text3"]),
            "error":     ("خطا", C["danger"]),
        }
        text, color = states.get(state, states["offline"])
        self.dot.configure(text_color=color)
        self.lbl.configure(text=text, text_color=color)


# ═══════════════════════════════════════════════════════════════
# 🧩 COMPONENT: SEARCH BAR
# ═══════════════════════════════════════════════════════════════
class SearchBar(ctk.CTkFrame):
    def __init__(self, master, on_change, placeholder="جستجو..."):
        super().__init__(master, fg_color=C["inner"], corner_radius=12,
                          border_width=1, border_color=C["divider"], height=46)
        self.pack_propagate(False)
        self._on_change = on_change

        ctk.CTkLabel(self, text="⌕", font=(FONT, 18, "bold"),
                     text_color=C["gold"]).pack(side="right", padx=(16, 6))

        self.var = tk.StringVar()
        self.var.trace_add("write", self._on_write)

        self.entry = ctk.CTkEntry(
            self, textvariable=self.var, placeholder_text=placeholder,
            font=F(11), height=44, corner_radius=0,
            fg_color="transparent", border_width=0, text_color=C["text"])
        self.entry.pack(side="right", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(self, text="✕", font=F(11, "bold"),
                       fg_color="transparent", hover_color=C["card_hover"],
                       text_color=C["text3"], width=32, height=32,
                       corner_radius=8, command=self._clear
                       ).pack(side="left", padx=(4, 10))

    def _on_write(self, *_):
        try:
            self._on_change(self.var.get())
        except Exception:
            pass

    def _clear(self):
        self.var.set("")


# ═══════════════════════════════════════════════════════════════
# 🧩 COMPONENT: FILTER PILL
# ═══════════════════════════════════════════════════════════════
class FilterPill(ctk.CTkButton):
    def __init__(self, master, label, key, color, command):
        super().__init__(master, text=label, font=F(10, "bold"),
                          fg_color=C["inner"],
                          hover_color=hex_alpha(color, 0.25, C["card_hover"]),
                          text_color=C["text2"], corner_radius=10,
                          height=36, width=92, border_width=1,
                          border_color=C["divider"],
                          command=lambda: command(key))
        self._key = key
        self._color = color

    def set_active(self, active):
        if active:
            self.configure(fg_color=self._color, text_color="#0A0E18",
                            border_color=self._color)
        else:
            self.configure(fg_color=C["inner"], text_color=C["text2"],
                            border_color=C["divider"])


# ═══════════════════════════════════════════════════════════════
# 🧩 COMPONENT: SPARKLINE
# ═══════════════════════════════════════════════════════════════
class Sparkline(tk.Canvas):
    def __init__(self, master, width=220, height=38):
        super().__init__(master, width=width, height=height,
                          bg=C["card"], bd=0, highlightthickness=0)
        self._width = width
        self._height = height
        self._data = []

    def set_data(self, data):
        self._data = list(data) if data else []
        self._redraw()

    def reset(self):
        self._data = []
        self._redraw()

    def set_colors(self, bg):
        try:
            self.configure(bg=bg)
            self._redraw()
        except Exception:
            pass

    def _redraw(self):
        self.delete("all")
        if len(self._data) < 2:
            self.create_line(10, self._height // 2,
                              self._width - 10, self._height // 2,
                              fill=C["divider"], width=1, dash=(3, 4))
            return

        d = self._data
        mn, mx = min(d), max(d)
        rng = mx - mn if mx != mn else 1
        pad_x, pad_y = 6, 5
        w, h = self._width, self._height
        n = len(d)

        pts = []
        for i, v in enumerate(d):
            x = pad_x + (w - 2 * pad_x) * i / (n - 1)
            y = h - pad_y - (h - 2 * pad_y) * (v - mn) / rng
            pts.append((x, y))

        is_up = d[-1] >= d[0]
        line_color = C["success"] if is_up else C["danger"]
        fill_color = hex_alpha(line_color, 0.20, C["card"])

        poly = [(pad_x, h - pad_y)] + pts + [(w - pad_x, h - pad_y)]
        flat = [c for p in poly for c in p]
        self.create_polygon(flat, fill=fill_color, outline="")

        line_pts = [c for p in pts for c in p]
        self.create_line(*line_pts, fill=line_color, width=2,
                          smooth=True, capstyle="round", joinstyle="round")

        lx, ly = pts[-1]
        self.create_oval(lx - 5, ly - 5, lx + 5, ly + 5,
                          fill=hex_alpha(line_color, 0.3, C["card"]), outline="")
        self.create_oval(lx - 3, ly - 3, lx + 3, ly + 3,
                          fill=line_color, outline=line_color)


# ═══════════════════════════════════════════════════════════════
# 🧩 COMPONENT: CURRENCY CARD
# ═══════════════════════════════════════════════════════════════
class CurrencyCard(ctk.CTkFrame):
    def __init__(self, master, item):
        super().__init__(master, fg_color=C["card"], corner_radius=20,
                          border_width=1, border_color=C["card_border"])
        self.item = item
        self.accent = item.get("accent", C["gold"])
        self._icon_img = None
        self._anim_id = None
        self._history = []
        self._is_loading = False
        self._favorites = set()
        self._on_fav = None

        self._build()

        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")

    def _build(self):
        self.accent_bar = ctk.CTkFrame(self, fg_color=self.accent,
                                        height=3, corner_radius=2)
        self.accent_bar.pack(fill="x", padx=16, pady=(14, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=16)

        head = ctk.CTkFrame(body, fg_color="transparent")
        head.pack(fill="x")

        self.fav_btn = ctk.CTkButton(
            head, text="☆", font=(FONT, 18),
            fg_color="transparent",
            hover_color=hex_alpha(C["gold"], 0.22, C["card"]),
            text_color=C["text3"], width=34, height=34,
            corner_radius=10,
            command=self._toggle_fav)
        self.fav_btn.pack(side="left", padx=(4, 0))

        self.icon_frame = ctk.CTkFrame(
            head, fg_color=hex_alpha(self.accent, 0.14, C["card"]),
            width=64, height=64, corner_radius=18, border_width=2,
            border_color=hex_alpha(self.accent, 0.45, C["card"]))
        self.icon_frame.pack(side="right")
        self.icon_frame.pack_propagate(False)

        self.icon_label = ctk.CTkLabel(self.icon_frame, text="")
        self.icon_label.pack(expand=True)
        self._load_icon()

        title_box = ctk.CTkFrame(head, fg_color="transparent")
        title_box.pack(side="right", fill="x", expand=True, padx=(0, 12))

        self.name_lbl = ctk.CTkLabel(title_box, text=self.item["name"],
                                       font=F(14, "bold"),
                                       text_color=C["text"], anchor="e")
        self.name_lbl.pack(anchor="e")

        meta_box = ctk.CTkFrame(title_box, fg_color="transparent")
        meta_box.pack(anchor="e", pady=(4, 0))

        ctk.CTkLabel(meta_box, text=self.item["code"],
                     font=F(9, "bold"), text_color=C["text3"]
                     ).pack(side="right")
        ctk.CTkLabel(meta_box, text="  •  ",
                     font=F(9), text_color=C["text4"]
                     ).pack(side="right")
        ctk.CTkLabel(meta_box, text=self.item["unit"],
                     font=F(9), text_color=C["text4"]
                     ).pack(side="right")

        self.price_box = ctk.CTkFrame(body, fg_color=C["inner"],
                                        corner_radius=14, border_width=1,
                                        border_color=C["inner_border"], height=96)
        self.price_box.pack(fill="x", pady=(18, 12))
        self.price_box.pack_propagate(False)

        self.price_inner = ctk.CTkFrame(self.price_box, fg_color="transparent")
        self.price_inner.pack(fill="both", expand=True, padx=16, pady=12)

        self.price_row = ctk.CTkFrame(self.price_inner, fg_color="transparent")
        self.price_row.pack(fill="x")

        self.price_lbl = ctk.CTkLabel(self.price_row, text="—",
                                        font=(FONT, 22, "bold"),
                                        text_color=C["text"], anchor="e")
        self.price_lbl.pack(side="right", fill="x", expand=True)

        self.currency_lbl = ctk.CTkLabel(self.price_row, text="تومان",
                                           font=F(9, "bold"),
                                           text_color=C["gold"], anchor="e")
        self.currency_lbl.pack(side="right", padx=(0, 6))

        self.change_row = ctk.CTkFrame(self.price_inner, fg_color="transparent")
        self.change_row.pack(fill="x", pady=(4, 0))

        self.change_arrow = ctk.CTkLabel(self.change_row, text="",
                                            font=(FONT, 11, "bold"),
                                            text_color=C["text3"], anchor="e")
        self.change_arrow.pack(side="right")

        self.change_lbl = ctk.CTkLabel(self.change_row, text="",
                                          font=(FONT, 12, "bold"),
                                          text_color=C["text3"], anchor="e")
        self.change_lbl.pack(side="right", padx=(4, 0))

        self.change_period = ctk.CTkLabel(self.change_row, text="",
                                            font=F(9),
                                            text_color=C["text4"], anchor="e")
        self.change_period.pack(side="right", padx=(0, 6))

        self.spark = Sparkline(body, width=220, height=38)
        self.spark.pack(fill="x", pady=(0, 10))

        foot = ctk.CTkFrame(body, fg_color="transparent")
        foot.pack(fill="x")

        self.status_lbl = ctk.CTkLabel(foot, text="قیمت لحظه‌ای",
                                         font=F(9),
                                         text_color=C["text3"], anchor="e")
        self.status_lbl.pack(side="right")

        self.status_dot = ctk.CTkLabel(foot, text="●", font=(FONT, 8),
                                         text_color=C["text4"])
        self.status_dot.pack(side="right", padx=(5, 0))

        src_text = "نوبیتکس" if self.item["type"] == "crypto" else "ارزدیجیتال"
        ctk.CTkLabel(foot, text=src_text, font=F(8),
                     text_color=C["text4"], anchor="w").pack(side="left")

    def _load_icon(self):
        img = load_icon(self.item["key"], size=(50, 50))
        if img is not None:
            self._icon_img = img
            self.icon_label.configure(image=img, text="")
        else:
            self.icon_label.configure(image=None,
                                        text=self.item["code"][:3],
                                        font=(FONT, 14, "bold"),
                                        text_color=self.accent)

    def _on_enter(self, _=None):
        try:
            self.configure(fg_color=C["card_hover"], border_color=self.accent)
            self.price_box.configure(
                fg_color=C["card_active"],
                border_color=hex_alpha(self.accent, 0.4, C["card_active"]))
            self.spark.set_colors(C["card_hover"])
        except Exception:
            pass

    def _on_leave(self, _=None):
        try:
            self.configure(fg_color=C["card"], border_color=C["card_border"])
            self.price_box.configure(fg_color=C["inner"],
                                       border_color=C["inner_border"])
            self.spark.set_colors(C["card"])
        except Exception:
            pass

    def _toggle_fav(self):
        if self._on_fav:
            self._on_fav(self.item["key"])

    def set_favorites(self, fav_set):
        self._favorites = fav_set
        is_fav = self.item["key"] in fav_set
        try:
            self.fav_btn.configure(
                text="★" if is_fav else "☆",
                text_color=C["gold"] if is_fav else C["text3"])
        except Exception:
            pass

    def set_fav_callback(self, cb):
        self._on_fav = cb

    def _pulse_border(self, color, steps=6, delay=60):
        if self._anim_id:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass

        def step(i):
            if i > steps:
                try:
                    self.configure(border_color=C["card_border"])
                except Exception:
                    pass
                self._anim_id = None
                return
            try:
                self.configure(border_color=color)
            except Exception:
                pass
            self._anim_id = self.after(delay, lambda: step(i + 1))

        step(0)

    def set_loading(self):
        self._is_loading = True
        self.price_lbl.configure(text="…", text_color=C["text3"])
        self.change_arrow.configure(text="")
        self.change_lbl.configure(text="")
        self.change_period.configure(text="")
        self.status_dot.configure(text_color=C["warning"])
        self.status_lbl.configure(text="در حال دریافت", text_color=C["warning"])

    def set_price(self, price, change_pct=None):
        self._is_loading = False
        if price is None:
            self.price_lbl.configure(text="—", text_color=C["danger"])
            self.change_arrow.configure(text="")
            self.change_lbl.configure(text="")
            self.change_period.configure(text="")
            self.status_dot.configure(text_color=C["danger"])
            self.status_lbl.configure(text="ناموفق", text_color=C["danger"])
            return

        self._history.append(price)
        if len(self._history) > 20:
            self._history = self._history[-20:]
        self.spark.set_data(self._history)

        color = C["text"]
        if len(self._history) >= 2:
            prev = self._history[-2]
            if price > prev:
                color = C["success"]
                self._pulse_border(C["success"])
            elif price < prev:
                color = C["danger"]
                self._pulse_border(C["danger"])

        self.price_lbl.configure(text=fmt_price(price), text_color=color)

        if change_pct is None and len(self._history) >= 2:
            prev = self._history[-2]
            if prev:
                try:
                    change_pct = ((price - prev) / prev) * 100
                except Exception:
                    change_pct = None

        if change_pct is not None:
            try:
                pct = float(change_pct)
                if pct > 0:
                    arrow = "▲"
                    ch_color = C["success"]
                elif pct < 0:
                    arrow = "▼"
                    ch_color = C["danger"]
                else:
                    arrow = "▬"
                    ch_color = C["text3"]

                self.change_arrow.configure(text=arrow, text_color=ch_color)
                self.change_lbl.configure(
                    text=f"{to_fa(f'{abs(pct):.2f}')}%",
                    text_color=ch_color)
                self.change_period.configure(text="۲۴ ساعت",
                                                text_color=C["text4"])
            except Exception:
                pass
        else:
            self.change_arrow.configure(text="")
            self.change_lbl.configure(text="")
            self.change_period.configure(text="")

        self.status_dot.configure(text_color=C["success"])
        self.status_lbl.configure(text="قیمت لحظه‌ای", text_color=C["success"])


# ═══════════════════════════════════════════════════════════════
# 🧩 COMPONENT: MARKET OVERVIEW CARD
# ═══════════════════════════════════════════════════════════════
class MarketOverviewCard(ctk.CTkFrame):
    def __init__(self, master, icon_key, fallback_icon, title, value, color):
        super().__init__(master, fg_color=C["card"], corner_radius=16,
                          border_width=1, border_color=C["card_border"])

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        self.icon_box = ctk.CTkFrame(
            inner, fg_color=hex_alpha(color, 0.15, C["card"]),
            width=50, height=50, corner_radius=14, border_width=1,
            border_color=hex_alpha(color, 0.35, C["card"]))
        self.icon_box.pack(side="right", padx=(0, 12))
        self.icon_box.pack_propagate(False)

        self.icon_lbl = ctk.CTkLabel(self.icon_box, text="",
                                       font=(FONT, 18, "bold"), text_color=color)
        img = load_icon(icon_key, size=(32, 32), subfolder="ui")
        if img is not None:
            self.icon_lbl.configure(image=img, text="")
        else:
            self.icon_lbl.configure(text=fallback_icon, text_color=color)
        self.icon_lbl.pack(expand=True)

        txt = ctk.CTkFrame(inner, fg_color="transparent")
        txt.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(txt, text=title, font=F(10),
                     text_color=C["text3"], anchor="e").pack(anchor="e")

        self.value_lbl = ctk.CTkLabel(txt, text=value, font=F(16, "bold"),
                                        text_color=C["text"], anchor="e")
        self.value_lbl.pack(anchor="e", pady=(2, 0))

    def set_value(self, value, color=None):
        self.value_lbl.configure(text=value)
        if color:
            self.value_lbl.configure(text_color=color)


# ═══════════════════════════════════════════════════════════════
# 🧩 COMPONENT: CLOCK CHIP
# ═══════════════════════════════════════════════════════════════
class ClockChip(ctk.CTkFrame):
    def __init__(self, master, city, tz, country):
        super().__init__(master, fg_color=C["card"], corner_radius=14,
                          border_width=1, border_color=C["card_border"])
        self.tz = tz

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        ctk.CTkLabel(top, text=city, font=F(12, "bold"),
                     text_color=C["text"]).pack(side="right")
        ctk.CTkLabel(top, text=country, font=F(8, "bold"),
                     text_color=C["gold"]).pack(side="left")

        self.time_lbl = ctk.CTkLabel(inner, text="--:--",
                                       font=(FONT, 22, "bold"),
                                       text_color=C["gold"])
        self.time_lbl.pack(anchor="e", pady=(6, 0))

        self.divider = ctk.CTkFrame(inner, fg_color=C["gold"],
                                      height=2, corner_radius=1)
        self.divider.pack(fill="x", pady=(8, 0))

    def update_time(self):
        try:
            self.time_lbl.configure(text=to_fa(get_city_time(self.tz)))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
# 🧮 CALCULATOR
# ═══════════════════════════════════════════════════════════════
class CalculatorDialog(ctk.CTkToplevel):
    def __init__(self, parent, prices):
        super().__init__(parent)
        self.prices = prices

        self.title("ماشین حساب ارز")
        self.geometry("540x540")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.transient(parent)
        self.grab_set()

        self._center(parent)
        self._build()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center(self, parent):
        try:
            self.update_idletasks()
            w, h = 540, 540
            px = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
            py = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
            self.geometry(f"{w}x{h}+{max(px, 0)}+{max(py, 0)}")
        except Exception:
            pass

    def _on_close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _build(self):
        head = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=90)
        head.pack(fill="x")
        head.pack_propagate(False)

        h_in = ctk.CTkFrame(head, fg_color="transparent")
        h_in.pack(expand=True, fill="both", padx=24, pady=18)

        ib = ctk.CTkFrame(h_in, fg_color=C["gold"], width=50, height=50,
                           corner_radius=14)
        ib.pack(side="right")
        ib.pack_propagate(False)
        ctk.CTkLabel(ib, text="∑", font=(FONT, 24, "bold"),
                     text_color="#0A0E18").pack(expand=True)

        tb = ctk.CTkFrame(h_in, fg_color="transparent")
        tb.pack(side="right", padx=(0, 14))
        ctk.CTkLabel(tb, text="ماشین حساب ارز", font=F(17, "bold"),
                     text_color=C["text"]).pack(anchor="e")
        ctk.CTkLabel(tb, text="مقدار × قیمت = قیمت کل", font=F(10),
                     text_color=C["text3"]).pack(anchor="e", pady=(2, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=26, pady=22)

        ctk.CTkLabel(body, text="مقدار", font=F(11, "bold"),
                     text_color=C["text2"], anchor="e").pack(anchor="e", pady=(0, 8))

        self.amount_entry = ctk.CTkEntry(
            body, placeholder_text="مثلاً ۵", font=F(15), height=50,
            corner_radius=11, fg_color=C["inner"], border_color=C["divider"],
            text_color=C["text"], justify="center")
        self.amount_entry.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(body, text="ارز", font=F(11, "bold"),
                     text_color=C["text2"], anchor="e").pack(anchor="e", pady=(0, 8))

        names = [it["name"] for it in ITEMS]
        self.currency_menu = ctk.CTkOptionMenu(
            body, values=names, font=F(12), height=50,
            fg_color=C["inner"], button_color=C["divider"],
            button_hover_color=C["gold"], text_color=C["text"],
            dropdown_font=F(11), corner_radius=11)
        self.currency_menu.pack(fill="x", pady=(0, 20))
        if names:
            self.currency_menu.set(names[0])

        ctk.CTkButton(body, text="محاسبه", font=F(13, "bold"),
                       fg_color=C["gold"], hover_color=C["gold_hi"],
                       text_color="#0A0E18", corner_radius=11, height=52,
                       command=self._calculate).pack(fill="x")

        self.result_lbl = ctk.CTkLabel(self, text="", font=F(15, "bold"),
                                         text_color=C["gold"], height=70,
                                         wraplength=480)
        self.result_lbl.pack(fill="x", padx=26, pady=(0, 20))

        self.amount_entry.bind("<Return>", lambda e: self._calculate())
        self.amount_entry.focus_set()

    def _calculate(self):
        try:
            raw = self.amount_entry.get().strip()
            if not raw:
                return
            amount = float(to_en(raw).replace(",", "").replace("٬", ""))
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.result_lbl.configure(text="مقدار وارد شده معتبر نیست",
                                        text_color=C["danger"])
            return

        name = self.currency_menu.get()
        item = next((x for x in ITEMS if x["name"] == name), None)
        if not item:
            return

        price = self.prices.get(item["key"], (None, None))[0]
        if not price:
            self.result_lbl.configure(text="قیمت این ارز دریافت نشده",
                                        text_color=C["danger"])
            return

        total = price * amount
        self.result_lbl.configure(
            text=f"{fmt_price(amount)} × {name}\n= {fmt_price(total)} تومان",
            text_color=C["gold"])


# ═══════════════════════════════════════════════════════════════
# 🔄 UPDATE DIALOG — پنجره‌ی آپدیت خودکار
# ═══════════════════════════════════════════════════════════════
class UpdateDialog(ctk.CTkToplevel):
    def __init__(self, parent, update_info):
        super().__init__(parent)
        self.parent = parent
        self.info = update_info
        self._installing = False

        self.title("آپدیت جدید موجود است")
        self.geometry("580x620")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.transient(parent)
        self.grab_set()

        self._center(parent)
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center(self, parent):
        try:
            self.update_idletasks()
            w, h = 580, 620
            px = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
            py = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
            self.geometry(f"{w}x{h}+{max(px, 0)}+{max(py, 0)}")
        except Exception:
            pass

    def _on_close(self):
        if self._installing:
            return
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _build(self):
        head = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=100)
        head.pack(fill="x")
        head.pack_propagate(False)

        h_in = ctk.CTkFrame(head, fg_color="transparent")
        h_in.pack(expand=True, fill="both", padx=24, pady=18)

        ib = ctk.CTkFrame(h_in, fg_color=C["success"], width=56, height=56,
                           corner_radius=16)
        ib.pack(side="right")
        ib.pack_propagate(False)
        ctk.CTkLabel(ib, text="⬆", font=(FONT, 26, "bold"),
                     text_color="#0A0E18").pack(expand=True)

        tb = ctk.CTkFrame(h_in, fg_color="transparent")
        tb.pack(side="right", padx=(0, 14))
        ctk.CTkLabel(tb, text="آپدیت جدید موجود است!", font=F(18, "bold"),
                     text_color=C["text"]).pack(anchor="e")

        cur = self.info.get("current_version", "?")
        new = self.info.get("latest_version", "?")
        ctk.CTkLabel(tb,
                     text=f"نسخه فعلی: {to_fa(cur)}  ←  نسخه جدید: {to_fa(new)}",
                     font=F(11), text_color=C["gold"]
                     ).pack(anchor="e", pady=(4, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=26, pady=22)

        ctk.CTkLabel(body, text="📝 تغییرات این نسخه:",
                     font=F(12, "bold"), text_color=C["gold"],
                     anchor="e").pack(anchor="e", pady=(0, 8))

        changelog_box = ctk.CTkFrame(body, fg_color=C["inner"],
                                       corner_radius=12, border_width=1,
                                       border_color=C["inner_border"])
        changelog_box.pack(fill="x", pady=(0, 18))

        changelog_text = self.info.get("changelog", "—") or "—"
        ctk.CTkLabel(changelog_box, text=changelog_text,
                     font=F(11), text_color=C["text2"],
                     anchor="e", justify="right",
                     wraplength=480).pack(anchor="e", padx=16, pady=14)

        ctk.CTkLabel(body, text="📥 پیشرفت دانلود:",
                     font=F(11, "bold"), text_color=C["text3"],
                     anchor="e").pack(anchor="e", pady=(0, 6))

        self.progress = ctk.CTkProgressBar(
            body, height=14, corner_radius=7,
            progress_color=C["gold"], fg_color=C["inner"])
        self.progress.pack(fill="x", pady=(0, 6))
        self.progress.set(0)

        self.status_lbl = ctk.CTkLabel(body, text="آماده برای دانلود",
                                         font=F(10), text_color=C["text3"])
        self.status_lbl.pack(anchor="e", pady=(0, 4))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=26, pady=(0, 22))

        self.cancel_btn = ctk.CTkButton(
            btns, text="بعداً", font=F(12, "bold"),
            fg_color=C["inner"], hover_color=C["card_hover"],
            text_color=C["text2"], corner_radius=11, height=50, width=130,
            command=self._on_close)
        self.cancel_btn.pack(side="left")

        self.update_btn = ctk.CTkButton(
            btns, text="⬇  دانلود و نصب", font=F(12, "bold"),
            fg_color=C["success"], hover_color=C["success_dark"],
            text_color="#FFFFFF", corner_radius=11, height=50,
            command=self._start_update)
        self.update_btn.pack(side="right", fill="x", expand=True, padx=(12, 0))

    def _start_update(self):
        self._installing = True
        self.update_btn.configure(state="disabled", text="در حال دانلود...")
        self.cancel_btn.configure(state="disabled")
        self.status_lbl.configure(text="اتصال به سرور...", text_color=C["cyan"])
        threading.Thread(target=self._do_update, daemon=True).start()

    def _do_update(self):
        try:
            import update_checker as uc
        except ImportError:
            self.after(0, lambda: self._on_error("ماژول update_checker پیدا نشد"))
            return

        url = self.info.get("download_url", "")

        def progress_cb(pct):
            try:
                self.after(0, lambda: self._update_progress(pct))
            except Exception:
                pass

        ok, tmp_path, err = uc.download_update(url, progress_callback=progress_cb)

        if not ok:
            self.after(0, lambda: self._on_error(f"دانلود ناموفق: {err}"))
            return

        self.after(0, lambda: self.status_lbl.configure(
            text="در حال نصب...", text_color=C["warning"]))

        version = self.info.get("latest_version", "0.0")
        changelog = self.info.get("changelog", "")
        ok, err, backup = uc.install_update(tmp_path, version, changelog)

        if not ok:
            self.after(0, lambda: self._on_error(f"نصب ناموفق: {err}"))
            return

        self.after(0, self._on_success)

    def _update_progress(self, pct):
        try:
            self.progress.set(pct / 100.0)
            self.status_lbl.configure(text=f"دانلود: {to_fa(pct)}٪",
                                       text_color=C["cyan"])
        except Exception:
            pass

    def _on_error(self, message):
        self._installing = False
        self.status_lbl.configure(text=message, text_color=C["danger"])
        self.update_btn.configure(state="normal", text="🔄 تلاش دوباره")
        self.cancel_btn.configure(state="normal")

    def _on_success(self):
        self.progress.set(1.0)
        self.status_lbl.configure(text="✅ نصب با موفقیت انجام شد!",
                                    text_color=C["success"])

        self.update_btn.configure(
            state="normal",
            text="🔄  ریستارت برنامه",
            fg_color=C["gold"],
            hover_color=C["gold_hi"],
            text_color="#0A0E18",
            command=self._restart)
        self.cancel_btn.configure(state="normal", text="بستن")

        ToastNotification(self.parent, "آپدیت نصب شد! لطفاً ریستارت کن",
                           kind="success", duration=5000)

    def _restart(self):
        try:
            import update_checker as uc
        except ImportError:
            return
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

        if uc.restart_app():
            try:
                self.parent._on_close()
            except Exception:
                self.parent.destroy()


# ═══════════════════════════════════════════════════════════════
# 🖼️ MAIN APP
# ═══════════════════════════════════════════════════════════════
class TeleCoinApp(ctk.CTk):
    def __init__(self):
        global FONT
        super().__init__()

        FONT = detect_font()
        self.config_data = load_config()
        ctk.set_appearance_mode("dark")

        sound.set_enabled(self.config_data.get("sound", True))
        sound.set_volume(self.config_data.get("volume", 70) / 100.0)

        self.title("TeleCoin Pro — ترمینال حرفه‌ای بازار")
        self.geometry("1440x920")
        self.minsize(1150, 750)
        self.configure(fg_color=C["bg"])

        self._icon_photo = None
        self._set_app_icon()

        self.prices = {}
        self.cards = {}
        self.visible_items = []
        self.favorites = set(self.config_data.get("favorites", []))
        self.current_filter = "all"
        self.search_query = ""
        self.is_loading = False
        self.calc_window = None
        self.settings_window = None
        self.update_window = None
        self.clock_chips = []
        self._price_queue = queue.Queue()
        self._last_update = "—"
        self._grid_cols = 4
        self._grid_resize_job = None
        self._closing = False
        self._auto_job = None
        self._poll_started = False

        self._build_layout()
        self._build_topbar()
        self._build_overview()
        self._build_toolbar()
        self._build_grid()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(300, self.load_all_prices)
        self._start_polling()
        self.after(1000, self._tick_clocks)
        self._schedule_auto_refresh()
        # 🔄 چک خودکار آپدیت ۵ ثانیه بعد از شروع
        self.after(5000, lambda: self._check_update(silent=True))

    def _set_app_icon(self):
        try:
            ico_path = os.path.join(BASE_DIR, "icon.ico")
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
                return
        except Exception:
            pass
        try:
            png_path = os.path.join(ICONS_DIR, "logo.png")
            if os.path.exists(png_path):
                from PIL import Image as PILImage, ImageTk
                img = PILImage.open(png_path).convert("RGBA")
                img = img.resize((64, 64), PILImage.LANCZOS)
                self._icon_photo = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._icon_photo)
        except Exception:
            pass

    def _build_layout(self):
        self.main = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.main.pack(fill="both", expand=True, padx=18, pady=18)

    def _build_topbar(self):
        self.topbar = ctk.CTkFrame(self.main, fg_color=C["topbar"],
                                    corner_radius=18, border_width=1,
                                    border_color=C["card_border"], height=92)
        self.topbar.pack(fill="x", pady=(0, 14))
        self.topbar.pack_propagate(False)

        inner = ctk.CTkFrame(self.topbar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=18)

        brand = ctk.CTkFrame(inner, fg_color="transparent")
        brand.pack(side="right")

        logo_img = load_icon("logo", size=(58, 58))
        if logo_img is not None:
            ctk.CTkLabel(brand, text="", image=logo_img).pack(side="right", padx=(0, 14))
        else:
            logo_box = ctk.CTkFrame(brand, fg_color=C["gold"], width=58,
                                     height=58, corner_radius=16)
            logo_box.pack(side="right", padx=(0, 14))
            logo_box.pack_propagate(False)
            ctk.CTkLabel(logo_box, text="₮", font=(FONT, 28, "bold"),
                         text_color="#0A0E18").pack(expand=True)

        brand_txt = ctk.CTkFrame(brand, fg_color="transparent")
        brand_txt.pack(side="right")
        ctk.CTkLabel(brand_txt, text="TeleCoin Pro", font=F(21, "bold"),
                     text_color=C["text"]).pack(anchor="e")
        ctk.CTkLabel(brand_txt, text="ترمینال حرفه‌ای بازار ارز و رمزارز",
                     font=F(10), text_color=C["text3"]
                     ).pack(anchor="e", pady=(3, 0))

        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="left")

        self.status_badge = StatusBadge(right)
        self.status_badge.pack(side="left", padx=(0, 16))

        update_box = ctk.CTkFrame(right, fg_color="transparent")
        update_box.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(update_box, text="آخرین بروزرسانی", font=F(9, "bold"),
                     text_color=C["text4"]).pack(anchor="e")
        self.last_update_lbl = ctk.CTkLabel(update_box, text="—",
                                              font=F(11, "bold"),
                                              text_color=C["text2"])
        self.last_update_lbl.pack(anchor="e", pady=(2, 0))

        # 🔄 دکمه بررسی آپدیت
        self.update_btn = ctk.CTkButton(
            right, text="🔄", command=self._check_update,
            font=(FONT, 16, "bold"), fg_color=C["card_hover"],
            hover_color=hex_alpha(C["cyan"], 0.25, C["card_hover"]),
            text_color=C["cyan"], corner_radius=10, width=44, height=44)
        self.update_btn.pack(side="left", padx=4)

        self.settings_btn = ctk.CTkButton(
            right, text="⚙", command=self._open_settings,
            font=(FONT, 16, "bold"), fg_color=C["card_hover"],
            hover_color=hex_alpha(C["gold"], 0.25, C["card_hover"]),
            text_color=C["text2"], corner_radius=10, width=44, height=44)
        self.settings_btn.pack(side="left", padx=4)

        self.calc_btn = ctk.CTkButton(
            right, text="∑  ماشین حساب", command=self._open_calculator,
            font=F(11, "bold"), fg_color=C["inner"],
            hover_color=C["card_hover"], text_color=C["text"],
            corner_radius=10, height=44, width=150)
        self.calc_btn.pack(side="left", padx=4)

        self.refresh_btn = ctk.CTkButton(
            right, text="↻  بروزرسانی", command=self.load_all_prices,
            font=F(11, "bold"), fg_color=C["gold"], hover_color=C["gold_hi"],
            text_color="#0A0E18", corner_radius=10, height=44, width=140)
        self.refresh_btn.pack(side="left", padx=4)

    def _build_overview(self):
        self.overview = ctk.CTkFrame(self.main, fg_color="transparent")
        self.overview.pack(fill="x", pady=(0, 14))

        for i in range(4):
            self.overview.grid_columnconfigure(i, weight=1, uniform="ov")

        self.ov_total = MarketOverviewCard(
            self.overview, "total", "◈", "کل بازارها",
            to_fa(len(ITEMS)), C["gold"])
        self.ov_total.grid(row=0, column=0, sticky="nsew", padx=(0, 7))

        self.ov_live = MarketOverviewCard(
            self.overview, "live", "◉", "قیمت‌های زنده", "۰", C["success"])
        self.ov_live.grid(row=0, column=1, sticky="nsew", padx=7)

        self.ov_update = MarketOverviewCard(
            self.overview, "clock", "◷", "آخرین بروزرسانی", "—", C["cyan"])
        self.ov_update.grid(row=0, column=2, sticky="nsew", padx=7)

        self.ov_status = MarketOverviewCard(
            self.overview, "connection", "◊", "وضعیت اتصال",
            "آفلاین", C["text3"])
        self.ov_status.grid(row=0, column=3, sticky="nsew", padx=(7, 0))

    def _build_toolbar(self):
        self.toolbar = ctk.CTkFrame(self.main, fg_color=C["topbar"],
                                     corner_radius=16, border_width=1,
                                     border_color=C["card_border"])
        self.toolbar.pack(fill="x", pady=(0, 14))

        inner = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=14)

        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x")

        self.search_bar = SearchBar(row1, self._on_search,
                                     placeholder="جستجوی ارز یا رمزارز...")
        self.search_bar.pack(side="right", fill="x", expand=True, padx=(0, 12))

        filters_box = ctk.CTkFrame(row1, fg_color="transparent")
        filters_box.pack(side="left")

        self.filter_pills = {}
        filter_defs = [
            ("all",     "همه",      C["gold"]),
            ("major",   "اصلی",     C["cyan"]),
            ("popular", "محبوب",    C["success"]),
            ("crypto",  "رمزارز",   C["purple"]),
            ("fiat",    "ارز",      C["text2"]),
            ("metal",   "طلا",      C["gold_hi"]),
            ("fav",     "★ دلخواه", C["gold"]),
        ]
        for key, label, color in filter_defs:
            pill = FilterPill(filters_box, label, key, color, self._set_filter)
            pill.pack(side="right", padx=3)
            self.filter_pills[key] = pill

        self.filter_pills["all"].set_active(True)

        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(14, 0))

        ctk.CTkLabel(row2, text="🕐 ساعت جهانی", font=F(11, "bold"),
                     text_color=C["text3"]).pack(side="right", padx=(0, 14))

        clocks = ctk.CTkFrame(row2, fg_color="transparent")
        clocks.pack(side="right", fill="x", expand=True)

        self.clock_chips = []
        for city, tz, country in CITIES:
            chip = ClockChip(clocks, city, tz, country)
            chip.pack(side="right", padx=4, fill="x", expand=True)
            self.clock_chips.append(chip)

    def _set_filter(self, key):
        self.current_filter = key
        for k, pill in self.filter_pills.items():
            pill.set_active(k == key)
        self._apply_filter()

    def _on_search(self, value):
        self.search_query = value.strip().lower()
        self._apply_filter()

    def _match(self, item):
        if self.current_filter == "fav":
            if item["key"] not in self.favorites:
                return False
        elif self.current_filter != "all":
            if item["cat"] != self.current_filter:
                return False

        if self.search_query:
            hay = (f"{item['name']} {item['key']} "
                   f"{item.get('code','')} {item['unit']}").lower()
            if self.search_query not in hay:
                return False
        return True

    def _apply_filter(self):
        self.visible_items = [it for it in ITEMS if self._match(it)]
        for refs in self.cards.values():
            refs["frame"].grid_forget()

        if not self.visible_items:
            self.empty_label.grid(row=0, column=0,
                                    columnspan=self._grid_cols, pady=60)
            self.canvas.yview_moveto(0)
            self._update_scrollregion()
            return

        self.empty_label.grid_forget()
        self._layout_grid(force=True)

    def _layout_grid(self, force=False):
        try:
            w = self.canvas.winfo_width()
        except Exception:
            w = 1300
        if w >= 1350:
            cols = 4
        elif w >= 1000:
            cols = 3
        elif w >= 650:
            cols = 2
        else:
            cols = 1

        cols_changed = (cols != self._grid_cols)
        if not force and not cols_changed:
            return

        self._grid_cols = cols
        for i in range(4):
            self.cards_frame.grid_columnconfigure(i, weight=0, uniform="")
        for i in range(cols):
            self.cards_frame.grid_columnconfigure(i, weight=1, uniform="card")

        for i, item in enumerate(self.visible_items):
            row = i // cols
            col = i % cols
            refs = self.cards.get(item["key"])
            if refs:
                refs["frame"].grid(row=row, column=col, sticky="nsew",
                                     padx=8, pady=8)

        self._update_scrollregion()

    def _update_scrollregion(self):
        try:
            self.cards_frame.update_idletasks()
            self.canvas.configure(
                scrollregion=(0, 0, 0, self.cards_frame.winfo_reqheight()))
        except Exception:
            pass

    def _build_grid(self):
        self.grid_container = tk.Frame(self.main, bg=C["bg2"], bd=0,
                                         highlightthickness=0)
        self.grid_container.pack(fill="both", expand=True)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Pro.Vertical.TScrollbar",
            background=C["scroll"], troughcolor=C["bg2"],
            bordercolor=C["bg2"], arrowcolor=C["gold"],
            lightcolor=C["scroll"], darkcolor=C["scroll"], width=10)
        style.map("Pro.Vertical.TScrollbar",
                   background=[("active", C["gold"])])

        self.scrollbar = ttk.Scrollbar(self.grid_container, orient="vertical",
                                         style="Pro.Vertical.TScrollbar")
        self.scrollbar.pack(side="left", fill="y")

        self.canvas = tk.Canvas(self.grid_container, bg=C["bg2"], bd=0,
                                  highlightthickness=0, relief="flat",
                                  yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="right", fill="both", expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        self.cards_frame = tk.Frame(self.canvas, bg=C["bg2"])
        self._win_id = self.canvas.create_window((0, 0), window=self.cards_frame,
                                                   anchor="nw")

        self.cards_frame.bind("<Configure>",
                                lambda e: self._update_scrollregion())
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        self._bind_mousewheel_recursive(self.canvas)
        self._bind_mousewheel_recursive(self.cards_frame)

        for item in ITEMS:
            card = CurrencyCard(self.cards_frame, item)
            card.set_favorites(self.favorites)
            card.set_fav_callback(self._toggle_favorite)
            self._bind_mousewheel_recursive(card)
            self.cards[item["key"]] = {
                "frame": card, "card": card, "item": item,
            }

        self.empty_label = tk.Label(self.cards_frame,
                                      text="🔍  موردی پیدا نشد",
                                      font=F(14), bg=C["bg2"], fg=C["text3"])

        self._apply_filter()

    def _on_canvas_resize(self, event):
        try:
            self.canvas.itemconfig(self._win_id, width=event.width)
        except Exception:
            pass
        if self._grid_resize_job:
            try:
                self.after_cancel(self._grid_resize_job)
            except Exception:
                pass
        self._grid_resize_job = self.after(120, self._layout_grid)

    def _bind_mousewheel_recursive(self, widget):
        if isinstance(widget, (tk.Entry, tk.Text)):
            return
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel_recursive(child)

    def _on_mousewheel(self, event):
        try:
            if event.num == 4:
                self.canvas.yview_scroll(-2, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(2, "units")
            else:
                delta = event.delta
                if delta == 0:
                    return "break"
                steps = int(-delta / 120) * 2
                if steps == 0:
                    steps = -1 if delta > 0 else 1
                self.canvas.yview_scroll(steps, "units")
        except Exception:
            pass
        return "break"

    def _toggle_favorite(self, key):
        if key in self.favorites:
            self.favorites.discard(key)
        else:
            self.favorites.add(key)
        self.config_data["favorites"] = list(self.favorites)
        save_config(self.config_data)

        for refs in self.cards.values():
            refs["card"].set_favorites(self.favorites)

        if self.current_filter == "fav":
            self._apply_filter()

    def _open_calculator(self):
        if self.calc_window and self.calc_window.winfo_exists():
            self.calc_window.lift()
            self.calc_window.focus_force()
            return
        self.calc_window = CalculatorDialog(self, self.prices)

    # ═══════════════════════════════════════════════════════════
    # 🔄 AUTO-UPDATE METHODS
    # ═══════════════════════════════════════════════════════════
    def _check_update(self, silent=False):
        """بررسی آپدیت — اگه silent=True باشه، پنجره فقط وقتی نسخه‌ی جدید بود باز می‌شه"""
        try:
            self.update_btn.configure(state="disabled", text="…")
        except Exception:
            pass

        def worker():
            try:
                import update_checker as uc
                info = uc.check_for_update(timeout=10)
            except ImportError:
                info = {"available": False,
                        "error": "ماژول update_checker نصب نیست",
                        "current_version": "?", "latest_version": "?"}
            except Exception as e:
                info = {"available": False, "error": str(e),
                        "current_version": "?", "latest_version": "?"}

            self.after(0, lambda: self._on_update_check(info, silent))

        threading.Thread(target=worker, daemon=True).start()

    def _on_update_check(self, info, silent):
        try:
            self.update_btn.configure(state="normal", text="🔄")
        except Exception:
            pass

        if info.get("error"):
            if not silent:
                ToastNotification(self, f"خطا: {info['error']}",
                                   kind="error", duration=3500)
            return

        if info.get("available"):
            # اگه پنجره‌ی آپدیت بازه، دوباره باز نکن
            if (self.update_window and
                    self.update_window.winfo_exists()):
                self.update_window.lift()
                self.update_window.focus_force()
                return
            self.update_window = UpdateDialog(self, info)
        else:
            if not silent:
                cur = info.get("current_version", "?")
                ToastNotification(self,
                    f"شما آخرین نسخه رو دارید ({to_fa(cur)})",
                    kind="success", duration=2500)

    def _open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        dlg = ctk.CTkToplevel(self)
        self.settings_window = dlg
        dlg.title("تنظیمات")
        dlg.geometry("580x740")
        dlg.minsize(540, 620)
        dlg.configure(fg_color=C["bg"])
        dlg.transient(self)
        dlg.grab_set()

        try:
            ico_path = os.path.join(BASE_DIR, "icon.ico")
            if os.path.exists(ico_path):
                dlg.iconbitmap(ico_path)
        except Exception:
            pass

        try:
            self.update_idletasks()
            w, h = 580, 740
            px = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
            py = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
            dlg.geometry(f"{w}x{h}+{max(px, 0)}+{max(py, 0)}")
        except Exception:
            pass

        head = ctk.CTkFrame(dlg, fg_color=C["card"], corner_radius=0, height=76)
        head.pack(fill="x")
        head.pack_propagate(False)
        ctk.CTkLabel(head, text="⚙  تنظیمات", font=F(19, "bold"),
                     text_color=C["text"]).pack(expand=True)

        scroll = ctk.CTkScrollableFrame(
            dlg, fg_color=C["bg"],
            scrollbar_button_color=C["divider"],
            scrollbar_button_hover_color=C["gold"])
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        self._settings_section(scroll, "🔔  اعلان‌ها")
        self.notif_var = tk.BooleanVar(
            value=self.config_data.get("notifications", True))
        ctk.CTkSwitch(scroll, text="اعلان‌های دسکتاپ",
                       variable=self.notif_var, font=F(11),
                       text_color=C["text2"], progress_color=C["gold"],
                       command=self._save_notifications
                       ).pack(anchor="w", pady=(4, 16))

        self._settings_section(scroll, "🔊  صدا")
        self.sound_var = tk.BooleanVar(value=self.config_data.get("sound", True))
        ctk.CTkSwitch(scroll, text="فعال بودن صدا",
                       variable=self.sound_var, font=F(11),
                       text_color=C["text2"], progress_color=C["gold"],
                       command=self._save_sound
                       ).pack(anchor="w", pady=(4, 12))

        ctk.CTkLabel(scroll, text="میزان صدای هشدار",
                     font=F(10, "bold"), text_color=C["text3"],
                     anchor="e").pack(anchor="e", pady=(6, 4))

        vol_row = ctk.CTkFrame(scroll, fg_color="transparent")
        vol_row.pack(fill="x", pady=(0, 4))

        self.volume_lbl = ctk.CTkLabel(
            vol_row, text=f"{int(self.config_data.get('volume', 70))}٪",
            font=F(11, "bold"), text_color=C["gold"], width=44)
        self.volume_lbl.pack(side="left")

        self.volume_var = tk.DoubleVar(
            value=self.config_data.get("volume", 70))
        self.volume_slider = ctk.CTkSlider(
            vol_row, from_=0, to=100,
            variable=self.volume_var, number_of_steps=20,
            progress_color=C["gold"], button_color=C["gold_hi"],
            button_hover_color=C["gold"],
            command=self._on_volume_change)
        self.volume_slider.pack(side="right", fill="x", expand=True)

        ctk.CTkButton(
            scroll, text="🔔  تست صدا",
            font=F(10, "bold"),
            fg_color=C["inner"], hover_color=C["card_hover"],
            text_color=C["text2"], corner_radius=10, height=36,
            command=lambda: sound.play("update", blocking=False)
        ).pack(fill="x", pady=(10, 4))

        self._settings_section(scroll, "⏱  بروزرسانی خودکار")
        self.refresh_interval_var = tk.StringVar(
            value=self._interval_to_label(
                self.config_data.get("auto_refresh", 60)))

        interval_options = ["خاموش", "۱ دقیقه", "۵ دقیقه",
                            "۱۰ دقیقه", "۳۰ دقیقه"]
        ctk.CTkOptionMenu(
            scroll, values=interval_options,
            variable=self.refresh_interval_var,
            font=F(11), height=44, fg_color=C["inner"],
            button_color=C["divider"], button_hover_color=C["gold"],
            text_color=C["text"], dropdown_font=F(11), corner_radius=10,
            command=self._save_refresh_interval
        ).pack(fill="x", pady=(4, 16))

        self._settings_section(scroll, "📊  داده‌ها")
        self._settings_row(scroll, "تعداد کل بازارها", to_fa(len(ITEMS)))
        self._settings_row(scroll, "منبع داده", "ارزدیجیتال + نوبیتکس")
        self._settings_row(scroll, "تعداد دلخواه", to_fa(len(self.favorites)))

        ctk.CTkButton(dlg, text="بستن", font=F(11, "bold"),
                       fg_color=C["gold"], hover_color=C["gold_hi"],
                       text_color="#0A0E18", corner_radius=10, height=44,
                       command=dlg.destroy
                       ).pack(fill="x", padx=16, pady=(0, 16))

    def _settings_section(self, parent, title):
        ctk.CTkLabel(parent, text=title, font=F(12, "bold"),
                     text_color=C["gold"], anchor="e"
                     ).pack(anchor="e", pady=(10, 6))

    def _settings_row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=10,
                            border_width=1, border_color=C["card_border"])
        row.pack(fill="x", pady=4)
        r_in = ctk.CTkFrame(row, fg_color="transparent")
        r_in.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(r_in, text=label, font=F(10, "bold"),
                     text_color=C["text3"]).pack(side="right")
        ctk.CTkLabel(r_in, text=str(value), font=F(11, "bold"),
                     text_color=C["text"]).pack(side="left")

    def _on_volume_change(self, value):
        v = int(value)
        self.volume_lbl.configure(text=f"{v}٪")
        self.config_data["volume"] = v
        save_config(self.config_data)
        sound.set_volume(v / 100.0)

    def _interval_to_label(self, seconds):
        try:
            seconds = int(seconds)
        except Exception:
            seconds = 60
        if seconds <= 0:
            return "خاموش"
        options = [(60, "۱ دقیقه"), (300, "۵ دقیقه"),
                   (600, "۱۰ دقیقه"), (1800, "۳۰ دقیقه")]
        closest = min(options, key=lambda x: abs(x[0] - seconds))
        return closest[1]

    def _label_to_interval(self, label):
        return {"خاموش": 0, "۱ دقیقه": 60, "۵ دقیقه": 300,
                "۱۰ دقیقه": 600, "۳۰ دقیقه": 1800}.get(label, 60)

    def _save_refresh_interval(self, label=None):
        label = label or self.refresh_interval_var.get()
        secs = self._label_to_interval(label)
        self.config_data["auto_refresh"] = secs
        save_config(self.config_data)

        if self._auto_job:
            try:
                self.after_cancel(self._auto_job)
            except Exception:
                pass
            self._auto_job = None
        self._schedule_auto_refresh()
        ToastNotification(self, f"بازه‌ی بروزرسانی: {label}",
                           kind="success", duration=2000)

    def _save_notifications(self):
        self.config_data["notifications"] = bool(self.notif_var.get())
        save_config(self.config_data)

    def _save_sound(self):
        val = bool(self.sound_var.get())
        self.config_data["sound"] = val
        save_config(self.config_data)
        sound.set_enabled(val)

    def _schedule_auto_refresh(self):
        if self._closing:
            return
        secs = self.config_data.get("auto_refresh", 60)
        if secs <= 0:
            self._auto_job = None
            return
        self._auto_job = self.after(secs * 1000, self._on_auto_refresh)

    def _on_auto_refresh(self):
        if self._closing:
            return
        self.load_all_prices()
        self._schedule_auto_refresh()

    def _start_polling(self):
        if self._poll_started:
            return
        self._poll_started = True
        self.after(50, self._poll_price_queue)

    def load_all_prices(self):
        if self.is_loading:
            return
        self.is_loading = True

        self.status_badge.set_state("updating")
        self.ov_status.set_value("در حال بروزرسانی", C["warning"])
        self.refresh_btn.configure(state="disabled", text="↻  ...")

        for refs in self.cards.values():
            refs["card"].set_loading()

        threading.Thread(target=self._worker, daemon=True).start()

    def _fetch_item(self, item):
        try:
            price, change = fetch_price(item)
            return item["key"], (price, change)
        except Exception:
            return item["key"], (None, None)

    def _worker(self):
        results = {}
        try:
            with ThreadPoolExecutor(max_workers=min(12, len(ITEMS))) as ex:
                futures = {ex.submit(self._fetch_item, it): it for it in ITEMS}
                for fut in as_completed(futures):
                    if self._closing:
                        break
                    item = futures[fut]
                    try:
                        key, result = fut.result()
                    except Exception:
                        key, result = item["key"], (None, None)
                    results[key] = result
                    self._price_queue.put(("item", key, result[0], result[1]))
        finally:
            self._price_queue.put(("done", results))

    def _poll_price_queue(self):
        if self._closing:
            return
        finished = None
        try:
            while True:
                try:
                    event = self._price_queue.get_nowait()
                except queue.Empty:
                    break
                if event[0] == "item":
                    _, key, price, change = event
                    self._update_card(key, price, change)
                elif event[0] == "done":
                    finished = event[1]
        except Exception:
            pass

        if finished is not None:
            self._on_finish(finished)

        try:
            if self.winfo_exists() and not self._closing:
                self.after(50, self._poll_price_queue)
        except Exception:
            pass

    def _update_card(self, key, price, change):
        refs = self.cards.get(key)
        if not refs:
            return
        try:
            refs["card"].set_price(price, change)
        except Exception:
            pass

    def _on_finish(self, results):
        old = self.prices
        merged = dict(old)
        for k, v in results.items():
            if v and v[0]:
                merged[k] = v
            elif k not in merged:
                merged[k] = v

        new_ok = sum(1 for (p, _) in results.values() if p)
        if new_ok > 0:
            self.prices = merged

        ok = sum(1 for (p, _) in self.prices.values() if p)
        total = len(ITEMS)
        now = datetime.now().strftime("%H:%M:%S")
        self._last_update = to_fa(now)

        self.last_update_lbl.configure(text=self._last_update)
        self.ov_update.set_value(self._last_update, C["cyan"])

        if new_ok > 0:
            sound.play("update")

        if new_ok == total:
            self.status_badge.set_state("connected")
            self.ov_status.set_value("متصل", C["success"])
            self.ov_live.set_value(f"{to_fa(ok)} / {to_fa(total)}", C["success"])
            ToastNotification(self, "قیمت‌ها با موفقیت بروزرسانی شد",
                               kind="success", duration=2500)
        elif new_ok > 0:
            self.status_badge.set_state("updating")
            self.ov_status.set_value(f"جزئی ({to_fa(new_ok)}/{to_fa(total)})",
                                       C["warning"])
            self.ov_live.set_value(f"{to_fa(ok)} / {to_fa(total)}", C["warning"])
            ToastNotification(self,
                              f"{to_fa(new_ok)} از {to_fa(total)} دریافت شد",
                              kind="warning", duration=2500)
        else:
            self.status_badge.set_state("error")
            self.ov_status.set_value("خطا", C["danger"])
            self.ov_live.set_value(f"{to_fa(ok)} / {to_fa(total)}", C["danger"])
            ToastNotification(self, "دریافت قیمت‌ها ناموفق بود",
                               kind="error", duration=3000)

        self.refresh_btn.configure(state="normal", text="↻  بروزرسانی")
        self.is_loading = False

        if old and new_ok > 0:
            self._check_notifications(old, results)

    def _check_notifications(self, old, new):
        moves = []
        for key, (new_price, _) in new.items():
            if not new_price:
                continue
            old_price = old.get(key, (None, None))[0]
            if not old_price:
                continue
            try:
                pct = ((new_price - old_price) / old_price) * 100
            except Exception:
                continue
            if abs(pct) >= 3.0:
                item = next((x for x in ITEMS if x["key"] == key), None)
                if item:
                    moves.append((item["name"], pct))

        if not moves:
            return
        moves.sort(key=lambda x: abs(x[1]), reverse=True)
        top = moves[:3]

        sound.play("alert")

        if self.config_data.get("notifications", True):
            lines = []
            for name, pct in top:
                sign = "+" if pct > 0 else ""
                arrow = "▲" if pct > 0 else "▼"
                lines.append(f"{name}: {sign}{pct:.2f}% {arrow}")
            threading.Thread(
                target=send_native_notification,
                args=("TeleCoin — تغییرات بازار", "\n".join(lines)),
                daemon=True).start()

    def _tick_clocks(self):
        if self._closing:
            return
        try:
            for chip in self.clock_chips:
                if chip.winfo_exists():
                    chip.update_time()
        except Exception:
            pass
        try:
            self.after(1000, self._tick_clocks)
        except Exception:
            pass

    def _on_close(self):
        self._closing = True
        try:
            if self._auto_job:
                self.after_cancel(self._auto_job)
                self._auto_job = None
        except Exception:
            pass

        for w in [self.calc_window, self.settings_window, self.update_window]:
            try:
                if w and w.winfo_exists():
                    try:
                        w.grab_release()
                    except Exception:
                        pass
                    w.destroy()
            except Exception:
                pass

        try:
            self.destroy()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 62)
    print("  💰  TeleCoin Pro — Market Terminal v6.4")
    print(f"  📊 {len(ITEMS)} markets | File: 1.py")
    print("═" * 62)
    print("\n[1/2]  آماده‌سازی فونت‌ها...")
    download_fonts_if_needed()
    register_fonts()

    print("[2/2]  راه‌اندازی برنامه...\n")
    app = TeleCoinApp()
    app.mainloop()