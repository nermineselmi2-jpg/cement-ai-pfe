from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from config import Config
from models import db, User, SensorLog
from factory import plant_twin
from ai_model import ai_brain
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- تهيئة قاعدة البيانات ---
with app.app_context():
    db.create_all()
    print("Database Initialized Successfully!")


# --- 1. إنشاء الأدمن (للتجربة) ---
@app.route('/create_admin')
def create_admin():
    if User.query.filter_by(username='admin').first():
        return "Admin already exists!"
    hashed_pw = generate_password_hash('admin123')
    admin = User(username='admin', password=hashed_pw, role='admin')
    db.session.add(admin)
    db.session.commit()
    return "Admin created! Username: admin, Password: admin123"


# --- 2. صفحة تسجيل الدخول (Login) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    html = """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Login</title>
    <style>
        body { font-family: sans-serif; background: #2c3e50; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .box { background: white; padding: 40px; border-radius: 10px; text-align: center; }
        input { padding: 10px; width: 80%; margin: 10px 0; }
        button { padding: 10px; width: 85%; background: #e74c3c; color: white; border: none; }
    </style></head>
    <body>
        <div class="box"><h2>Cement AI Login</h2>
        <form method="post">
            Username: <input type="text" name="username" required><br><br>
            Password: <input type="password" name="password" required><br><br>
            <button type="submit">Login</button>
        </form>
        {% if error %}<p style="color:red">{{ error }}</p>{% endif %}
        </div>
    </body></html>
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect('/')
        else:
            return render_template_string(html, error="Wrong Username or Password!")

    return render_template_string(html)


# --- 3. تسجيل الخروج ---
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


# --- 4. الواجهة (Dashboard HTML) ---
html_dashboard = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Cement AI Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f4f4f9; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }
        .value { font-size: 32px; font-weight: bold; color: #2c3e50; }
        .history-box { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: center; border-bottom: 1px solid #ddd; }
        th { background-color: #34495e; color: white; }
        #safety-bar { background: #2ecc71; color: white; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; transition: 0.5s; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🏭 Cement AI - Digital Twin</h2>
        <div>
            <a href="/logout" style="color: white; text-decoration: none; margin-left: 15px;">Logout</a>
            <a href="/history_db" style="color: white; margin-left: 20px; text-decoration: none; background: #e67e22; padding: 5px 10px; border-radius: 4px;">📂 سجل قاعدة البيانات</a>
        </div>
    </div>

    <div id="safety-bar">🟢 منطقة آمنة: النظام يعمل بشكل طبيعي</div>

    <div class="grid">
        <div class="card"><h3>الحرارة</h3><div class="value" id="val-temp">--</div></div>
        <div class="card"><h3>الضغط</h3><div class="value" id="val-pressure">--</div></div>
        <div class="card"><h3>الطاقة</h3><div class="value" id="val-energy">--</div></div>
        <div class="card"><h3>الإنتاج</h3><div class="value" id="val-production">--</div></div>
        <div class="card" style="border: 2px solid #e67e22;"><h3>🔮 حرارة متوقعة (AI)</h3><div class="value" id="val-predicted-temp" style="color: #e67e22;">--</div></div>
        <div class="card">
            <h3>حالة المستودع (Inventory)</h3>
            <div class="value" id="val-stock">--</div>
            <div style="background:#eee; height:10px; border-radius:5px; margin-top:10px; overflow:hidden;">
                <div id="stock-bar" style="background:#3498db; width:0%; height:100%; transition: width 1s;"></div>
            </div>
            <small id="stock-text">0%</small>
        </div>
    </div>

    <div class="history-box">
        <h3>سجل القراءات المحفوظة</h3>
        <button class="btn-danger" onclick="clearHistory()" style="background:#e74c3c; color:white; border:none; padding:5px 10px; border-radius:4px;">مسح السجل</button>
        <table>
            <thead><tr><th>الوقت</th><th>الحرارة</th><th>الضغط</th><th>الطاقة</th><th>الإنتاج</th></tr></thead>
            <tbody id="history-table-body"></tbody>
        </table>
    </div>

    <div style="position: fixed; bottom: 20px; right: 20px;">
        <button onclick="askChatbot()" style="background: #3498db; color: white; border-radius: 50%; width: 60px; height: 60px; font-size: 24px; border: none; cursor: pointer;">💬</button>
    </div>

    <script>
        const STORAGE_KEY = 'cement_ai_logs';
        function saveToLocalStorage(data) {
            let history = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
            history.unshift(data);
            if (history.length > 50) history = history.slice(0, 50);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
            renderTable(history);
        }
        function renderTable(history) {
            const tbody = document.getElementById('history-table-body');
            tbody.innerHTML = '';
            history.slice(0, 20).forEach(row => {
                tbody.innerHTML += `<tr><td>${row.timestamp}</td><td>${row.temp}</td><td>${row.pressure}</td><td>${row.energy}</td><td>${row.production}</td></tr>`;
            });
        }
        function clearHistory() { if(confirm('مسح السجل؟')) { localStorage.removeItem(STORAGE_KEY); renderTable([]); } }
        function askChatbot() {
            let t = document.getElementById('val-temp').innerText;
            let msg = t == "--" ? "النظام لم يبدأ." : (t > 1480 ? "⚠️ حرارة مرتفعة! خفف الوقود." : (t < 1420 ? "❄️ حرارة منخفضة." : "✅ الوضع ممتاز."));
            alert("🤖 المساعد: " + msg);
        }
        async function fetchData() {
            try {
                const res = await fetch('/api/data');
                const d = await res.json();
                document.getElementById('val-temp').innerText = d.temp;
                document.getElementById('val-pressure').innerText = d.pressure;
                document.getElementById('val-energy').innerText = d.energy;
                document.getElementById('val-production').innerText = d.production;
                const pElem = document.getElementById('val-predicted-temp');
                pElem.innerText = d.predicted_temp ? d.predicted_temp : "جاري التعلم...";
                if(d.stock && d.capacity) {
                    document.getElementById('val-stock').innerText = d.stock + " / " + d.capacity;
                    let pct = (d.stock / d.capacity) * 100;
                    document.getElementById('stock-bar').style.width = pct + "%";
                    document.getElementById('stock-text').innerText = Math.round(pct) + "% ممتلئ";
                }
                const bar = document.getElementById('safety-bar');
                if (d.temp > 1490 || d.pressure > 29) { bar.style.background = "#c0392b"; bar.innerHTML = "🔴 خطر: إخلاء المنطقة!"; }
                else if (d.temp > 1460) { bar.style.background = "#f39c12"; bar.innerHTML = "🟠 تحذير: معدات الوقاية إلزامية"; }
                else { bar.style.background = "#2ecc71"; bar.innerHTML = "🟢 منطقة آمنة"; }
                saveToLocalStorage(d);
            } catch (e) { console.error(e); }
        }
        window.onload = function() { renderTable(JSON.parse(localStorage.getItem(STORAGE_KEY)) || []); fetchData(); setInterval(fetchData, 2000); };
    </script>
</body>
</html>
"""


# --- 5. الصفحة الرئيسية ---
@app.route('/')
@login_required
def home():
    return render_template_string(html_dashboard)


# --- 6. API (Backend Logic) ---
@app.route('/api/data')
def get_data():
    data = plant_twin.update_sensors()

    # AI Logic
    ai_brain.add_data(data['temp'], data['pressure'], data['energy'])
    predicted = ai_brain.predict_temp(data['pressure'], data['energy'])
    data['predicted_temp'] = round(predicted, 2) if predicted else None

    # Inventory Logic
    data['stock'] = round(plant_twin.current_stock, 2)
    data['capacity'] = plant_twin.warehouse_capacity

    # Maintenance Logic
    maint_msg, _ = ai_brain.predict_maintenance(data['temp'], data['pressure'])
    data['maintenance'] = maint_msg

    return jsonify(data)

    # --- حفظ البيانات في قاعدة البيانات (Logging) ---
    new_log = SensorLog(
        temperature=data['temp'],
        pressure=data['pressure'],
        energy=data['energy'],
        status='Normal'
    )
    db.session.add(new_log)
    db.session.commit()
    print(f"✅ Data Saved: Temp {data['temp']} at {data['timestamp']}")


# --- صفحة السجل من قاعدة البيانات (Database History) ---
@app.route('/history_db')
@login_required
def history_db():
    # جلب آخر 50 سجل من قاعدة البيانات مرتبة من الأحدث للأقدم
    logs = SensorLog.query.order_by(SensorLog.timestamp.desc()).limit(50).all()

    # كود HTML لعرض الجدول
    history_html = """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>سجل قاعدة البيانات</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; padding: 20px; background-color: #f4f4f9; }
            h1 { color: #2c3e50; }
            table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: center; }
            th { background-color: #34495e; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .back-btn { display: inline-block; margin-bottom: 20px; padding: 10px 20px; background: #2c3e50; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <a href="/" class="back-btn">↩️ العودة للوحة التحكم</a>
        <h1>📂 السجل المحفوظ في قاعدة البيانات (Database)</h1>
        <p>هذه البيانات مخزنة بشكل دائم في ملف SQLite.</p>

        <table>
            <thead>
                <tr>
                    <th>الوقت (Timestamp)</th>
                    <th>الحرارة (°C)</th>
                    <th>الضغط (Bar)</th>
                    <th>الطاقة (kW)</th>
                    <th>الحالة (Status)</th>
                </tr>
            </thead>
            <tbody>
                {% for log in logs %}
                <tr>
                    <td>{{ log.timestamp }}</td>
                    <td>{{ log.temperature }}</td>
                    <td>{{ log.pressure }}</td>
                    <td>{{ log.energy }}</td>
                    <td><span style="color:green">{{ log.status }}</span></td>
                </tr>
                {% else %}
                <tr><td colspan="5">لا توجد بيانات محفوظة بعد. انتظر قليلاً...</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """
    return render_template_string(history_html, logs=logs)
if __name__ == '__main__':
    app.run(debug=True, port=5000)
