from flask import Flask, request, jsonify
from flask_cors import CORS # flask_cors kütüphanesini içeri aktarıyoruz

app = Flask(__name__)
CORS(app) # CORS'u uygulamanıza dahil ediyoruz

# Kullanıcının tüm senaryo cevaplarını burada tutacağız.
# Bu liste, her senaryo adımında kullanıcının seçimini kaydedecek.
collected_data = []

SCENARIO = {
    "step1": {
        "text": """Sabah uyandın. Yeni bir okul yılı başlıyor ve en iyi arkadaşın Ece ile buluşmak için sabırsızlanıyorsun. Kahvaltını yapıp hazırlanırken, aklında Ece ile konuşacağınız konular var. Okul servisine binmeden önce, annenin sana yardım etmek isteyip istemediğini sorarsın. Annen "Gerek yok, sen de artık büyüdün" der. Ne yaparsın?""",
        "options": [
            {"text": "\"Peki o zaman\" deyip hemen yola çıkarsın.", "value": "A"},
            {"text": "\"Belki bir dahaki sefere\" diyerek gülümser ve yola çıkarsın.", "value": "B"},
            {"text": "\"O zaman kahvaltı masasındaki bardakları toplayayım\" der ve annene yardım edersin.", "value": "C"}
        ],
        "next_step": "step2"
    },
    "step2": {
        "text": """Okul servisiyle okula geldin ve Ece'yle buluştun. Sınıfa girdiğinizde, en arka sıraya oturdunuz. O sırada sınıfa yeni bir öğrenci girdi. Adı Ali. Biraz çekingen duruyor ve kimseyle konuşmuyor. Öğretmen, Ali'yi tek başına bir sıraya oturttu. Ali'nin yalnız olduğunu görüyorsun. Ece sana "Hadi teneffüste bahçeye çıkalım" der. Ne yaparsın?""",
        "options": [
            {"text": "\"Önce şu yeni çocukla tanışalım\" der ve Ali'ye gülümsersin.", "value": "A"},
            {"text": "Ece'yle beraber bahçeye çıkarsınız, Ali'yi kendi haline bırakırsınız.", "value": "B"},
            {"text": "Öğretmene gidip \"Ali'nin yanına oturabilir miyim?\" diye sorarsın.", "value": "C"}
        ],
        "next_step": "step3"
    },
    "step3": {
        "text": """Öğle arası oldu ve sen sıranın başında Ece'yi kantinden bekliyorsun. O sırada sınıfın zorba çocuğu Can, yanına geldi. "Ne kadar da komik bir çanta, sen bunu nereden buldun?" dedi. Sınıftaki birkaç kişi de ona güldü. Can, seninle alay ederken, Ece de kantinden geliyordu. Göz göze geldiniz. Ne yaparsın?""",
        "options": [
            {"text": "\"Bunun komik bir yanı yok, kimsenin eşyasıyla dalga geçemezsin\" der ve Can'a karşı durursun.", "value": "A"},
            {"text": "Can'ı duymazdan gelir, yere düşen kitaplarını toplar ve ağlamaklı bir şekilde Ece'ye sarılırsın.", "value": "B"},
            {"text": "Can'a karşılık verir ve \"Senin çantan daha kötü\" diyerek tartışmaya girersin.", "value": "C"}
        ],
        "next_step": "step4"
    },
    "step4": {
        "text": """Zil çaldı ve sınıfa girdiniz. Can ve arkadaşları, artık seninle değil, Ali ile uğraşmaya başladı. Her teneffüs Ali'nin eşyalarını saklıyor, onunla alay ediyorlardı. Son derste, Ali'nin sıranın altında ağladığını gördün. Ece, "Sence öğretmene söylemeli miyiz?" diye sordu. Ne yaparsın?""",
        "options": [
            {"text": "\"Kesinlikle! Birinin yardım etmesi gerekiyor\" der ve öğretmene gidersin.", "value": "A"},
            {"text": "\"Bize de zorbalık yapar diye korkuyorum\" der ve kararsız kalırsın.", "value": "B"},
            {"text": "Ali'nin yanına gidip onu teselli etmeye çalışır, sonra da durumu kendi aranızda çözmeye çalışırsınız.", "value": "C"}
        ],
        "next_step": "end"
    },
    "end": {
        "text": "Senaryo tamamlandı! Şimdi raporunu oluşturuyoruz...",
        "options": [],
        "next_step": "report" # Bu, senaryo bittiğinde rapor aşamasına geçeceğimizi belirtir.
    }
}

@app.route('/')
def index():
    # Bu rota, uygulamanın ana sayfasına gelen istekleri karşılar.
    # Şimdilik sadece bir karşılama mesajı döndürüyor.
    return "Merhaba, Duygu Pusulası'na hoş geldin!"


@app.route('/next_step', methods=['POST'])
def next_step():
    # Frontend'den gelen JSON verisini al.
    data = request.get_json()
    # Mevcut adımın anahtarını al (örn. "step1"). Frontend'den gelmiyorsa 'None' olur.
    current_step_key = data.get('current_step') 
    # Kullanıcının seçtiği seçeneğin değerini al (örn. "A").
    user_choice_value = data.get('choice') 

    # Kullanıcının seçimini collected_data listesine kaydet.
    # Sadece 'current_step_key' ve 'user_choice_value' varsa kaydet (yani ilk çağrı değilse).
    if current_step_key and user_choice_value:
        collected_data.append({
            "step": current_step_key,
            "choice_value": user_choice_value
        })
        # Konsola kaydettiğin veriyi yazdır (geliştirme ve test için faydalıdır).
        print(f"Collected data for {current_step_key}: {user_choice_value}")
        print(f"All collected data: {collected_data}")

    # Senaryonun bir sonraki adımını belirle.
    # Eğer current_step_key yoksa (yani frontend'den ilk çağrıysa), 'step1' ile başla.
    if current_step_key is None:
        next_step_key = 'step1'
    else:
        # SCENARIO sözlüğünden mevcut adımın 'next_step' değerini al.
        # Eğer 'next_step' anahtarı yoksa (ki bu senaryonun sonu anlamına gelir), varsayılan olarak 'end' kullan.
        next_step_key = SCENARIO.get(current_step_key, {}).get('next_step', 'end')
    
    # Eğer bir sonraki adım 'report' ise (yani senaryo bittiyse), rapor oluşturma aşamasına geç.
    if next_step_key == 'report':
        # Burada daha sonra YZ'ye rapor oluşturma isteği gönderme mantığı gelecek.
        # Şimdilik frontend'e raporun hazırlandığını belirten bir mesaj gönderiyoruz.
        return jsonify({
            "text": "Senaryo tamamlandı! Raporunuz hazırlanıyor...",
            "options": [], # Bu adımda seçenek olmayacak.
            "next_step": "report_generated" # Frontend'in raporun hazırlandığını anlaması için özel bir anahtar.
        })
    
    # Bir sonraki adımın verilerini (metin ve seçenekler) JSON olarak frontend'e gönder.
    # SCENARIO.get(next_step_key) ile ilgili adımın tüm verilerini alırız.
    return jsonify(SCENARIO.get(next_step_key))


if __name__ == '__main__':
    # Flask uygulamasını hata ayıklama modunda çalıştır.
    # Bu modda kodda değişiklik yaptığınızda sunucu otomatik olarak yeniden başlar.
    app.run(debug=True)
