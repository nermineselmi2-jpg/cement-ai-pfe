from app import app
from models import db, User
from werkzeug.security import generate_password_hash

# هذا الكود ينفذ داخلياً بدون متصفح
with app.app_context():
    # التحقق هل المستخدم موجود؟
    if User.query.filter_by(username='admin').first():
        print("المستخدم Admin موجود بالفعل في قاعدة البيانات.")
    else:
        # إنشاء المستخدم
        hashed_pw = generate_password_hash('admin123')
        admin = User(username='admin', password=hashed_pw, role='admin')
        db.session.add(admin)
        db.session.commit()
        print("✅ تم إنشاء المستخدم Admin بنجاح!")
        print("اسم المستخدم: admin")
        print("كلمة المرور: admin123")