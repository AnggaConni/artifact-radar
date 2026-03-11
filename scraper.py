import os
import json
import google.generativeai as genai
import hashlib
from datetime import datetime, timedelta

# ==============================================================================
# 0. SISTEM HISTORY & PENJADWALAN
# ==============================================================================
# Menggunakan path absolut agar aman saat dijalankan di lingkungan cloud/server
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
DATA_FILE = os.path.join(BASE_DIR, "data.json")
SCRIPT_FILE = os.path.abspath(__file__)

def get_file_hash(filepath):
    """Menghitung hash MD5 untuk mendeteksi perubahan pada script ini."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def should_crawl():
    # Syarat 1: Jika belum ada history (baru pertama kali jalan)
    if not os.path.exists(HISTORY_FILE):
        print("Status: File history tidak ditemukan. Memulai crawl pertama.")
        return True

    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except Exception:
        print("Status: File history korup. Melakukan crawl ulang.")
        return True

    # Syarat 2: Jika script python di-update (hash / sidik jari file berubah)
    current_hash = get_file_hash(SCRIPT_FILE)
    if history.get("script_hash") != current_hash:
        print(f"Status: Perubahan script terdeteksi (Hash: {current_hash[:8]}). Crawl ulang.")
        return True

    # Syarat 3: Jika sudah 7 hari dari crawl terakhir
    last_crawl_str = history.get("last_crawl_date")
    if last_crawl_str:
        last_crawl_date = datetime.fromisoformat(last_crawl_str)
        if datetime.now() - last_crawl_date >= timedelta(days=7):
            print("Status: Sudah 1 minggu berlalu. Memulai crawl berkala.")
            return True

    print("Status: Kondisi belum terpenuhi. Sistem istirahat untuk menghemat API.")
    return False

def save_history():
    """Menyimpan tanggal crawl dan hash script terbaru ke history.json"""
    history = {
        "last_crawl_date": datetime.now().isoformat(),
        "script_hash": get_file_hash(SCRIPT_FILE)
    }
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# ------------------------------------------------------------------------------
# CEK KONDISI SEBELUM LANJUT
# ------------------------------------------------------------------------------
if not should_crawl():
    # Keluar dengan kode 0 (Sukses) agar GitHub Action tidak menganggap ini error
    exit(0)

# ==============================================================================
# 1. KONFIGURASI GEMINI AI
# ==============================================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY tidak ditemukan di environment variables.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# ==============================================================================
# 2. SIMULASI CRAWLING DATA (Global Context)
# ==============================================================================
raw_scraped_data = """
Listing 1: Authentic Egyptian Ushabti figure, Late Period faience, recently unearthed in Luxor, price $15,000. Private collector, discreet shipping.
Listing 2: Souvenir Greek Parthenon statue, made of lightweight resin, perfect for aquarium decor, price $25.
Listing 3: Vintage graphic T-shirt with Mayan calendar print, size L black, 100% cotton, price $18.
Listing 4: Ancient Roman bronze Gladius sword, 1st century AD, battle ready with rust marks, uncleaned, asking price £25,000. Location secret.
Listing 5: Hand-carved replica of Aztec calendar stone for garden decoration, newly made last month, price $1,200.
"""

print("Mulai menganalisis data dengan Gemini AI...")

# ==============================================================================
# 3. PROMPT ENGINEERING (Global Context)
# ==============================================================================
prompt = f"""
You are a forensic expert specializing in global illicit artifact trafficking.
Analyze these listings:
{raw_scraped_data}

Classify each:
1. "Authentic (Suspected)" - High risk.
2. "Replica" - Low risk.
3. "Irrelevant" - Zero risk.

Output ONLY a JSON Array:
[
  {{
    "item_name": "string",
    "price_usd": number,
    "status": "string",
    "risk_score": 1-10,
    "reason": "string"
  }}
]
"""

# ==============================================================================
# 4. EKSEKUSI AI & PENYIMPANAN DATA
# ==============================================================================
try:
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    analyzed_data = json.loads(response.text)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(analyzed_data, f, indent=4, ensure_ascii=False)
        
    save_history()
    print("✅ Berhasil: Data dan history telah diperbarui.")

except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")
    exit(1)
