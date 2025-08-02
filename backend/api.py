from flask import Flask, request, jsonify, render_template, redirect, url_for, session, abort
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import timedelta
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=14)
CORS(app)


try:
    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
    model = genai.GenerativeModel('gemini-pro')
except KeyError:
    raise RuntimeError("GOOGLE_API_KEY environment variable missing")

@app.route("/")
def index():
    if 'isim' in session:
        return redirect(url_for('scenerio'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    isim = request.form.get('isim', '').strip()
    soyad = request.form.get('soyad', '').strip()
    
    if not isim or not soyad:
        return redirect(url_for('index'))
    
    session.permanent = True
    session['isim'] = isim
    session['soyad'] = soyad
    session['cevaplar'] = []
    return redirect(url_for('scenerio'))

@app.route('/scenerio')
def scenerio():
    if 'isim' not in session:
        return redirect(url_for('index'))
    return render_template('scenerio.html', isim=session['isim'], soyad=session['soyad'])

@app.route('/save_answer', methods=['POST'])
def save_answer():
    if not request.is_json:
        abort(400)
    
    data = request.get_json()
    if 'answer' not in data:
        abort(400)
    
    if 'cevaplar' not in session:
        session['cevaplar'] = []
    
    session['cevaplar'].append(data['answer'])
    session.modified = True
    
    return jsonify({'status': 'success'})

@app.route('/generate_report')
def generate_report():
    if 'cevaplar' not in session or len(session['cevaplar']) != 4:
        return redirect(url_for('scenerio'))

    
    scenarios = {
        "step1": {
            "question": "Sabah uyandın. Yeni bir okul yılı başlıyor ve en iyi arkadaşın Ece ile buluşmak için sabırsızlanıyorsun. Kahvaltını yapıp hazırlanırken, annenin sana yardım etmek isteyip istemediğini sorarsın. Annen 'Gerek yok, sen de artık büyüdün' der. Ne yaparsın?",
            "options": {
                "A": "\"Peki o zaman\" deyip hemen yola çıkarsın.",
                "B": "\"Belki bir dahaki sefere\" diyerek gülümser ve yola çıkarsın.",
                "C": "\"O zaman kahvaltı masasındaki bardakları toplayayım\" der ve annene yardım edersin."
            }
        },
        "step2": {
            "question": "Okul servisiyle okula geldin ve Ece'yle buluştun. Sınıfa girdiğinizde, en arka sıraya oturdunuz. O sırada sınıfa yeni bir öğrenci girdi. Adı Ali. Biraz çekingen duruyor ve kimseyle konuşmuyor. Öğretmen, Ali'yi tek başına bir sıraya oturttu. Ali'nin yalnız olduğunu görüyorsun. Ece sana 'Hadi teneffüste bahçeye çıkalım' der. Ne yaparsın?",
            "options": {
                "A": "\"Önce şu yeni çocukla tanışalım\" der ve Ali'ye gülümsersin.",
                "B": "Ece'yle beraber bahçeye çıkarsınız, Ali'yi kendi haline bırakırsınız.",
                "C": "Öğretmene gidip \"Ali'nin yanına oturabilir miyim?\" diye sorarsın."
            }
        },
        "step3": {
            "question": "Öğle arası oldu ve sen sıranın başında Ece'yi kantinden bekliyorsun. O sırada sınıfın zorba çocuğu Can, yanına geldi. 'Ne kadar da komik bir çanta, sen bunu nereden buldun?' dedi. Sınıftaki birkaç kişi de ona güldü. Can, seninle alay ederken, Ece de kantinden geliyordu. Göz göze geldiniz. Ne yaparsın?",
            "options": {
                "A": "\"Bunun komik bir yanı yok, kimsenin eşyasıyla dalga geçemezsin\" der ve Can'a karşı durursun.",
                "B": "Can'ı duymazdan gelir, yere düşen kitaplarını toplar ve ağlamaklı bir şekilde Ece'ye sarılırsın.",
                "C": "Can'a karşılık verir ve \"Senin çantan daha kötü\" diyerek tartışmaya girersin."
            }
        },
        "step4": {
            "question": "Zil çaldı ve sınıfa girdiniz. Can ve arkadaşları, artık seninle değil, Ali ile uğraşmaya başladı. Her teneffüs Ali'nin eşyalarını saklıyor, onunla alay ediyorlardı. Son derste, Ali'nin sıranın altında ağladığını gördün. Ece, 'Sence öğretmene söylemeli miyiz?' diye sordu. Ne yaparsın?",
            "options": {
                "A": "\"Kesinlikle! Birinin yardım etmesi gerekiyor\" der ve öğretmene gidersin.",
                "B": "\"Bize de zorbalık yapar diye korkuyorum\" der ve kararsız kalırsın.",
                "C": "Ali'nin yanına gidip onu teselli etmeye çalışır, sonra da durumu kendi aranızda çözmeye çalışırsınız."
            }
        }
    }

    
    prompt = f"Kullanıcının adı: {session['isim']} {session['soyad']}\n\n"
    prompt += "Aşağıda bir senaryo boyunca kullanıcının karşılaştığı durumlar ve verdiği kararlar yer alıyor. Her adım sosyal, duygusal ve etik kararlar içeriyor.\n"
    prompt += "Lütfen bu cevaplara göre kişilik analizi yap. Özellikle şu özelliklere odaklan:\n"
    prompt += "- Empati\n- Özgüven\n- Sosyal sorumluluk\n- Liderlik\n- Ahlaki tutarlılık\n\n"

    steps = ['step1', 'step2', 'step3', 'step4']
    for i, step in enumerate(steps):
        soru = scenarios[step]['question']
        secenek_kodu = session['cevaplar'][i]
        secenek_metni = scenarios[step]['options'].get(secenek_kodu, "Bilinmiyor")

        prompt += f"Adım {i+1}:\n"
        prompt += f"Soru: {soru}\n"
        prompt += f"Cevap: {secenek_kodu} - {secenek_metni}\n\n"

    prompt += "Yukarıdaki bilgiler doğrultusunda maksimum 500 kelime olacak şekilde kişilik raporu yaz."

    try:
        response = model.generate_content(prompt)
        return render_template('report.html', 
                                report=response.text,
                                isim=session['isim'],
                                soyad=session['soyad'])
    except Exception as e:
        return render_template('report.html',
                               report=f"Hata: {str(e)}",
                               isim=session['isim'],
                               soyad=session['soyad'])

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')