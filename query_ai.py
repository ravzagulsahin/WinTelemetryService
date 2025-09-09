# query_ai.py
from dotenv import load_dotenv
import os, time, random, sys
from pathlib import Path
import requests
from question_classifier import classify_text, get_appropriate_prompt, should_use_lab_prompt

def _load_env():
    """Load .env from the executable/script directory first, then fallback."""
    try:
        if getattr(sys, 'frozen', False):  # PyInstaller onefile/onedir
            app_dir = Path(sys.executable).parent
        else:
            app_dir = Path(__file__).parent
        candidate = app_dir / ".env"
        if candidate.exists():
            load_dotenv(dotenv_path=candidate)
        else:
            # Fallback to default search (current working directory)
            load_dotenv()
    except Exception:
        # As a last resort, attempt default
        load_dotenv()

_load_env()
API_KEY = os.getenv("GEMINI_API_KEY")

# Bu durumlar geçici (retry edilir)
TRANSIENT_STATUS = {429, 500, 502, 503, 504}

def _post_gemini(final_prompt: str, max_tokens: int = 4096, timeout: int = 45) -> str:
    """
    Gemini 1.5 Flash'a isteği atar. final_prompt: modele gidecek TAM metin.
    max_tokens: çıktı token üst sınırı.
    """
    if not API_KEY:
        return "[HATA] API anahtarı bulunamadı (.env dosyasını kontrol et)"

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash-latest:generateContent?key={API_KEY}"
    )
    data = {
        "contents": [{"parts": [{"text": final_prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": max_tokens
        }
    }

    r = requests.post(url, json=data, timeout=timeout)
    # Geçici hataları üst katmana özel işaretle
    if r.status_code in TRANSIENT_STATUS:
        return f"[HATA_HTTP]{r.status_code}"

    # Diğer HTTP hataları için exception
    r.raise_for_status()

    j = r.json()
    cands = j.get("candidates", [])
    if not cands:
        return f"[HATA] Beklenmeyen yanıt: {j}"
    parts = cands[0].get("content", {}).get("parts", [])
    if not parts:
        return f"[HATA] Beklenmeyen yanıt: {j}"
    text = parts[0].get("text", "")
    if not text:
        return "[HATA] Boş yanıt geldi."

    # Ufak temizlik: baş/son boşluk, üçlü fence kırpma
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text.strip("`").strip()
        # dil etiketi varsa ilk satırı da kırp
        if "\n" in text:
            first, rest = text.split("\n", 1)
            # örn: 'java' gibi dil etiketi olabilir
            if len(first) < 12 and first.isalpha():
                text = rest.strip()
    return text

def query_ai(question: str) -> str:
    """
    Soru metnini alır:
      - Sınıflandır (short/mcq/lab vs.)
      - Uygun promptu kur (lab ise lab promptu; yoksa classifier tabanlı prompt)
      - Dayanıklı retry ile Gemini'den yanıt al
    """
    # 1) Sınıflandırma
    classification = classify_text(question)
    print(f"[DEBUG] Detected type={classification.type.value}, style={classification.suggested_prompt_style}")

    # 2) Prompt oluştur
    final_prompt = get_appropriate_prompt(question)

    # Lab skeleton ise özel prompt (aynı dosyadaki fonksiyonu direkt çağır)
    if should_use_lab_prompt(question):
        try:
            final_prompt = build_lab_prompt(question)
            print("[INFO] Lab skeleton detected → using lab prompt")
        except Exception as e:
            print(f"[WARN] Lab prompt kurulamadı, generic prompt kullanılacak: {e}")

    """
    Dayanıklı sorgu: 3 deneme, exponential backoff + jitter.
    1. deneme: 4096 token, 45s timeout
    2. deneme: 4096 token, 45s timeout (bekle)
    3. deneme: 3072 token, 45s timeout (daha küçük çıktı dene)
    """
    attempts = [
        {"max_tokens": 4096, "timeout": 45},
        {"max_tokens": 4096, "timeout": 45},
        {"max_tokens": 3072, "timeout": 45},
    ]
    for i, cfg in enumerate(attempts):
        try:
            resp = _post_gemini(final_prompt, **cfg)
            if isinstance(resp, str) and resp.startswith("[HATA_HTTP]"):
                # 429/500/502/503/504 gibi → backoff
                try:
                    code = int(resp.replace("[HATA_HTTP]", "") or "0")
                except Exception:
                    code = 0
                sleep_s = (1.5 ** i) + random.uniform(0.0, 0.6)
                print(f"[WARN] HTTP {code}, yeniden deneme #{i+1} sonrası bekleme: {sleep_s:.2f}s")
                time.sleep(sleep_s)
                continue
            return resp
        except requests.exceptions.RequestException as e:
            sleep_s = (1.5 ** i) + random.uniform(0.0, 0.6)
            print(f"[WARN] Ağ/HTTP hatası: {e}. Yeniden deneme #{i+1} için bekleme: {sleep_s:.2f}s")
            time.sleep(sleep_s)
            continue
        except Exception as e:
            return f"[HATA] Cevap alınamadı: {e}"

    return "[HATA] Geçici servis hataları nedeniyle yanıt alınamadı (çok denendi)."

# Lab Report Skeleton için özel prompt
def build_lab_prompt(user_question: str) -> str:
    """
    İskelet tamamlatma için sıkı yönergeler.
    Gerekirse burayı senin şablonlarına göre genişletebilirsin.
    """
    return (
        "TASK: Complete the given Java class skeletons (Product, CartItem, ShoppingCart) ONLY.\n"
        "RULES:\n"
        "- Replace every '____' and '___ ____' with correct Java keywords and types.\n"
        "- Keep TODO comments exactly as they are.\n"
        "- Do NOT output any other problem.\n"
        "- Return a single Java code block only.\n"
        "INPUT:\n" + user_question
    )
