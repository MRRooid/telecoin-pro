"""
🔄 TeleCoin Auto-Updater
ماژول بررسی و دانلود آپدیت از GitHub
"""
import os
import json
import shutil
import hashlib
import tempfile
import subprocess
import sys
import requests
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# ⚙️ تنظیمات — این‌ها با اطلاعات تو پر شده
# ═══════════════════════════════════════════════════════════════
GITHUB_USER = "MRRooid"                    # ← یوزرنیم GitHub تو
GITHUB_REPO = "telecoin-pro"                # ← اسم ریپو
GITHUB_BRANCH = "main"                      # ← شاخه اصلی

VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/version.json"
FILE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/1.py"

LOCAL_VERSION_FILE = "version.json"
LOCAL_APP_FILE = "1.py"
BACKUP_SUFFIX = ".backup"


# ═══════════════════════════════════════════════════════════════
# 🔢 نسخه‌ی محلی
# ═══════════════════════════════════════════════════════════════
def get_local_version():
    """خوندن نسخه‌ی محلی از version.json"""
    try:
        if os.path.exists(LOCAL_VERSION_FILE):
            with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return str(data.get("version", "0.0"))
    except Exception:
        pass
    return "0.0"


def save_local_version(version, changelog=""):
    """ذخیره‌ی نسخه در version.json"""
    try:
        data = {
            "version": str(version),
            "updated_at": datetime.now().isoformat(),
            "changelog": changelog,
        }
        with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# 🌐 چک آپدیت از GitHub
# ═══════════════════════════════════════════════════════════════
def check_for_update(timeout=10):
    """
    بررسی وجود نسخه‌ی جدید
    Returns:
        dict با کلیدهای:
            - available: bool
            - current_version: str
            - latest_version: str
            - changelog: str
            - download_url: str
            - error: str (در صورت خطا)
    """
    result = {
        "available": False,
        "current_version": get_local_version(),
        "latest_version": None,
        "changelog": "",
        "download_url": FILE_URL,
        "error": None,
    }

    try:
        r = requests.get(VERSION_URL, timeout=timeout)
        if not r.ok:
            result["error"] = f"HTTP {r.status_code}"
            return result

        remote = r.json()
        latest = str(remote.get("version", "0.0"))
        result["latest_version"] = latest
        result["changelog"] = remote.get("changelog", "")

        # مقایسه‌ی نسخه‌ها
        if _version_newer(latest, result["current_version"]):
            result["available"] = True
            # اگه download_url توی version.json بود، از اون استفاده کن
            if remote.get("download_url"):
                result["download_url"] = remote["download_url"]

    except requests.exceptions.Timeout:
        result["error"] = "اتصال به سرور timeout خورد"
    except requests.exceptions.ConnectionError:
        result["error"] = "اتصال اینترنت برقرار نیست"
    except Exception as e:
        result["error"] = str(e)

    return result


