# main.py
# WinTelemetryService - Headless Hotkey AI Assistant
# Windows 10/11, Python 3.10+
# ------------------------------------------------------------

import time
import signal
import threading
import ctypes
import keyboard
import psutil
import win32clipboard as wc
import win32con
import win32gui
import win32process
import win32api
import uuid
import re
import os
import builtins
from typing import List

# Yerel modüller
from query_ai import query_ai, classify_text
from ui_toast import show_answer_toast, show_letter_toast

# =============================================================
# 1) AYARLAR
# =============================================================
CHUNK_MAX_CHARS = 2500
CLIPBOARD_WAIT_TIMEOUT = 1.0
PASTE_PREP_SLEEP = 0.12  # DEĞİŞİKLİK: Değer artırıldı
PASTE_AFTER_SLEEP = 0.08 # DEĞİŞİKLİK: Değer artırıldı
ENTER_BETWEEN_PIECES_SLEEP = 0.02
TYPE_OUT_PER_CHAR_SLEEP = 0.006
ROBUST_COPY_ATTEMPTS = 3
COMPRESS_BLANK_LINES_BEFORE_PASTE = True

# Varsayılan olarak tamamen sessiz çalış (iz bırakma)
# İsteğe bağlı debug için: ortam değişkeni WTS_DEBUG=1
SILENT = os.getenv("WTS_SILENT", "1") == "1"
DEBUG = os.getenv("WTS_DEBUG", "0") == "1"

if SILENT and not DEBUG:
    # Tüm print çağrılarını kapat
    def _noop(*args, **kwargs):
        pass
    builtins.print = _noop

# Hotkey'ler
HOTKEY_COLLECT_SUBMIT = 'ctrl+insert'
HOTKEY_PASTE_NEXT = 'shift+insert'
HOTKEY_PASTE_NEXT_ALT = 'ctrl+shift+v' # Yedek
HOTKEY_EXIT = 'ctrl+alt+end' # Güvenli çıkış

# Windows key codes
VK_NUMLOCK = 0x90
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_INSERT = 0x2D
VK_RETURN = 0x0D
VK_V = 0x56
VK_C = 0x43
KEYEVENTF_KEYUP = 0x2
WM_COPY = 0x0301

CONSOLE_PROCESSES = {
    "cmd.exe", "powershell.exe", "pwsh.exe", "windowsterminal.exe",
    "python.exe", "pythonw.exe", "conhost.exe",
    "idea64.exe", "code.exe", "devenv.exe"
}

# =============================================================
# 2) DURUM VE YARDIMCILAR
# =============================================================
state = {
    "busy": False,
    "chunks": [],
    "idx": 0,
    "lock": threading.Lock(),
    "exit": False,
}

def toggle_numlock():
    ctypes.windll.user32.keybd_event(VK_NUMLOCK, 0, 0, 0)
    ctypes.windll.user32.keybd_event(VK_NUMLOCK, 0, KEYEVENTF_KEYUP, 0)

def blink_numlock(count=1, delay=0.12):
    for i in range(count):
        toggle_numlock()
        time.sleep(delay)
        toggle_numlock()
        if i < count - 1:
            time.sleep(delay)

def get_foreground_exe_name() -> str:
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name()
    except Exception:
        return ""

# =============================================================
# 3) GÜVENİLİR KOPYALAMA VE YAPIŞTIRMA
# =============================================================

def get_clipboard_text() -> str:
    # (Bu fonksiyon hotkey_chunk_demo.py'den alınmıştır)
    text = ""
    try:
        wc.OpenClipboard()
        data = wc.GetClipboardData(win32con.CF_UNICODETEXT)
        text = data if isinstance(data, str) else str(data)
    finally:
        try: wc.CloseClipboard()
        except Exception: pass
    return text

def set_clipboard_text(text: str):
    # (Bu fonksiyon hotkey_chunk_demo.py'den alınmıştır)
    try:
        wc.OpenClipboard()
        wc.EmptyClipboard()
        wc.SetClipboardData(win32con.CF_UNICODETEXT, text)
    finally:
        try: wc.CloseClipboard()
        except Exception: pass

