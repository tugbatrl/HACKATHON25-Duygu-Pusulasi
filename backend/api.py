from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import google.generativeai as genai
import os
import secrets
import json
from datetime import datetime, timedelta
import threading

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=14)
CORS(app)

DB_FILE = 'db.json'
file_lock = threading.Lock()

def load_data():
    with file_lock:
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"users": {}, "reports": {}, "student_progress": {}}

def save_data(data):
    with file_lock:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

scenarios = {
    "step1": {
        "question": "Sabah uyandın. Yeni bir okul yılı başlıyor ve en iyi arkadaşın Ece ile buluşmak için sabırsızlanıyorsun. Kahvaltını yapıp hazırlanırken, annenin sana yardım etmek isteyip istemediğini sorarsın. Annen 'Gerek yok, sen de artık büyüdün' der. Ne yaparsın?",
        "options": {
            "A": "Peki o zaman deyip hemen yola çıkarsın.",
            "B": "Belki bir dahaki sefere diyerek gülümser ve yola çıkarsın.",
            "C": "O zaman kahvaltı masasındaki bardakları toplayayım der ve annene yardım edersin."
        }
    },
    "step2": {
        "question": "Okul servisiyle okula geldin ve Ece'yle buluştun. Sınıfa girdiğinizde, en arka sıraya oturdunuz. O sırada sınıfa yeni bir öğrenci girdi. Adı Ali. Biraz çekingen duruyor ve kimseyle konuşmuyor. Öğretmen, Ali'yi tek başına bir sıraya oturttu. Ali'nin yalnız olduğunu görüyorsun. Ece sana 'Hadi teneffüste bahçeye çıkalım' der. Ne yaparsın?",
        "options": {
            "A": "Önce şu yeni çocukla tanışalım der ve Ali'ye gülümsersin.",
            "B": "Ece'yle beraber bahçeye çıkarsınız, Ali'yi kendi haline bırakırsınız.",
            "C": "Öğretmene gidip Ali'nin yanına oturabilir miyim? diye sorarsın."
        }
    },
    "step3": {
        "question": "Öğle arası oldu ve sen sıranın başında Ece'yi kantinden bekliyorsun. O sırada sınıfın zorba çocuğu Can, yanına geldi. 'Ne kadar da komik bir çanta, sen bunu nereden buldun?' dedi. Sınıftaki birkaç kişi de ona güldü. Can, seninle alay ederken, Ece de kantinden geliyordu. Göz göze geldiniz. Ne yaparsın?",
        "options": {
            "A": "Bunun komik bir yanı yok, kimsenin eşyasıyla dalga geçemezsin der ve Can'a karşı durursun.",
            "B": "Can'ı duymazdan gelir, yere düşen kitaplarını toplar ve ağlamaklı bir şekilde Ece'ye sarılırsın.",
            "C": "Can'a karşılık verir ve Senin çantan daha kötü diyerek tartışmaya girersin."
        }
    },
    "step4": {
        "question": "Zil çaldı ve sınıfa girdiniz. Can ve arkadaşları, artık seninle değil, Ali ile uğraşmaya başladı. Her teneffüs Ali'nin eşyalarını saklıyor, onunla alay ediyorlardı. Son derste, Ali'nin sıranın altında ağladığını gördün. Ece, 'Sence öğretmene söylemeli miyiz?' diye sordu. Ne yaparsın?",
        "options": {
            "A": "Kesinlikle! Birinin yardım etmesi gerekiyor der ve öğretmene gidersin.",
            "B": "Bize de zorbalık yapar diye korkuyorum der ve kararsız kalırsın.",
            "C": "Ali'nin yanına gidip onu teselli etmeye çalışır, sonra da durumu kendi aranızda çözmeye çalışırsınız."
        }
    }
}

try:
    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
    model = genai.GenerativeModel('gemini-pro')
except KeyError:
    raise RuntimeError("GOOGLE_API_KEY ortam değişkeni eksik.")

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('arayuz.html')

@app.route('/login', methods=['POST'])
def login():
    isim = request.form.get('isim', '').strip()
    soyad = request.form.get('soyad', '').strip()
    kullanici_turu = request.form.get('kullanici_turu')
    sinif = request.form.get('sinif', '').strip() if kullanici_turu == 'ogrenci' else None

    if not isim or not soyad or not kullanici_turu:
        return redirect(url_for('index'))

    if kullanici_turu == 'ogrenci' and not sinif:
        return redirect(url_for('index'))

    data = load_data()
    user_id = f"{kullanici_turu}_{isim}_{soyad}"
    data["users"][user_id] = {
        "name": isim,
        "surname": soyad,
        "user_type": kullanici_turu,
        "class": sinif
    }
    save_data(data)

    session.permanent = True
    session['user_id'] = user_id
    session['user_type'] = kullanici_turu
    session['name'] = isim
    session['surname'] = soyad
    session['class'] = sinif

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    if session.get('user_type') == 'ogrenci':
        return redirect(url_for('student_scenario'))
    else:
        return redirect(url_for('teacher_dashboard'))

def get_student_progress(user_id):
    data = load_data()
    progress = data["student_progress"].get(user_id, {})
    answers = progress.get("answers", [])
    current_step = len(answers)
    return answers, current_step

