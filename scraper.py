import os
import json
import google.generativeai as genai
import hashlib
from datetime import datetime, timedelta

# ==============================================================================
# 0. SISTEM HISTORY & PENJADWALAN
# ==============================================================================
HISTORY_FILE = "history.json"
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

    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    # Syarat 2: Jika script python di-update (hash / sidik jari file berubah)
    current_hash = get_file_hash(SCRIPT_FILE)
    if history.get("script_hash") != current_hash:
        print("Status: Terdeteksi perubahan pada script Python. Melakukan crawl ulang.")
        return True

    # Syarat 3: Jika sudah 7 hari dari crawl terakhir
    last_crawl_str = history.get("last_crawl_date")
    if last_crawl_str:
        last_crawl_date = datetime.fromisoformat(last_crawl_str)
        if datetime.now() - last_crawl_date >= timedelta(days=7):
            print("Status: Sudah 1 minggu (7 hari) berlalu. Melakukan crawl berkala.")
            return True

    print("Status: Belum waktunya crawl dan tidak ada update script. Sistem istirahat.")
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
# Jika tidak memenuhi syarat untuk crawl, hentikan program dengan aman (exit 0)
# ------------------------------------------------------------------------------
if not should_crawl():
    exit(0)

# ==============================================================================
# 1. KONFIGURASI GEMINI AI
# ==============================================================================
# Mengambil API Key yang nanti akan kita simpan di rahasia GitHub (GitHub Secrets)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("⚠️ Peringatan: GEMINI_API_KEY belum di-set!")
    # Berhenti jika tidak ada API Key
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
# Menggunakan model flash karena cepat, murah, dan pintar untuk tugas JSON
model = genai.GenerativeModel('gemini-2.5-flash')

# ==============================================================================
# 2. SIMULASI CRAWLING DATA (Pengganti Web Scraper)
# ==============================================================================
# Catatan: Di dunia nyata, di sinilah Anda menggunakan 'requests' dan 'BeautifulSoup'.
# Namun, karena banyak marketplace memblokir scraper pemula, kita gunakan 
# data teks mentah simulasi ini agar Anda bisa melihat cara kerja AI-nya dulu.

raw_scraped_data = """
Listing 1: Authentic Egyptian Ushabti figure, Late Period faience, recently unearthed in Luxor, price $15,000. Private collector, discreet shipping.
Listing 2: Souvenir Greek Parthenon statue, made of lightweight resin, perfect for aquarium decor, price $25.
Listing 3: Vintage graphic T-shirt with Mayan calendar print, size L black, 100% cotton, price $18.
Listing 4: Ancient Roman bronze Gladius sword, 1st century AD, battle ready with rust marks, uncleaned, asking price £25,000. Location secret.
Listing 5: Hand-carved replica of Aztec calendar stone for garden decoration, newly made last month, price $1,200.
"""

print("Mulai menganalisis data dengan Gemini AI...")

# ==============================================================================
# 3. PROMPT ENGINEERING (Instruksi untuk AI)
# ==============================================================================
prompt = f"""
You are a forensic expert and detective specializing in ancient artifacts and cultural heritage.
Your task is to monitor the illicit trafficking of cultural property based on raw scraped data from global marketplaces.

Analyze the following marketplace listings:
{raw_scraped_data}

Classify each item into one of the following statuses:
1. "Authentic (Suspected)" - Very high price (thousands/millions), suspicious keywords (unearthed, uncleaned, private collector, location secret). High Risk.
2. "Replica" - Reasonable/low price, clearly mentions modern materials (resin, 3D printed, newly made, souvenir). Low Risk.
3. "Irrelevant" - The item has nothing to do with actual artifacts (e.g., t-shirts, books, food). Zero Risk.

Provide the output ONLY in a JSON Array format without any prefix or suffix. Use this exact structure:
[
  {{
    "item_name": "Name of the product sold",
    "price_usd": numeric_value_in_usd_without_symbols,
    "status": "Authentic (Suspected) / Replica / Irrelevant",
    "risk_score": integer from 1 to 10 (10 = highly suspicious/illicit),
    "reason": "Logical explanation in max 2 sentences why it received this status and score."
  }}
]
"""

# ==============================================================================
# 4. EKSEKUSI AI & PENYIMPANAN DATA
# ==============================================================================
try:
    # Meminta Gemini merespon dalam format baku JSON
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    # Mengubah teks dari Gemini menjadi objek Python
    analyzed_data = json.loads(response.text)
    
    # Menyimpan hasil ke file data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(analyzed_data, f, indent=4, ensure_ascii=False)
        
    print("✅ Berhasil! Data telah dianalisis AI dan disimpan ke data.json")
    print(json.dumps(analyzed_data, indent=2))

    # 5. SIMPAN HISTORY SETELAH SEMUA PROSES BERHASIL
    save_history()
    print("✅ History eksekusi berhasil diperbarui!")

except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")
