from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging
from datetime import datetime
import json

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# قائمة الأرقام المسموحة (يمكنك إضافة أرقام أخرى)
ALLOWED_NUMBERS = [
    '+967774675020',  # رقمك
    '+966500000000',  # يمكنك إضافة أرقام أخرى
]

# ============== دوال المساعدة ==============

def is_allowed_number(phone):
    """التحقق إذا كان الرقم مسموحاً"""
    # تنظيف الرقم
    if phone.startswith('whatsapp:'):
        phone = phone.replace('whatsapp:', '')
    
    # التحقق من القائمة
    for allowed in ALLOWED_NUMBERS:
        if phone == allowed or phone.endswith(allowed.replace('+', '')):
            return True
    
    logger.info(f"📞 رقم جديد: {phone} (غير موجود في القائمة المسموحة)")
    return True  # إرجاع True للسماح بجميع الأرقام للتجربة

def process_message(message):
    """معالجة الرسالة وإعداد الرد"""
    message_lower = message.lower().strip()
    
    # قائمة الأوامر والردود
    responses = {
        'مرحبا': 'أهلاً وسهلاً! 🌹\nكيف يمكنني مساعدتك اليوم؟',
        'السلام عليكم': 'وعليكم السلام ورحمة الله وبركاته 🌺',
        'اهلا': 'أهلاً بك! 😊',
        'hello': 'Hello! 👋\nHow can I help you today?',
        'hi': 'Hi there! 😊',
        
        # الأوامر العربية
        'مساعده': '''🆘 *قائمة الأوامر المتاحة:*
        
• "مرحبا" - للترحيب
• "مساعدة" - لعرض هذه القائمة
• "حالة" - لعرض حالة النظام
• "معلومات" - معلومات عن الخدمة
• "وقت" - الوقت والتاريخ الحالي
• "شكرا" - لإنهاء المحادثة

*للتواصل المباشر:*
📞 0500000000
✉️ info@example.com''',
        
        'مساعدة': '''🆘 *قائمة الأوامر المتاحة:*
        
• "مرحبا" - للترحيب  
• "مساعدة" - لعرض هذه القائمة
• "حالة" - لعرض حالة النظام
• "معلومات" - معلومات عن الخدمة
• "وقت" - الوقت والتاريخ الحالي
• "شكرا" - لإنهاء المحادثة

*للتواصل المباشر:*
📞 0500000000
✉️ info@example.com''',
        
        'حالة': '✅ *حالة النظام:*\n\n🟢 الخدمة تعمل بشكل طبيعي\n📊 جميع الأنظمة نشطة\n🕒 آخر تحديث: ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
        'معلومات': '''🤖 *معلومات النظام:*
        
- الاسم: WhatsApp Auto-Reply Bot
- الإصدار: 2.0
- المطور: فريق الدعم الفني
- الوظيفة: الرد التلقائي على الرسائل
- اللغة: العربية والإنجليزية

📅 تم التحديث: 2024''',
        
        'وقت': '🕒 *التاريخ والوقت الحالي:*\n' + datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
        
        'تاريخ': '📅 *التاريخ الهجري والميلادي:*\n' + datetime.now().strftime("%Y/%m/%d - %A"),
        
        'شكرا': 'العفو! 😊\nشكراً لتواصلك معنا.\nنتمنى لك يوماً سعيداً! 🌟',
        
        'شكر': 'العفو! 🌹\nلا تتردد في التواصل معنا لأي استفسار.',
        
        # الأوامر الإنجليزية
        'help': '''🆘 *Available Commands:*
        
• "hello" - Greeting
• "help" - Show this menu  
• "status" - System status
• "info" - Service information
• "time" - Current time and date
• "thanks" - End conversation

*Contact us:*
📞 +966500000000
✉️ info@example.com''',
        
        'status': '✅ *System Status:*\n\n🟢 Service operational\n📊 All systems active\n🕒 Last update: ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
        'info': '''🤖 *System Information:*
        
- Name: WhatsApp Auto-Reply Bot
- Version: 2.0
- Developer: Support Team
- Function: Auto-reply to messages
- Language: Arabic & English

📅 Updated: 2024''',
        
        'time': '🕒 *Current Date & Time:*\n' + datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
        
        'thanks': 'You\'re welcome! 😊\nThank you for contacting us.\nHave a great day! 🌟',
    }
    
    # البحث عن تطابق كامل
    for keyword in responses:
        if keyword == message_lower:
            return responses[keyword]
    
    # البحث عن تطابق جزئي
    for keyword in responses:
        if keyword in message_lower:
            return responses[keyword]
    
    # الرد الافتراضي
    return '''📱 *مرحباً بك في نظام الرد التلقائي!*

أنا بوت ذكي يمكنني مساعدتك في:

📞 *الاستفسارات الفورية*
🔄 *متابعة الطلبات*  
🛠️ *الدعم الفني*
🔔 *الإشعارات*

*للحصول على المساعدة، أرسل أحد هذه الأوامر:*
• "مساعدة" أو "help" - لعرض جميع الأوامر
• "حالة" أو "status" - حالة النظام
• "معلومات" أو "info" - معلومات عن الخدمة
• "وقت" أو "time" - الوقت الحالي

*للتواصل المباشر مع ممثل خدمة العملاء:*
📞 0500000000
🕒 من 8 صباحاً حتى 10 مساءً

شكراً لاختيارك لنا! 🌟'''