def robust_copy_selection() -> str:
    # (Bu fonksiyon hotkey_chunk_demo.py'den alınmıştır, sadeliği korumak için aynı mantık kullanılmıştır)
    original = get_clipboard_text()
    marker = f"__SNAP__{uuid.uuid4()}__"
    set_clipboard_text(marker)
    
    keyboard.send("ctrl+c")
    time.sleep(0.2) # Panonun güncellenmesi için kısa bir bekleme
    
    copied_text = get_clipboard_text()
    
    if copied_text != marker and copied_text:
        return copied_text.strip()
    else:
        # Başarısız olursa panoyu eski haline getir
        set_clipboard_text(original)
        print("[WARN] Metin kopyalanamadı.")
        return ""

def paste_chunk_with_2line_cap(chunk_text: str):
    # (Bu fonksiyon hotkey_chunk_demo.py'den alınmıştır)
    if COMPRESS_BLANK_LINES_BEFORE_PASTE:
        chunk_text = re.sub(r'\n{3,}', '\n\n', chunk_text)

    pieces = [chunk_text]
    # 2 satır limiti sezgisel olarak, belirli pencerelerde uygulanabilir. Şimdilik genel yapıştırma kullanılıyor.
    # Gerçek bir 2 satır limiti için get_foreground_exe_name() ile hedef uygulama kontrol edilebilir.
    # Örn: if get_foreground_exe_name() in RESTRICTED_APPS: pieces = split_by_lines(chunk_text, 2)

    total = len(pieces)
    for i, piece in enumerate(pieces, 1):
        set_clipboard_text(piece)
        time.sleep(PASTE_PREP_SLEEP)
        
        try:
            keyboard.send('shift+insert')
            time.sleep(PASTE_AFTER_SLEEP)
        except Exception:
            try:
                print("[WARN] Shift+Insert başarısız, Ctrl+V denenecek...")
                keyboard.send('ctrl+v')
                time.sleep(PASTE_AFTER_SLEEP)
            except Exception:
                print("[WARN] Yapıştırma başarısız, karakter karakter yazılıyor...")
                keyboard.write(piece, delay=TYPE_OUT_PER_CHAR_SLEEP)
        
        if i < total:
            keyboard.send('enter')
            time.sleep(ENTER_BETWEEN_PIECES_SLEEP)

# =============================================================
# 4) ANA İŞLEVLER
# =============================================================

def handle_collect_and_submit():
    with state["lock"]:
        if state["busy"]:
            return
        state["busy"] = True

    try:
        copied_text = robust_copy_selection()
        if not copied_text or len(copied_text.strip()) < 5:
            print("[WARN] Kopyalanan metin çok kısa, işlem iptal edildi.")
            return

        print("[INFO] Metin alındı, AI sorgusu gönderiliyor...")
        answer = query_ai(copied_text)

        if not answer or answer.startswith("[HATA]"):
            print(f"[ERROR] {answer}")
            blink_numlock(3, 0.15) # Hata sinyali
            return
        
        # İsteğe bağlı: debug modunda cevabı dosyaya bırak (varsayılan kapalı)
        # Debug dosyası bırakma kaldırıldı (tamamen izsiz)

        # Cevap türüne göre sunum
        classification = classify_text(copied_text)

        # Sınıf değerini string'e çevirerek karşılaştır (Enum.value)
        qtype = getattr(classification.type, 'value', str(classification.type))
        is_mcq_or_short = qtype in ('multiple_choice', 'short_answer')

        if qtype == 'multiple_choice':
            # AI'dan gelen cevaptan tek harfi ayıkla ve mini toast göster
            m = re.search(r"\b([A-E])\b", answer.strip().upper())
            letter = m.group(1) if m else answer.strip()[:1].upper()
            print(f"[INFO] MCQ tespit edildi. Doğru şık: {letter}")
            # Panoya yerleştir ve tek parçalık kuyruğa al
            state["chunks"] = [letter]
            state["idx"] = 0
            set_clipboard_text(letter)
            blink_numlock(1)
            # Küçük toast (sessiz modda da kısa süreli görsel)
            threading.Thread(target=show_letter_toast, args=(letter,), daemon=True).start()
        elif is_mcq_or_short and len(answer.strip()) < 120:
            print(f"[INFO] Kısa cevap tespit edildi. Toast gösteriliyor: {answer}")
            # Panoya yerleştir ve tek parçalık kuyruğa al
            state["chunks"] = [answer.strip()]
            state["idx"] = 0
            set_clipboard_text(state["chunks"][0])
            blink_numlock(1)
            threading.Thread(target=show_answer_toast, args=(answer,), daemon=True).start()
        else:
            print("[INFO] Kod/Uzun cevap tespit edildi. Parçalara ayrılıyor...")
            chunks = re.split(r'(\n---\n)', answer) # Basit bir ayraç
            state["chunks"] = [c.strip() for c in chunks if c.strip() and c != '---']
            state["idx"] = 0
            
            if not state["chunks"]:
                 print("[WARN] Cevap parçalara ayrılamadı.")
                 return

            set_clipboard_text(state["chunks"][0])
            blink_count = 2 if len(state["chunks"]) > 1 else 1
            blink_numlock(blink_count)
            print(f"[INFO] {len(state['chunks'])} parça hazır. İlk parça panoda. Yapıştırmak için {HOTKEY_PASTE_NEXT} kullanın.")

    finally:
        with state["lock"]:
            state["busy"] = False


