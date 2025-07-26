from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Ortam değişkenlerini yükle (.env dosyasından)
load_dotenv()

# Flask uygulaması
app = Flask(__name__)
CORS(app)

# Kullanıcı verilerini geçici olarak saklayacağımız global liste
collected_data = []

# Güvenli şekilde API anahtarını al
API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini modelini ayarla
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Senaryo adımları
SCENARIO = {
    "step1": {
        "text": """Sabah uyandın. Yeni bir okul yılı başlıyor ve...""",
        "options": [
            {"text": "\"Peki o zaman\" deyip hemen yola çıkarsın.", "value": "A"},
            {"text": "\"Belki bir dahaki sefere\" diyerek gülümser ve yola çıkarsın.", "value": "B"},
            {"text": "\"O zaman kahvaltı masasındaki bardakları toplayayım\" der ve annene yardım edersin.", "value": "C"}
        ],
        "next_step": "step2"
    },
    "step2": {
        "text": """Okul servisiyle okula geldin ve Ece'yle buluştun...""",
        "options": [
            {"text": "\"Önce şu yeni çocukla tanışalım\" der ve Ali'ye gülümsersin.", "value": "A"},
            {"text": "Ece'yle beraber bahçeye çıkarsınız, Ali'yi kendi haline bırakırsınız.", "value": "B"},
            {"text": "Öğretmene gidip \"Ali'nin yanına oturabilir miyim?\" diye sorarsın.", "value": "C"}
        ],
        "next_step": "step3"
    },
    "step3": {
        "text": """Öğle arası oldu ve sen sıranın başında Ece'yi kantinden bekliyorsun...""",
        "options": [
            {"text": "\"Bunun komik bir yanı yok...\" der ve Can'a karşı durursun.", "value": "A"},
            {"text": "Can'ı duymazdan gelir... Ece’ye sarılırsın.", "value": "B"},
            {"text": "Can'a karşılık verir ve \"Senin çantan daha kötü\" diyerek tartışmaya girersin.", "value": "C"}
        ],
        "next_step": "step4"
    },
    "step4": {
        "text": """Zil çaldı ve sınıfa girdiniz. Can ve arkadaşları Ali ile uğraşmaya başladı...""",
        "options": [
            {"text": "\"Kesinlikle! Birinin yardım etmesi gerekiyor\" der ve öğretmene gidersin.", "value": "A"},
            {"text": "\"Bize de zorbalık yapar diye korkuyorum\" der ve kararsız kalırsın.", "value": "B"},
            {"text": "Ali'nin yanına gidip onu teselli etmeye çalışırsın.", "value": "C"}
        ],
        "next_step": "end"
    },
    "end": {
        "text": "Senaryo tamamlandı! Şimdi raporunuzu oluşturuyoruz...",
        "options": [],
        "next_step": "report"
    }
}

# Prompt oluşturma
def create_ai_prompt(collected_data):
    prompt_parts = [
        "Aşağıdaki senaryoda 9-12 yaşındaki bir çocuğun verdiği yanıtlar var.",
        "Her yanıt, çocuğun sosyal becerileri ve duygusal zekasını yansıtır.",
        "Senaryo ve cevaplar:"
    ]
    
    for item in collected_data:
        step_text = SCENARIO.get(item['step'], {}).get('text', 'Adım metni yok')
        choice_text = ""
        for option in SCENARIO.get(item['step'], {}).get('options', []):
            if option['value'] == item['choice_value']:
                choice_text = option['text']
                break
        prompt_parts.append(f"- Adım: \"{step_text[:100]}...\"")
        prompt_parts.append(f"  Seçim ({item['choice_value']}): \"{choice_text}\"")

    prompt_parts.append("Lütfen aşağıdaki maddelerle kısa, net ve pedagojik değer taşıyan bir rapor yaz:")
    prompt_parts.append("- Çocuğun güçlü yönleri")
    prompt_parts.append("- Geliştirilebilecek yönler")
    prompt_parts.append("Her maddeye olumlu olumsuz ve somut öneri ekle")
    prompt_parts.append("Raporu yalnızca Türkçe olarak döndür.")

    return "\n".join(prompt_parts)

@app.route('/')
def index():
    return render_template("arayuz.html")

@app.route('/next_step', methods=['POST'])
def next_step():
    global collected_data
    data = request.get_json()
    current_step_key = data.get('current_step')
    user_choice_value = data.get('choice')

    if current_step_key and user_choice_value:
        collected_data.append({
            "step": current_step_key,
            "choice_value": user_choice_value
        })
        print(f"Kaydedilen adım: {current_step_key} = {user_choice_value}")

    if current_step_key is None:
        next_step_key = 'step1'
    else:
        next_step_key = SCENARIO.get(current_step_key, {}).get('next_step', 'end')

    if next_step_key == 'report':
        try:
            prompt = create_ai_prompt(collected_data)
            print("Prompt:\n", prompt)
            response = model.generate_content(prompt)
            ai_report = response.text if response.text else "Rapor alınamadı."
            print("AI Raporu:\n", ai_report)

            collected_data = [] 
            return jsonify({
                "text": "Çocuğun sosyal-duygusal gelişim raporu:",
                "report": ai_report,
                "options": [],
                "next_step": "report_generated"
            })
        except Exception as e:
            print("AI hatası:", e)
            collected_data = []
            return jsonify({
                "text": "Rapor oluşturulurken bir hata oluştu.",
                "options": [],
                "next_step": "error"
            })

    return jsonify(SCENARIO.get(next_step_key))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
