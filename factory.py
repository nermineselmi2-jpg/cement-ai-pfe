import random
from datetime import datetime


class CementPlantDigitalTwin:
    def __init__(self):
        # 1. الحساسات القديمة
        self.status = "Running"
        self.temperature = 1450.0  # درجة حرارة الفرن
        self.pressure = 25.0  # الضغط داخل الكيلن
        self.energy_consumption = 450.0  # استهلاك الطاقة
        self.production_tons = 1200.0  # إجمالي الإنتاج

        # 2. متغيرات المخزون الجديدة (Inventory)
        self.warehouse_capacity = 1000.0  # سعة المستودع (1000 طن مثلاً)
        self.current_stock = 500.0  # المخزون الحالي (يبدأ بالنصف)
        self.production_rate = 20.0  # معدل الإضافة (كل ثانية يزداد 2 طن لسرعة العرض)

    def update_sensors(self):
        """تحديث البيانات وحساب المخزون"""

        # --- تحديث الحساسات العشوائية ---
        self.temperature += random.uniform(-5, 5)
        self.pressure += random.uniform(-0.5, 0.5)
        self.energy_consumption += random.uniform(-10, 10)

        # ضبط الحدود
        self.temperature = max(1400, min(1500, self.temperature))
        self.pressure = max(20, min(30, self.pressure))

        # --- تحديث الإنتاج والمخزون (الربط) ---
        self.production_tons += self.production_rate
        self.current_stock += self.production_rate

        # شرط: إذا امتلأ المستودع
        if self.current_stock >= self.warehouse_capacity:
            self.current_stock = self.warehouse_capacity
            self.status = "ممتلئ - توقف الإنتاج"
        else:
            self.status = "Running"

        # إرجاع البيانات
        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "temp": round(self.temperature, 2),
            "pressure": round(self.pressure, 2),
            "energy": round(self.energy_consumption, 2),
            "production": round(self.production_tons, 2),
            "status": self.status
        }


# إنشاء الكائن
plant_twin = CementPlantDigitalTwin()