def _version_newer(new, old):
    """مقایسه‌ی دو نسخه (مثلاً 6.2 vs 6.3)"""
    try:
        new_parts = [int(x) for x in str(new).split(".")]
        old_parts = [int(x) for x in str(old).split(".")]

        # هم‌طول کردن
        max_len = max(len(new_parts), len(old_parts))
        new_parts += [0] * (max_len - len(new_parts))
        old_parts += [0] * (max_len - len(old_parts))

        return new_parts > old_parts
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
# 📥 دانلود و نصب آپدیت
# ═══════════════════════════════════════════════════════════════
def download_update(download_url, progress_callback=None, timeout=30):
    """
    دانلود فایل جدید
    Returns:
        (success: bool, temp_path: str or None, error: str)
    """
    try:
        r = requests.get(download_url, timeout=timeout, stream=True)
        if not r.ok:
            return False, None, f"HTTP {r.status_code}"

        # ذخیره در فایل موقت
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".py", prefix="telecoin_")
        os.close(tmp_fd)

        total = int(r.headers.get("content-length", 0))
        downloaded = 0

        with open(tmp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        pct = int((downloaded / total) * 100)
                        progress_callback(pct)

        # بررسی حجم فایل (نباید کمتر از 5KB باشه)
        if os.path.getsize(tmp_path) < 5000:
            os.remove(tmp_path)
            return False, None, "فایل دانلود شده خیلی کوچکه (احتمالاً خرابه)"

        return True, tmp_path, ""

    except requests.exceptions.Timeout:
        return False, None, "دانلود timeout خورد"
    except Exception as e:
        return False, None, str(e)


def install_update(temp_path, version, changelog=""):
    """
    جایگزینی فایل قدیمی با فایل جدید
    Returns:
        (success: bool, error: str, backup_path: str or None)
    """
    try:
        if not os.path.exists(LOCAL_APP_FILE):
            # اگه فایل اصلی نبود، فقط کپی کن
            shutil.copy2(temp_path, LOCAL_APP_FILE)
            save_local_version(version, changelog)
            os.remove(temp_path)
            return True, "", None

        # بکاپ گرفتن از فایل قدیمی
        backup_path = LOCAL_APP_FILE + BACKUP_SUFFIX
        try:
            shutil.copy2(LOCAL_APP_FILE, backup_path)
        except Exception:
            backup_path = None

        # جایگزینی فایل اصلی
        shutil.copy2(temp_path, LOCAL_APP_FILE)

        # ذخیره‌ی نسخه‌ی جدید
        save_local_version(version, changelog)

        # پاک کردن فایل موقت
        try:
            os.remove(temp_path)
        except Exception:
            pass

        return True, "", backup_path

    except Exception as e:
        return False, str(e), None


def rollback_update():
    """
    برگرداندن به نسخه‌ی قبلی از بکاپ
    Returns:
        (success: bool, error: str)
    """
    try:
        backup_path = LOCAL_APP_FILE + BACKUP_SUFFIX
        if not os.path.exists(backup_path):
            return False, "بکاپ پیدا نشد"

        shutil.copy2(backup_path, LOCAL_APP_FILE)
        os.remove(backup_path)
        return True, ""
    except Exception as e:
        return False, str(e)


def restart_app():
    """
    ریستارت خودکار برنامه
    """
    try:
        python = sys.executable
        script = os.path.abspath(LOCAL_APP_FILE)

        if os.name == "nt":
            # ویندوز
            subprocess.Popen(
                [python, script],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                          | subprocess.DETACHED_PROCESS,
                close_fds=True,
            )
        else:
            # لینوکس / مک
            subprocess.Popen(
                [python, script],
                start_new_session=True,
                close_fds=True,
            )
        return True
    except Exception as e:
        print(f"[Restart] خطا: {e}")
        return False


def get_file_hash(path):
    """گرفتن SHA-256 فایل (برای تأیید صحت)"""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# 🧪 تست سریع (وقتی این فایل رو مستقیم اجرا کنی)
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═" * 60)
    print("  🔄 TeleCoin Auto-Updater — Test")
    print("═" * 60)
    print(f"\n  GitHub User : {GITHUB_USER}")
    print(f"  Repo        : {GITHUB_REPO}")
    print(f"  Branch      : {GITHUB_BRANCH}")
    print(f"\n  VERSION_URL : {VERSION_URL}")
    print(f"  FILE_URL    : {FILE_URL}")
    print(f"\n  نسخه محلی   : {get_local_version()}")

    print("\n  🌐 در حال بررسی آپدیت از GitHub...")
    info = check_for_update(timeout=15)

    if info.get("error"):
        print(f"\n  ❌ خطا: {info['error']}")
    elif info.get("available"):
        print(f"\n  ✅ آپدیت موجود است!")
        print(f"     نسخه فعلی  : {info['current_version']}")
        print(f"     نسخه جدید  : {info['latest_version']}")
        print(f"     تغییرات    : {info['changelog']}")
        print(f"     دانلود از  : {info['download_url']}")
    else:
        print(f"\n  ℹ️  شما آخرین نسخه رو دارید ({info['current_version']})")

    print("\n" + "═" * 60)