def save_message_log(sender, message, response):
    """حفظ سجل الرسائل"""
    try:
        log_entry = {
            'sender': sender,
            'message': message,
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime("%Y-%m-%d"),
            'time': datetime.now().strftime("%H:%M:%S")
        }
        
        # إنشاء مجلد السجلات
        os.makedirs('message_logs', exist_ok=True)
        
        # اسم الملف بالتاريخ
        log_file = f'message_logs/messages_{datetime.now().strftime("%Y-%m-%d")}.json'
        
        # قراءة السجلات الموجودة
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        logs = json.loads(content)
            except:
                logs = []
        
        # إضافة السجل الجديد
        logs.append(log_entry)
        
        # حفظ الملف
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 تم حفظ الرسالة من {sender}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ السجل: {e}")

# ============== نقطة النهاية الرئيسية ==============

@app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """نقطة استقبال رسائل WhatsApp من Twilio"""
    try:
        # الحصول على البيانات من الطلب
        sender = request.values.get('From', '')
        incoming_msg = request.values.get('Body', '').strip()
        
        logger.info(f"📩 رسالة واردة من: {sender}")
        logger.info(f"📝 محتوى الرسالة: {incoming_msg}")
        
        # التحقق من وجود الرسالة
        if not incoming_msg:
            logger.warning("⚠️ رسالة فارغة مستلمة")
            resp = MessagingResponse()
            resp.message("لم أستلم أي رسالة. يرجى إعادة المحاولة.")
            return str(resp)
        
        # التحقق من الرقم (اختياري)
        if not is_allowed_number(sender):
            logger.warning(f"⛔ رقم غير مسموح: {sender}")
            resp = MessagingResponse()
            resp.message("عذراً، هذا الرقم غير مسموح به حاليًا.")
            return str(resp)
        
        # معالجة الرسالة وإعداد الرد
        response_text = process_message(incoming_msg)
        
        # حفظ السجل
        save_message_log(sender, incoming_msg, response_text)
        
        # إعداد الرد
        resp = MessagingResponse()
        resp.message(response_text)
        
        logger.info(f"📤 تم إرسال الرد إلى: {sender}")
        logger.info(f"💬 محتوى الرد: {response_text[:100]}...")
        
        return str(resp)
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {str(e)}")
        resp = MessagingResponse()
        resp.message("⚠️ عذراً، حدث خطأ في النظام. يرجى المحاولة لاحقاً.")
        return str(resp)

# ============== نقاط نهاية إضافية ==============

@app.route('/health', methods=['GET'])
def health_check():
    """فحص حالة الخادم"""
    return jsonify({
        'status': 'healthy',
        'service': 'whatsapp-auto-reply',
        'timestamp': datetime.now().isoformat(),
        'allowed_numbers': ALLOWED_NUMBERS,
        'message': '✅ النظام يعمل بشكل طبيعي'
    })

