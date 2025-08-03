from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import google.generativeai as genai
import os
import secrets
import json
from datetime import datetime, timedelta
import threading
from dotenv import load_dotenv
load_dotenv()


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
            return {"users": {}, "reports": {}, "student_progress": {}, "next_user_id": 1, "next_report_id": 1}

def save_data(data):
   
    with file_lock:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

# Google AI API'yi yapılandır
try:
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY ortam değişkeni eksik.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")
except (KeyError, ValueError) as e:
    raise RuntimeError(f"API yapılandırma hatası: {e}")

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

# --- Rota Tanımlamaları ---

@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('game_page' if session.get('user_type') == 'ogrenci' else 'teacher_panel'))
    return render_template('index.html')

@app.route('/student')
def student_login_page():
    return render_template('student.html')

@app.route('/teacher')
def teacher_login_page():
    return render_template('teacher.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    return handle_login('ogrenci')

@app.route('/teacher_login', methods=['POST'])
def teacher_login():
    return handle_login('ogretmen')

def handle_login(user_type):
    """Öğrenci ve öğretmen girişi için ortak işlev."""
    form_data = request.form
    name = form_data.get('name', '').strip()
    surname = form_data.get('surname', '').strip()

    if user_type == 'ogrenci':
        identifier = 'grade'
        identifier_value = form_data.get('grade', '').strip()
    else:  # ogretmen
        identifier = 'class_name'
        identifier_value = form_data.get('class_name', '').strip()

    if not all([name, surname, identifier_value]):
        error_message = "Lütfen tüm alanları doldurunuz."
        return render_template(f'{user_type}.html', error=error_message)

    data = load_data()
    user_id = None
    
    
    for uid, user_info in data["users"].items():
        if user_info["name"] == name and user_info["surname"] == surname and user_info["user_type"] == user_type:
            user_id = uid
            user_info[identifier] = identifier_value
            break

    
    if not user_id:
        user_id = data["next_user_id"]
        data["users"][str(user_id)] = {
            "name": name,
            "surname": surname,
            "user_type": user_type,
            identifier: identifier_value
        }
        data["next_user_id"] += 1

    save_data(data)

    session.permanent = True
    session['user_id'] = str(user_id)
    session['user_type'] = user_type
    session['name'] = name
    session['surname'] = surname
    session[identifier] = identifier_value

    if user_type == 'ogrenci':
        return redirect(url_for('game_page'))
    else:
        return redirect(url_for('teacher_panel'))

@app.route('/game')
def game_page():
    if session.get('user_type') != 'ogrenci':
        return redirect(url_for('index'))
    return render_template('game.html')

@app.route('/api/student-info')
def student_info():
    if session.get('user_type') != 'ogrenci':
        return jsonify({"success": False, "error": "Unauthorized access"}), 403
    
    return jsonify({
        "success": True,
        "name": session.get('name', ''),
        "surname": session.get('surname', ''),
        "grade": session.get('grade', '')
    })

@app.route('/api/scenarios')
def get_scenarios():
    if session.get('user_type') != 'ogrenci':
        return jsonify({"error": "Unauthorized access"}), 403
    
    return jsonify(scenarios)

@app.route('/api/student-progress')
def get_student_progress():
    if session.get('user_type') != 'ogrenci':
        return jsonify({"error": "Unauthorized access"}), 403
    
    data = load_data()
    user_id = session.get('user_id')
    db_progress = data.get("student_progress", {}).get(user_id, {})
    
    # Veritabanından ilerlemeyi al, yoksa boş sözlük döndür
    current_progress = db_progress.get("answers", {})
    current_step = db_progress.get("current_step", "step1")
    
    return jsonify({
        "progress": current_progress,
        "current_step": current_step,
        "completed_steps": len(current_progress)
    })

@app.route('/save-answer', methods=['POST'])
def save_answer():
    if session.get('user_type') != 'ogrenci':
        return jsonify({"status": "error", "message": "Unauthorized access"}), 403

    answer_data = request.get_json()
    answer = answer_data.get('answer')
    step = answer_data.get('step')

    if not answer or not step:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    expected_steps = list(scenarios.keys())
    
    if step not in expected_steps:
        return jsonify({"status": "error", "message": "Invalid step"}), 400

    data = load_data()
    user_id = session.get('user_id')
    
    # İlerleme veritabanında yoksa oluştur
    if user_id not in data.get("student_progress", {}):
        data["student_progress"][user_id] = {"answers": {}}
    
    # Adımları sırayla kontrol et
    current_progress = data["student_progress"][user_id].get("answers", {})
    current_step_db = data["student_progress"][user_id].get("current_step", "step1")
    
    if step != current_step_db:
        # Öğrencinin bir önceki adımı tamamlamasını bekle
        if expected_steps.index(step) > expected_steps.index(current_step_db):
            next_expected_step_index = expected_steps.index(current_step_db) + 1
            if next_expected_step_index < len(expected_steps) and step == expected_steps[next_expected_step_index]:
                # Doğru sıradaki adım
                pass
            else:
                return jsonify({"status": "error", "message": "You must follow the steps in order."}), 400
        elif step != 'step1': # İlk adımı her zaman kabul et
            return jsonify({"status": "error", "message": "This step has already been completed."}), 400

    data["student_progress"][user_id]["answers"][step] = answer
    
    # Bir sonraki adımı belirle
    next_step_index = expected_steps.index(step) + 1
    next_step = expected_steps[next_step_index] if next_step_index < len(expected_steps) else "end"
    data["student_progress"][user_id]["current_step"] = next_step

    data["student_progress"][user_id]["last_updated"] = datetime.utcnow().isoformat()
    save_data(data)

    return jsonify({"status": "success", "next_step": next_step})

@app.route('/generate-report', methods=['POST'])
def generate_report():
    if session.get('user_type') != 'ogrenci':
        return jsonify({"status": "error", "message": "Unauthorized access"}), 403

    try:
        data = request.get_json()
        progress = data.get('progress', {})
        
        if len(progress) != len(scenarios):
            return jsonify({"status": "error", "message": "All scenarios must be completed before generating a report."}), 400

        # Cevapları sıralı olarak al
        sorted_answers = [progress.get(f"step{i+1}") for i in range(len(scenarios))]
        
        # Gelişmiş prompt ile rapor oluştur
        prompt = create_report_prompt(session['name'], session['surname'], session.get('grade', ''), sorted_answers)
        
        report_text = ""
        try:
            response = model.generate_content(prompt)
            if response and hasattr(response, 'text') and response.text:
                report_text = response.text.strip()
            else:
                raise Exception("AI response was empty or invalid.")
        except Exception as ai_error:
            print(f"AI error: {ai_error}")
            report_text = create_fallback_report(session['name'], session['surname'], sorted_answers)

        # Raporu veritabanına kaydet
        db_data = load_data()
        report_id = db_data["next_report_id"]
        db_data["reports"][str(report_id)] = {
            "student_id": session['user_id'],
            "student_name": session['name'],
            "student_surname": session['surname'],
            "student_grade": session.get('grade', ''),
            "answers": progress,
            "report_text": report_text,
            "timestamp": datetime.utcnow().isoformat()
        }
        db_data["next_report_id"] += 1
        save_data(db_data)

        # Öğrencinin ilerlemesini veritabanından ve oturumdan temizle
        if session.get('user_id') in db_data.get('student_progress', {}):
            del db_data['student_progress'][session['user_id']]
            save_data(db_data)
        
        session.pop('student_progress', None)
        session.pop('current_step', None)

        return jsonify({"status": "success", "report_id": report_id, "report_text": report_text})
    except Exception as e:
        print(f"Error during report generation: {e}")
        return jsonify({"status": "error", "message": "An error occurred while generating the report."}), 500

# --- Öğretmen Paneli Rotaları ---

@app.route('/teacher-panel')
def teacher_panel():
    if session.get('user_type') != 'ogretmen':
        return redirect(url_for('index'))
    return render_template('teacher-panel.html')

@app.route('/api/teacher-info')
def teacher_info():
    if session.get('user_type') != 'ogretmen':
        return jsonify({"success": False, "error": "Unauthorized access"}), 403
    return jsonify({
        "success": True,
        "name": session.get('name', ''),
        "surname": session.get('surname', ''),
        "class_name": session.get('class_name', '')
    })

@app.route('/api/class-stats')
def class_stats():
    if session.get('user_type') != 'ogretmen':
        return jsonify({"error": "Unauthorized access"}), 403
    
    data = load_data()
    teacher_class = session.get('class_name', '')
    class_reports = [r for r in data.get("reports", {}).values() if r.get('student_grade') == teacher_class]
    
    today = datetime.now().date()
    today_reports = sum(1 for r in class_reports if datetime.fromisoformat(r['timestamp']).date() == today)
    
    total_students = len(set([r['student_id'] for r in class_reports]))
    
    stats = {
        "total_students": total_students,
        "total_reports": len(class_reports),
        "today_reports": today_reports,
        "avg_score": 85
    }
    
    return jsonify(stats)

@app.route('/reports')
def reports_page():
    if session.get('user_type') != 'ogretmen':
        return redirect(url_for('index'))
    return render_template('reports.html')

@app.route('/api/class-reports')
def class_reports():
    if session.get('user_type') != 'ogretmen':
        return jsonify({"error": "Unauthorized access"}), 403
    
    data = load_data()
    teacher_class = session.get('class_name', '')
    class_reports = []
    
    for report_id, report in data.get("reports", {}).items():
        if report.get('student_grade') == teacher_class:
            formatted_report = {
                "report_id": report_id,
                "student_name": report.get('student_name', ''),
                "student_surname": report.get('student_surname', ''),
                "ai_report": report.get('report_text', ''),
                "created_at": datetime.fromisoformat(report.get('timestamp', datetime.utcnow().isoformat())).strftime('%Y-%m-%d %H:%M'),
                "answers": []
            }
            answers = report.get('answers', {})
            for step, answer_key in answers.items():
                step_num = step.replace('step', '')
                choice_value = scenarios.get(step, {}).get('options', {}).get(answer_key, answer_key)
                formatted_report["answers"].append({
                    "step": step_num,
                    "choice": answer_key,
                    "choice_value": choice_value
                })
            class_reports.append(formatted_report)
    
    return jsonify({"reports": class_reports})

@app.route('/report/<report_id>')
def view_report(report_id):
    if session.get('user_type') != 'ogretmen':
        return redirect(url_for('index'))
    
    data = load_data()
    report_data = data["reports"].get(report_id)

    if not report_data or report_data.get('student_grade') != session.get('class_name'):
        return "Report not found or unauthorized access", 404
    
    return render_template('report_view.html', report=report_data, scenarios=scenarios)

@app.route('/class-analysis')
def class_analysis():
    if session.get('user_type') != 'ogretmen':
        return redirect(url_for('index'))
    
    data = load_data()
    teacher_class = session.get('class_name', '')
    class_reports = [r for r in data.get("reports", {}).values() if r.get('student_grade') == teacher_class]
    
    analysis_data = {
        "total_students": len(set([r['student_id'] for r in class_reports])),
        "total_reports": len(class_reports),
        "reports": class_reports
    }
    
    return render_template('class_analysis.html', analysis=analysis_data)

@app.route('/progress-tracking')
def progress_tracking():
    if session.get('user_type') != 'ogretmen':
        return redirect(url_for('index'))
    return render_template('progress_tracking.html')

@app.route('/game-management')
def game_management():
    if session.get('user_type') != 'ogretmen':
        return redirect(url_for('index'))
    return render_template('game_management.html', scenarios=scenarios)

@app.route('/homework-assignment')
def homework_assignment():
    if session.get('user_type') != 'ogretmen':
        return redirect(url_for('index'))
    return render_template('homework_assignment.html')

@app.route('/notifications')
def notifications():
    if session.get('user_type') != 'ogretmen':
        return redirect(url_for('index'))
    return render_template('notifications.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- AI Prompt ve Fallback Fonksiyonları ---

def create_report_prompt(name, surname, student_grade, student_answers):
    """Gemini modeline gönderilecek ayrıntılı ve yapılandırılmış prompt'u oluşturur."""
    prompt = f"""
    Öğrenci Adı Soyadı: {name} {surname}
    Sınıf: {student_grade}

    Aşağıda, bir öğrencinin sosyal ve duygusal becerilerini değerlendirmek amacıyla tasarlanmış dört farklı senaryoya verdiği cevaplar yer almaktadır. Senaryolar ve öğrencinin tercihleri şu şekildedir:

    ---
    1. Senaryo:
    Soru: 'Sabah uyandın... Annen 'Gerek yok, sen de artık büyüdün' der. Ne yaparsın?'
    Öğrencinin Cevabı: {student_answers[0]} - {scenarios['step1']['options'].get(student_answers[0], '')}

    2. Senaryo:
    Soru: 'Sınıfa yeni bir öğrenci girdi, adı Ali. Biraz çekingen duruyor... Ece sana 'Hadi teneffüste bahçeye çıkalım' der. Ne yaparsın?'
    Öğrencinin Cevabı: {student_answers[1]} - {scenarios['step2']['options'].get(student_answers[1], '')}

    3. Senaryo:
    Soru: 'Öğle arası... Sınıfın zorba çocuğu Can, yanına geldi... Ne yaparsın?'
    Öğrencinin Cevabı: {student_answers[2]} - {scenarios['step3']['options'].get(student_answers[2], '')}
    
    4. Senaryo:
    Soru: 'Zil çaldı... Can ve arkadaşları, artık seninle değil, Ali ile uğraşmaya başladı... Ece, 'Sence öğretmene söylemeli miyiz?' diye sordu. Ne yaparsın?'
    Öğrencinin Cevabı: {student_answers[3]} - {scenarios['step4']['options'].get(student_answers[3], '')}
    ---
    
    Bu cevaplara dayanarak, öğrencinin sosyal ve duygusal gelişimini profesyonel bir eğitimci gibi analiz eden, aşağıdaki bölümlerden oluşan bir rapor oluştur. Rapor Türkçe olmalı, net ve anlaşılır bir dil kullanmalı ve pedagojik yaklaşımla yazılmalıdır.

    Rapor, aşağıdaki başlıkları içermelidir:

    ### Öğrenci Gelişim Özeti
    (Öğrencinin genel olarak sergilediği tutum ve davranışların kısa bir özeti. Örneğin, "Öğrenci genel olarak empati kurma ve problem çözme eğiliminde..." gibi.)

    ### Senaryo Bazlı Değerlendirme
    (Her bir senaryo için ayrı ayrı, öğrencinin seçtiği cevabın altında yatan olumlu ve olumsuz yönlerin analizi. Bu bölüm her senaryo için bir paragraf uzunluğunda olmalı.
    - Senaryo 1: Sosyal Sorumluluk ve Aile Bağları
    - Senaryo 2: Empati ve Kapsayıcılık
    - Senaryo 3: Özgüven ve Zorbalığa Karşı Durma
    - Senaryo 4: Ahlaki Gelişim ve Yardım Etme

    ### Güçlü Yönler
    (Öğrencinin sergilediği pozitif özelliklerin bir listesi veya paragrafı. Örneğin, 'Empati', 'Problem çözme becerisi', 'Liderlik potansiyeli' gibi.)

    ### Geliştirilmesi Gereken Alanlar
    (Öğrencinin daha fazla desteklenmesi gereken alanların bir listesi veya paragrafı. Örneğin, 'Duygusal tepkilerini yönetme', 'Risk alma cesareti' gibi.)

    ### Öneriler
    (Öğrencinin gelişimine katkı sağlamak için öğretmenlere ve velilere yönelik 3-4 maddelik somut ve uygulanabilir öneriler. Örnek olarak: 'Empati oyunları oynatılması', 'Sınıfta grup çalışmaları yapılması' gibi.)
    
    Raporun uzunluğu 300-500 kelime arasında olmalı, öğrenciyi yargılamaktan kaçınmalı ve yapıcı bir dil kullanmalıdır.
    """
    return prompt

def create_fallback_report(name, surname, student_answers):
    """AI çalışmadığında kullanılacak fallback raporu, daha detaylı hale getirildi."""
    report = f"### Öğrenci Gelişim Özeti (Otomatik Rapor)\n\n"
    
    empathy_count = 0
    confidence_count = 0
    problem_solving_count = 0
    
    analysis_points = []
    
    # 1. Senaryo
    if student_answers[0] == 'C':
        analysis_points.append("- Aile içinde sorumluluk alma ve yardım etme bilinci gösteriyor.")
    
    # 2. Senaryo
    if student_answers[1] == 'A' or student_answers[1] == 'C':
        analysis_points.append("- Empati kurma ve yeni bir öğrenciyi kapsama konusunda pozitif bir yaklaşım sergiliyor.")
        empathy_count += 1
    
    # 3. Senaryo
    if student_answers[2] == 'A':
        analysis_points.append("- Zorbalığa karşı durma ve özgüvenli bir tavır sergileme potansiyeli gösteriyor.")
        confidence_count += 1
    elif student_answers[2] == 'B':
        analysis_points.append("- Zorbalık karşısında pasif bir tepki veriyor. Bu durum, özgüven üzerinde çalışılması gerektiğini gösterir.")

    # 4. Senaryo
    if student_answers[3] == 'A':
        analysis_points.append("- Doğru zamanda yardım isteme ve sorunları yetkili birine bildirme sorumluluğu taşıyor.")
        problem_solving_count += 1
    elif student_answers[3] == 'C':
        analysis_points.append("- Sorunları kendi başına çözmeye çalışma eğilimi var. Bu durum, yardımlaşmanın önemini anlamak için destek gerektirebilir.")

    report += "Bu rapor, yapay zeka modelinin geçici olarak kullanılamaması nedeniyle temel bir değerlendirme içermektedir.\n\n"
    
    report += "Bu öğrencinin cevapları incelendiğinde:\n"
    report += "\n".join(analysis_points)
    report += f"\n\n**Güçlü Yönler:**\n- Empati kurma\n- Problem çözme becerisi\n- Sosyal sorumluluk\n\n"
    report += "**Geliştirilmesi Gereken Alanlar:**\n- Durumsal farkındalık ve doğru tepki verme\n- Zorbalık karşısında daha proaktif olma\n\n"
    
    report += "**Öneriler:**\n- Öğrenciye empati ve sosyal sorumluluk konularında destekleyici hikayeler okutulabilir.\n- Zorbalık durumunda doğru iletişim kurma ve yardım isteme becerileri öğretilmelidir."
    
    return report


if __name__ == '__main__':
    app.run(debug=True)