def handle_paste_next():
    with state["lock"]:
        if not state["chunks"]:
            return
        idx = state["idx"]
        total = len(state["chunks"])

    if idx >= total:
        print("[INFO] Tüm parçalar yapıştırıldı.")
        blink_numlock(2)
        return

    chunk = state["chunks"][idx]
    if get_clipboard_text() != chunk:
        set_clipboard_text(chunk)
        time.sleep(PASTE_PREP_SLEEP)

    print(f"[INFO] Parça {idx + 1}/{total} yapıştırılıyor...")
    paste_chunk_with_2line_cap(chunk)

    with state["lock"]:
        state["idx"] += 1
        done = (state["idx"] >= total)
        if not done:
            set_clipboard_text(state["chunks"][state["idx"]])
            print("[INFO] Sıradaki parça panoya kopyalandı.")

    if done:
        print("[INFO] Tüm parçalar bitti.")
        blink_numlock(2)


# =============================================================
# 5) SERVİS KURULUMU VE DÖNGÜ
# =============================================================

def ensure_single_instance(name="Global\\WinTelemetryServiceV1"):
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, name)
    return ctypes.windll.kernel32.GetLastError() != 183

def request_exit():
    with state["lock"]:
        state["exit"] = True
    print("[INFO] Çıkış istendi.")

def main():
    if not ensure_single_instance():
        print("[INFO] Zaten çalışıyor, çıkılıyor.")
        return

    print("[INFO] WinTelemetryService Başlatıldı.")
    print(f"  - {HOTKEY_COLLECT_SUBMIT.ljust(18)}: Seçili metni al ve gönder")
    print(f"  - {HOTKEY_PASTE_NEXT.ljust(18)}: Sıradaki cevap parçasını yapıştır")
    print(f"  - {HOTKEY_EXIT.ljust(18)}: Güvenli çıkış")

    keyboard.add_hotkey(HOTKEY_COLLECT_SUBMIT, handle_collect_and_submit, suppress=True)
    keyboard.add_hotkey(HOTKEY_PASTE_NEXT, handle_paste_next, suppress=True)
    keyboard.add_hotkey(HOTKEY_PASTE_NEXT_ALT, handle_paste_next, suppress=True)
    keyboard.add_hotkey(HOTKEY_EXIT, request_exit, suppress=True)

    try:
        while not state["exit"]:
            time.sleep(0.2)
    finally:
        print("[INFO] Çıkılıyor...")
        keyboard.unhook_all()

if __name__ == "__main__":
    # Konsol penceresini gizle (script olarak çalıştırılsa bile)
    try:
        if os.name == "nt" and os.getenv("WTS_HIDE_CONSOLE", "1") == "1":
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass
    main()
