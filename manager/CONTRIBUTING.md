# Contributing to NextGen Hub

شكراً لك على اهتمامك بالمساهمة في NextGen Hub! هذا الدليل سيساعدك على البدء.

## كيفية المساهمة

### الإبلاغ عن الأخطاء

1. تحقق من أن المشكلة لم يتم الإبلاغ عنها مسبقاً
2. استخدم قالب الإبلاغ عن الأخطاء
3. وصف المشكلة بالتفصيل مع خطوات إعادة الإنتاج
4. أرفق سجلات الأخطاء إن أمكن

### اقتراح ميزات جديدة

1. تحقق من أن الميزة لم يتم اقتراحها مسبقاً
2. وصف الميزة المطلوبة بالتفصيل
3. اشرح الفائدة من هذه الميزة
4. اقترح كيفية تنفيذها إن أمكن

### المساهمة بالكود

#### إعداد بيئة التطوير

1. Fork المشروع
2. Clone الـ repository المحلي:
   ```bash
   git clone https://github.com/YOUR_USERNAME/nextgen-hub.git
   cd nextgen-hub
   ```

3. إنشاء بيئة افتراضية:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # أو
   venv\Scripts\activate     # Windows
   ```

4. تثبيت المتطلبات:
   ```bash
   pip install -r backend/requirements.txt
   pip install -e .[dev]
   ```

#### إرشادات التطوير

1. **إنشاء Branch جديد**:
   ```bash
   git checkout -b feature/your-feature-name
   # أو
   git checkout -b fix/your-bug-fix
   ```

2. **كتابة الكود**:
   - اتبع معايير PEP 8
   - أضف تعليقات باللغة الإنجليزية
   - اكتب اختبارات للميزات الجديدة
   - تأكد من أن جميع الاختبارات تمر

3. **تنسيق الكود**:
   ```bash
   black manager/ tests/
   isort manager/ tests/
   ```

4. **فحص جودة الكود**:
   ```bash
   flake8 manager/ tests/
   mypy manager/
   ```

5. **تشغيل الاختبارات**:
   ```bash
   pytest tests/ -v
   ```

#### إرشادات الـ Commit

- استخدم رسائل commit واضحة ومختصرة
- ابدأ الرسالة بفعل في المضارع (Add, Fix, Update, etc.)
- اكتب الرسالة باللغة الإنجليزية
- أمثلة:
  ```
  Add system metrics collection
  Fix terminal window visibility issue
  Update dashboard UI components
  ```

#### إرشادات الـ Pull Request

1. **إنشاء Pull Request**:
   - اذهب إلى GitHub repository الأصلي
   - انقر على "New Pull Request"
   - اختر branch الخاص بك

2. **وصف التغييرات**:
   - استخدم قالب Pull Request
   - وصف التغييرات بالتفصيل
   - اذكر أي breaking changes
   - أرفق screenshots إن أمكن

3. **التأكد من**:
   - جميع الاختبارات تمر
   - الكود يتبع المعايير
   - الوثائق محدثة
   - لا توجد conflicts

## معايير الكود

### Python

- Python 3.8+
- اتبع PEP 8
- استخدم type hints
- اكتب docstrings للدوال
- استخدم f-strings بدلاً من .format()

### الواجهة الأمامية

- HTML5 semantic markup
- CSS3 مع متغيرات CSS
- JavaScript ES6+
- استخدم Tailwind CSS للتصميم
- تأكد من التوافق مع المتصفحات

### قاعدة البيانات

- استخدم YAML للتكوين
- تأكد من صحة البيانات
- استخدم validation للبيانات

## الاختبارات

### أنواع الاختبارات

1. **Unit Tests**: اختبار الدوال الفردية
2. **Integration Tests**: اختبار التفاعل بين المكونات
3. **End-to-End Tests**: اختبار التطبيق بالكامل

### كتابة الاختبارات

```python
import pytest
from manager.backend.models import ProjectConfig

def test_project_config_validation():
    """Test project configuration validation"""
    config = ProjectConfig(
        id="test-project",
        name="Test Project",
        working_dir="/path/to/project",
        command="python"
    )
    assert config.id == "test-project"
    assert config.name == "Test Project"
```

## الوثائق

### تحديث الوثائق

- حدث README.md عند إضافة ميزات جديدة
- حدث API documentation
- أضف أمثلة للاستخدام
- حدث CHANGELOG.md

### معايير الوثائق

- اكتب باللغة العربية للوثائق العامة
- استخدم اللغة الإنجليزية للكود والتعليقات
- اكتب أمثلة واضحة
- استخدم Markdown formatting

## إرشادات عامة

### التواصل

- كن محترماً ومهذباً
- استخدم اللغة العربية في المناقشات العامة
- استخدم اللغة الإنجليزية للكود والتعليقات التقنية
- اطرح أسئلة إذا كنت غير متأكد

### الجودة

- اكتب كود نظيف وقابل للقراءة
- اتبع مبادئ SOLID
- استخدم meaningful names للمتغيرات والدوال
- اكتب اختبارات شاملة

### الأمان

- لا تضع معلومات حساسة في الكود
- استخدم validation للمدخلات
- اتبع مبادئ الأمان الأساسية
- افحص الكود بحثاً عن ثغرات أمنية

## الحصول على المساعدة

إذا كنت بحاجة إلى مساعدة:

1. اقرأ الوثائق أولاً
2. ابحث في Issues المفتوحة والمغلقة
3. اطرح سؤالاً في Discussions
4. تواصل مع المطورين عبر Issues

## شكر وتقدير

شكراً لك على مساهمتك في NextGen Hub! كل مساهمة، مهما كانت صغيرة، تساعد في تحسين المشروع.

---

**ملاحظة**: هذا الدليل قابل للتحديث. يرجى مراجعة أحدث إصدار قبل البدء في المساهمة. 