@app.route('/student')
def student_scenario():
    if 'user_type' not in session or session['user_type'] != 'ogrenci':
        return redirect(url_for('index'))

    user_id = session['user_id']
    answers, current_step = get_student_progress(user_id)
    
    return render_template('student_scenario.html',
                           scenarios=scenarios,
                           name=session['name'],
                           surname=session['surname'],
                           sinif=session['class'],
                           current_step=current_step)

@app.route('/save_answer', methods=['POST'])
def save_answer():
    answer = request.json.get('answer')
    step_index = request.json.get('step_index')
    user_id = session.get('user_id')

    if not answer or not user_id or session.get('user_type') != 'ogrenci':
        return jsonify({"status": "error", "message": "Geçersiz istek"}), 400

    data = load_data()
    
    if user_id not in data["student_progress"]:
        data["student_progress"][user_id] = {"answers": []}

    if len(data["student_progress"][user_id]["answers"]) != step_index:
        return jsonify({"status": "error", "message": "Yanlış adım sırası"}), 400

    data["student_progress"][user_id]["answers"].append(answer)
    save_data(data)

    return jsonify({"status": "success"})

@app.route('/generate_report', methods=['POST'])
def generate_report():
    user_id = session.get('user_id')
    if session.get('user_type') != 'ogrenci' or not user_id:
        return jsonify({"status": "error", "message": "Yetkisiz erişim"}), 403

    answers, _ = get_student_progress(user_id)
    if len(answers) != len(scenarios):
        return jsonify({"status": "error", "message": "Tüm senaryolar yanıtlanmadı"}), 400

    prompt = create_report_prompt(session['name'], session['surname'], session['class'], answers)
    try:
        response = model.generate_content(prompt)
        report_text = response.text

        data = load_data()
        report_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        data["reports"][report_id] = {
            "student_id": user_id,
            "name": session['name'],
            "surname": session['surname'],
            "class": session['class'],
            "answers": answers,
            "report": report_text,
            "timestamp": datetime.now().isoformat()
        }
        
        if user_id in data["student_progress"]:
            del data["student_progress"][user_id]
            
        save_data(data)

        return jsonify({"status": "success", "report": report_text})

    except Exception as e:
        return jsonify({"status": "error", "message": f"Rapor oluşturulurken bir hata oluştu: {str(e)}"}), 500

def create_report_prompt(name, surname, student_class, student_answers):
    prompt = f"Kullanıcının adı: {name} {surname}\nSınıfı: {student_class}\n\n"
    prompt += "Aşağıda bir senaryo boyunca kullanıcının karşılaştığı durumlar ve verdiği kararlar yer alıyor. Her adım sosyal, duygusal ve etik kararlar içeriyor. Lütfen bu cevaplara göre öğrencinin kişiliğini analiz eden, en fazla 500 kelimelik bir rapor yazın. Analizde özellikle şu özelliklere odaklanın:\n"
    prompt += "- Empati: Başkalarının duygularını anlama ve paylaşma yeteneği.\n"
    prompt += "- Özgüven: Kendi kararlarından emin olma ve zorbalığa karşı durabilme.\n"
    prompt += "- Sosyal Sorumluluk: Çevresindeki sorunlara duyarlı olma ve harekete geçme isteği.\n"
    prompt += "- Liderlik: Bir grup içinde inisiyatif alıp yön gösterebilme.\n"
    prompt += "- Ahlaki Tutarlılık: Etik değerlere bağlı kalma ve farklı durumlarda benzer ilkelerle hareket etme.\n\n"
    
    steps = ['step1', 'step2', 'step3', 'step4']
    for i, step in enumerate(steps):
        try:
            soru = scenarios[step]['question']
            secenek_kodu = student_answers[i]
            secenek_metni = scenarios[step]['options'][secenek_kodu]
    
            prompt += f"Adım {i + 1}:\n"
            prompt += f"Soru: {soru}\n"
            prompt += f"Cevap: {secenek_kodu} - {secenek_metni}\n\n"
        except (IndexError, KeyError) as e:
            prompt += f"Adım {i + 1}: Hatalı veya eksik cevap. (Hata: {e})\n\n"

    prompt += "Yukarıdaki bilgiler doğrultusunda detaylı bir kişilik raporu yazın. Raporun yapısı, paragraf başlıkları ve madde işaretleri içerebilir."
    return prompt

@app.route('/teacher')
def teacher_dashboard():
    if 'user_type' not in session or session['user_type'] != 'ogretmen':
        return redirect(url_for('index'))
    
    data = load_data()
    grouped_reports = {}
    
    for report_id, report_data in data.get("reports", {}).items():
        sinif = report_data.get('class', 'Bilinmeyen Sınıf')
        if sinif not in grouped_reports:
            grouped_reports[sinif] = []
        
        report_data['report_id'] = report_id
        grouped_reports[sinif].append(report_data)
    
    sorted_classes = sorted(grouped_reports.keys())

    return render_template('teacher_dashboard.html',
                           grouped_reports=grouped_reports,
                           sorted_classes=sorted_classes,
                           name=session['name'],
                           surname=session['surname'])

@app.route('/report/<report_id>')
def view_report(report_id):
    if 'user_type' not in session or session['user_type'] != 'ogretmen':
        return redirect(url_for('index'))
    
    data = load_data()
    report_data = data["reports"].get(report_id)

    if not report_data:
        return "Rapor bulunamadı.", 404

    return render_template('report_view.html',
                           report=report_data,
                           scenarios=scenarios)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)