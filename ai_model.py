import random
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


class CementAI:
    def __init__(self):
        self.model = LinearRegression()
        # سنخزن آخر 50 قراءة لتدريب النموذج عليها
        self.data_history = []
        self.is_trained = False

    def add_data(self, temperature, pressure, energy):
        """إضافة البيانات الجديدة للتاريخ"""
        self.data_history.append({
            'temp': temperature,
            'pressure': pressure,
            'energy': energy
        })
        # نحتفظ بآخر 50 نقطة فقط للحفاظ على السرعة
        if len(self.data_history) > 50:
            self.data_history.pop(0)

        # نعيد تدريب النموذج مع كل بيانات جديدة (Online Learning بسيط)
        self.train_model()

    def train_model(self):
        """تدريب النموذج للربط بين الضغط/الطاقة والحرارة"""
        if len(self.data_history) < 10:
            return  # نحتاج 10 نقاط بيانات على الأقل

        # تحضير البيانات
        df = pd.DataFrame(self.data_history)
        X = df[['pressure', 'energy']]  # المدخلات (السبب)
        y = df['temp']  # المخرجات (النتيجة)

        try:
            self.model.fit(X, y)
            self.is_trained = True
        except:
            pass

    def predict_temp(self, future_pressure, future_energy):
        """التنبؤ بالحرارة بناءً على قيم مستقبلية"""
        if not self.is_trained:
            return None

        # إصلاح تحذير Sklearn: نمرر البيانات كـ DataFrame ليطابق أسماء الأعمدة
        input_data = pd.DataFrame([[future_pressure, future_energy]], columns=['pressure', 'energy'])
        prediction = self.model.predict(input_data)
        return prediction[0]

    # === الدالة الناقصة التي تسببت في الخطأ ===
    def predict_maintenance(self, temp, pressure):
        """خوارزمية بسيطة للتنبؤ بالأعطال"""
        risk_score = 0

        # قواعد بسيطة (Rules)
        if temp > 1480: risk_score += 30
        if pressure > 28: risk_score += 40
        if temp < 1400: risk_score += 20

        if risk_score > 50:
            return "خطر: الصيانة مطلوبة فوراً!", "red"
        elif risk_score > 20:
            return "تنبيه: راقب المستويات", "orange"
        else:
            return "الوضع طبيعي", "green"


# إنشاء كائن الذكاء الاصطناعي
ai_brain = CementAI()