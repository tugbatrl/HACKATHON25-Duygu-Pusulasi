import google.generativeai as genai
import os
from dotenv import load_dotenv

# Ortam değişkenlerini yükle (eğer .env dosyası kullanıyorsan)
load_dotenv()

# API anahtarını al
API_KEY = os.environ.get("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY bulunamadı. Lütfen .env dosyasına ekleyin.")

# Gemini yapılandırması
genai.configure(api_key=API_KEY)

# Modeli yükle
model = genai.GenerativeModel(model_name="models/gemini-1.0-pro")


# Test prompt'u
prompt = "Merhaba! Bu bir API bağlantı testidir. Lütfen bunu onaylayan kısa bir mesaj yaz."

try:
    response = model.generate_content(prompt)
    print("✅ AI yanıtı başarıyla alındı:")
    print("--------------------------------------------------")
    print(response.text.strip())
    print("--------------------------------------------------")
except Exception as e:
    print("❌ HATA! AI yanıtı alınamadı.")
    print("Hata detayı:", e)