@app.route('/logs', methods=['GET'])
def view_logs():
    """عرض سجلات الرسائل"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = f'message_logs/messages_{today}.json'
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # تنسيق HTML للعرض
            html = '''
            <!DOCTYPE html>
            <html dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>سجلات الرسائل</title>
                <style>
                    body { font-family: Arial; padding: 20px; }
                    .message { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                    .incoming { background: #e3f2fd; }
                    .time { color: #666; font-size: 0.9em; }
                </style>
            </head>
            <body>
                <h2>📋 سجلات رسائل اليوم ({date})</h2>
                <p>عدد الرسائل: {count}</p>
            '''.format(date=today, count=len(logs))
            
            for log in reversed(logs):  # عرض أحدث الرسائل أولاً
                html += f'''
                <div class="message incoming">
                    <strong>📞 من:</strong> {log.get('sender', '')}<br>
                    <strong>📩 الرسالة:</strong> {log.get('message', '')}<br>
                    <strong>💬 الرد:</strong> {log.get('response', '')[:200]}...<br>
                    <span class="time">⏰ {log.get('time', '')}</span>
                </div>
                '''
            
            html += '''
                <br>
                <a href="/">العودة للصفحة الرئيسية</a>
            </body>
            </html>
            '''
            
            return html
        else:
            return jsonify({
                'message': 'لا توجد سجلات لهذا اليوم',
                'date': today
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send-test', methods=['GET'])
def send_test_form():
    """نموذج لإرسال رسالة تجريبية"""
    return '''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>اختبار الرد التلقائي</title>
        <style>
            body { font-family: Arial; padding: 20px; max-width: 600px; margin: auto; }
            input, textarea, button { width: 100%; padding: 12px; margin: 8px 0; }
            button { background: #25D366; color: white; border: none; cursor: pointer; }
            .info { background: #e8f5e9; padding: 15px; border-radius: 5px; margin: 15px 0; }
        </style>
    </head>
    <body>
        <h2>🧪 اختبار نظام الرد التلقائي</h2>
        
        <div class="info">
            <strong>ℹ️ معلومات:</strong><br>
            هذا النموذج يحاكي استقبال رسالة من WhatsApp.
            أدخل رسالة لترى كيف سيرد النظام.
        </div>
        
        <input type="text" id="message" placeholder="اكتب رسالتك هنا (مثال: مرحبا)" value="مرحبا">
        <button onclick="simulateMessage()">اختبار الرد</button>
        
        <div id="result" style="margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 5px; display: none;">
            <h3>📨 نتيجة الاختبار:</h3>
            <div id="response"></div>
        </div>
        
        <script>
        async function simulateMessage() {
            const message = document.getElementById('message').value;
            
            if (!message) {
                alert('يرجى إدخال رسالة');
                return;
            }
            
            // إرسال طلب محاكاة
            const response = await fetch('/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });
            
            const result = await response.json();
            const resultDiv = document.getElementById('result');
            const responseDiv = document.getElementById('response');
            
            resultDiv.style.display = 'block';
            
            if (response.ok) {
                responseDiv.innerHTML = `
                    <p><strong>📩 الرسالة الأصلية:</strong> ${result.original_message}</p>
                    <p><strong>💬 الرد التلقائي:</strong><br>${result.response.replace(/\\n/g, '<br>')}</p>
                    <p><strong>⏰ الوقت:</strong> ${result.timestamp}</p>
                `;
            } else {
                responseDiv.innerHTML = `<p style="color: red;">❌ خطأ: ${result.error}</p>`;
            }
        }
        </script>
    </body>
    </html>
    '''

@app.route('/simulate', methods=['POST'])
def simulate_message():
    """محاكاة استقبال رسالة (للتجربة)"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'الرسالة مطلوبة'}), 400
        
        # معالجة الرسالة
        response = process_message(message)
        
        return jsonify({
            'success': True,
            'original_message': message,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return '''
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>نظام الرد التلقائي على WhatsApp</title>
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            
            header {
                background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            
            header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
            }
            
            .status-badge {
                background: rgba(255,255,255,0.2);
                padding: 10px 20px;
                border-radius: 50px;
                display: inline-block;
                font-weight: bold;
                margin-top: 15px;
            }
            
            .main-content {
                padding: 40px;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
            }
            
            .card {
                background: #f8f9fa;
                padding: 30px;
                border-radius: 15px;
                border-left: 5px solid #25D366;
                transition: transform 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            
            .card h3 {
                color: #128C7E;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .btn {
                display: inline-flex;
                align-items: center;
                gap: 10px;
                background: #25D366;
                color: white;
                padding: 15px 25px;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
                margin: 10px 5px;
                transition: all 0.3s ease;
            }
            
            .btn:hover {
                background: #128C7E;
                transform: translateY(-2px);
            }
            
            .instructions {
                background: #e8f5e9;
                padding: 25px;
                border-radius: 10px;
                margin: 20px 0;
            }
            
            .instructions ol {
                margin-right: 20px;
                margin-top: 15px;
            }
            
            .instructions li {
                margin-bottom: 10px;
            }
            
            footer {
                text-align: center;
                padding: 30px;
                background: #f8f9fa;
                color: #666;
                border-top: 1px solid #e0e0e0;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            
            .stat-box {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            
            .stat-box .number {
                font-size: 2em;
                font-weight: bold;
                color: #25D366;
                margin: 10px 0;
            }
            
            @media (max-width: 768px) {
                .main-content {
                    grid-template-columns: 1fr;
                }
                
                header h1 {
                    font-size: 1.8em;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>
                    <span>🤖</span>
                    نظام الرد التلقائي على WhatsApp
                </h1>
                <p>نظام آلي متكامل للرد الفوري على رسائل واتساب</p>
                <div class="status-badge">
                    ✅ النظام نشط وجاهز للاستقبال
                </div>
            </header>
            
            <div class="main-content">
                <div class="card">
                    <h3>🚀 بدء الاستخدام</h3>
                    <div class="instructions">
                        <strong>لبدء الاستخدام:</strong>
                        <ol>
                            <li>أرسل رسالة إلى رقم Sandbox</li>
                            <li>سيرد النظام تلقائياً</li>
                            <li>جرب الأوامر المختلفة</li>
                        </ol>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <a href="/send-test" class="btn">
                            <span>🧪</span> اختبار النظام
                        </a>
                        <a href="/health" class="btn">
                            <span>✅</span> فحص الحالة
                        </a>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📋 الأوامر المتاحة</h3>
                    <ul style="list-style: none; margin-right: 10px;">
                        <li>• "مرحبا" - للترحيب</li>
                        <li>• "مساعدة" - عرض الأوامر</li>
                        <li>• "حالة" - حالة النظام</li>
                        <li>• "معلومات" - معلومات الخدمة</li>
                        <li>• "وقت" - الوقت الحالي</li>
                        <li>• "شكرا" - إنهاء المحادثة</li>
                    </ul>
                    
                    <div style="margin-top: 20px;">
                        <a href="/logs" class="btn">
                            <span>📊</span> عرض السجلات
                        </a>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📊 إحصائيات النظام</h3>
                    <div class="stats">
                        <div class="stat-box">
                            <div class="number">24/7</div>
                            <div>التشغيل</div>
                        </div>
                        <div class="stat-box">
                            <div class="number">⚡</div>
                            <div>رد فوري</div>
                        </div>
                        <div class="stat-box">
                            <div class="number">📱</div>
                            <div>واتساب</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="padding: 0 40px;">
                <div class="instructions">
                    <h3>🔧 معلومات تقنية</h3>
                    <p><strong>نقطة الاستقبال:</strong> POST /whatsapp</p>
                    <p><strong>رقم Sandbox:</strong> +14155238886</p>
                    <p><strong>الأرقام المسموحة:</strong> جميع الأرقام مفعلة للتجربة</p>
                    <p><strong>حالة الويب هوك:</strong> <span style="color: green;">✅ مفعل</span></p>
                </div>
            </div>
            
            <footer>
                <p>🤖 نظام الرد التلقائي على WhatsApp | الإصدار 2.0</p>
                <p>تم النشر على Render.com | {timestamp}</p>
            </footer>
        </div>
        
        <script>
            // عرض التاريخ والوقت
            const now = new Date();
            const options = {
                weekday: 'long',
                year: 'numeric', 
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Asia/Riyadh'
            };
            const timestamp = new Intl.DateTimeFormat('ar-SA', options).format(now);
            document.body.innerHTML = document.body.innerHTML.replace('{timestamp}', timestamp);
        </script>
    </body>
    </html>
    '''

# معالجة الأخطاء
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'الصفحة غير موجودة'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Internal server error: {error}")
    return jsonify({'error': 'Internal server error', 'message': 'حدث خطأ داخلي'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info("=" * 50)
    logger.info("🚀 بدء تشغيل نظام الرد التلقائي على WhatsApp")
    logger.info(f"🌐 البورت: {port}")
    logger.info(f"📞 الأرقام المسموحة: {ALLOWED_NUMBERS}")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)