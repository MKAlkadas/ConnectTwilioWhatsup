from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# الحصول على بيانات الاعتماد من متغيرات البيئة
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

# التحقق من وجود بيانات الاعتماد
if not ACCOUNT_SID or not AUTH_TOKEN:
    logger.error("❌ يرجى تعيين TWILIO_ACCOUNT_SID و TWILIO_AUTH_TOKEN في متغيرات البيئة")
    logger.error("❌ على Render: أضف Environment Variables في Dashboard")

# تهيئة Twilio client
try:
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    validator = RequestValidator(AUTH_TOKEN) if AUTH_TOKEN else None
    logger.info("✅ Twilio client initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Twilio client: {e}")
    client = None
    validator = None

# ============== دوال المساعدة ==============

def process_command(message, sender):
    """معالجة الأوامر المختلفة"""
    message_lower = message.lower().strip()
    
    # أوامر عربية
    commands = {
        'مرحبا': 'أهلاً وسهلاً! 😊 كيف يمكنني مساعدتك؟',
        'السلام عليكم': 'وعليكم السلام ورحمة الله وبركاته 🌹',
        'مساعده': '''🆘 *الأوامر المتاحة:*
• "مرحبا" - للترحيب
• "مساعدة" - لعرض هذه القائمة
• "حالة" - لعرض حالة النظام
• "طلب" - لإنشاء طلب جديد
• "معلومات" - لمعلومات عن الخدمة
• "دعم" - للاتصال بالدعم''',
        'مساعدة': '''🆘 *الأوامر المتاحة:*
• "مرحبا" - للترحيب
• "مساعدة" - لعرض هذه القائمة
• "حالة" - لعرض حالة النظام
• "طلب" - لإنشاء طلب جديد
• "معلومات" - لمعلومات عن الخدمة
• "دعم" - للاتصال بالدعم''',
        'حالة': '✅ *حالة النظام:* تعمل بشكل طبيعي\n🕒 *آخر تحديث:* ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'طلب': '''📝 *لإنشاء طلب جديد:*
1. قم بزيارة موقعنا الإلكتروني
2. أو اتصل بنا على: ٠٥٠٠٠٠٠٠٠٠
3. أو أرسل "تفاصيل" لمزيد من المعلومات''',
        'معلومات': '''🤖 *معلومات النظام:*
- الاسم: WhatsApp Bot
- الإصدار: 2.0
- التاريخ: 2024
- المطور: فريق الدعم الفني''',
        'دعم': '''📞 *الدعم الفني:*
- الهاتف: ٠٥٠٠٠٠٠٠٠٠
- البريد: support@example.com
- ساعات العمل: 8 صباحاً - 10 مساءً''',
        'شكرا': 'العفو! 😊 نحن هنا لخدمتك دائماً',
        'تفاصيل': '''📋 *تفاصيل الخدمة:*
نقدم خدمات متكاملة عبر واتساب تشمل:
1. الاستفسارات الفورية
2. متابعة الطلبات
3. الدعم الفني
4. الإشعارات والتحديثات''',
        
        # أوامر إنجليزية
        'hello': 'Hello! 👋 How can I help you today?',
        'hi': 'Hi there! 😊',
        'help': '''🆘 *Available Commands:*
• "hello" - For greeting
• "help" - Show this help menu
• "status" - Check system status
• "order" - Create new order
• "info" - Service information
• "support" - Contact support''',
        'status': '✅ *System Status:* Operating normally\n🕒 *Last Update:* ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'order': '''📝 *To create a new order:*
1. Visit our website
2. Or call us: +966500000000
3. Or send "details" for more info''',
        'info': '''🤖 *System Information:*
- Name: WhatsApp Bot
- Version: 2.0
- Date: 2024
- Developer: Support Team''',
        'support': '''📞 *Technical Support:*
- Phone: +966500000000
- Email: support@example.com
- Hours: 8 AM - 10 PM''',
        'thanks': 'You\'re welcome! 😊 We\'re always here to help',
        'thank you': 'You\'re welcome! 😊',
        'details': '''📋 *Service Details:*
We offer comprehensive WhatsApp services including:
1. Instant inquiries
2. Order tracking
3. Technical support
4. Notifications and updates'''
    }
    
    # البحث عن تطابق كامل أو جزئي
    for key in commands:
        if key in message_lower:
            return commands[key]
    
    # الرد الافتراضي
    return '''📱 *مرحباً بك!*

أنا بوت واتساب الذكي. يمكنني مساعدتك في:
• الاستفسارات الفورية
• متابعة الطلبات  
• الدعم الفني
• الإشعارات

*جرب أحد هذه الأوامر:*
• "مساعدة" أو "help"
• "حالة" أو "status"
• "طلب" أو "order"
• "دعم" أو "support"

*للتواصل المباشر:*
📞 ٠٥٠٠٠٠٠٠٠٠
✉️ info@example.com'''

def log_message(sender, incoming, response, direction='incoming'):
    """تسجيل الرسائل في ملف JSON"""
    try:
        log_entry = {
            'sender': sender,
            'incoming': incoming,
            'response': response[:500] if response else '',
            'direction': direction,
            'timestamp': datetime.now().isoformat()
        }
        
        # إنشاء مجلد logs إذا لم يكن موجوداً
        os.makedirs('logs', exist_ok=True)
        
        log_file = f'logs/whatsapp_logs_{datetime.now().strftime("%Y-%m-%d")}.json'
        
        # قراءة السجلات الموجودة
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        # التعامل مع تنسيق JSON lines
                        lines = content.strip().split('\n')
                        for line in lines:
                            if line.strip():
                                logs.append(json.loads(line.strip()))
            except Exception as e:
                logger.error(f"❌ Error reading log file: {e}")
                logs = []
        
        # إضافة السجل الجديد
        logs.append(log_entry)
        
        # حفظ الملف
        with open(log_file, 'w', encoding='utf-8') as f:
            for entry in logs:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        # طباعة في سجلات التطبيق
        log_type = "📨 INCOMING" if direction == 'incoming' else "📤 OUTGOING"
        logger.info(f"{log_type}: {sender} -> {incoming[:50]}...")
        
    except Exception as e:
        logger.error(f"❌ Error logging message: {str(e)}")

# ============== نقاط النهاية ==============

@app.route('/whatsapp', methods=['POST'])
def handle_whatsapp():
    """معالجة رسائل WhatsApp الواردة"""
    try:
        logger.info("📨 Received WhatsApp webhook request")
        
        incoming_msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '')
        
        logger.info(f"📩 Message from {sender}: {incoming_msg}")
        
        if not incoming_msg:
            logger.warning("⚠️ Empty message received")
            return 'No message body', 400
        
        # معالجة الرسالة
        response_text = process_command(incoming_msg, sender)
        
        # إرسال الرد
        resp = MessagingResponse()
        resp.message(response_text)
        
        # تسجيل الرسالة
        log_message(sender, incoming_msg, response_text)
        
        logger.info(f"📤 Sent response to {sender}")
        return str(resp)
    
    except Exception as e:
        logger.error(f"❌ Error handling WhatsApp message: {str(e)}")
        resp = MessagingResponse()
        resp.message("⚠️ عذراً، حدث خطأ في النظام. يرجى المحاولة لاحقاً.")
        return str(resp)

@app.route('/send-message', methods=['POST'])
def send_message():
    """واجهة برمجية لإرسال رسائل WhatsApp"""
    try:
        logger.info("📤 Received request to send message")
        
        # التحقق من نوع المحتوى
        if not request.is_json:
            logger.error("❌ Content-Type must be application/json")
            return jsonify({'error': 'Content-Type must be application/json'}), 415
        
        data = request.get_json()
        
        if not data:
            logger.error("❌ No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400
        
        # التحقق من الحقول المطلوبة
        if 'to' not in data or 'message' not in data:
            logger.error("❌ Missing required fields: 'to' or 'message'")
            return jsonify({'error': 'Missing required fields: "to" and "message"'}), 400
        
        to_number = data['to']
        message_body = data['message']
        
        # التحقق من صحة رقم الهاتف
        if not to_number.startswith('+'):
            logger.error(f"❌ Invalid phone number format: {to_number}")
            return jsonify({'error': 'Phone number must start with +'}), 400
        
        # التحقق من أن Twilio client معيّن
        if not client:
            logger.error("❌ Twilio client not initialized")
            return jsonify({'error': 'Twilio client not configured'}), 500
        
        logger.info(f"📤 Sending message to {to_number}")
        
        # إرسال الرسالة
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=f'whatsapp:{to_number}'
        )
        
        logger.info(f"✅ Message sent successfully. SID: {message.sid}")
        
        # تسجيل الرسالة الصادرة
        log_message(f'whatsapp:{to_number}', 'SYSTEM_SENT', message_body, 'outgoing')
        
        return jsonify({
            'success': True,
            'message_sid': message.sid,
            'status': message.status,
            'to': to_number,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"❌ Error sending message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/send-message', methods=['GET'])
def send_message_get():
    """عرض نموذج إرسال رسالة"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>إرسال رسالة WhatsApp</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            input, textarea { width: 100%; padding: 10px; margin: 10px 0; }
            button { background: #25D366; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h2>إرسال رسالة WhatsApp تجريبية</h2>
        <input type="text" id="to" placeholder="رقم الهاتف (+966500000000)">
        <textarea id="message" rows="5" placeholder="نص الرسالة..."></textarea>
        <button onclick="sendMessage()">إرسال</button>
        <div id="result"></div>
        
        <script>
        async function sendMessage() {
            const data = {
                to: document.getElementById('to').value,
                message: document.getElementById('message').value
            };
            
            const response = await fetch('/send-message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (response.ok) {
                document.getElementById('result').innerHTML = 
                    `<p style="color: green;">✅ تم الإرسال بنجاح! SID: ${result.message_sid}</p>`;
            } else {
                document.getElementById('result').innerHTML = 
                    `<p style="color: red;">❌ خطأ: ${result.error}</p>`;
            }
        }
        </script>
    </body>
    </html>
    '''

@app.route('/status-callback', methods=['POST'])
def status_callback():
    """استقبال تحديثات حالة الرسائل"""
    try:
        message_sid = request.values.get('MessageSid', '')
        message_status = request.values.get('MessageStatus', '')
        
        logger.info(f"📊 Message Status: {message_sid} -> {message_status}")
        
        return '', 200
    except Exception as e:
        logger.error(f"❌ Error in status callback: {e}")
        return '', 200

@app.route('/health', methods=['GET'])
def health_check():
    """فحص حالة التطبيق"""
    status = {
        'status': 'healthy',
        'service': 'whatsapp-bot',
        'timestamp': datetime.now().isoformat(),
        'twilio_configured': bool(ACCOUNT_SID and AUTH_TOKEN),
        'environment': os.getenv('FLASK_ENV', 'production'),
        'endpoints': {
            'whatsapp': '/whatsapp (POST)',
            'send_message': '/send-message (POST/GET)',
            'health': '/health (GET)',
            'status_callback': '/status-callback (POST)'
        }
    }
    logger.info("✅ Health check passed")
    return jsonify(status)

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WhatsApp Bot</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
            .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #25D366; text-align: center; }
            .status { background: #25D366; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 20px 0; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #25D366; }
            .btn { display: inline-block; background: #25D366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 WhatsApp Bot System</h1>
            
            <div class="status">
                ✅ النظام يعمل بشكل طبيعي
            </div>
            
            <div>
                <h2>نقاط الواجهة البرمجية:</h2>
                
                <div class="endpoint">
                    <strong>POST /whatsapp</strong><br>
                    استقبال رسائل WhatsApp من Twilio
                </div>
                
                <div class="endpoint">
                    <strong>POST /send-message</strong><br>
                    إرسال رسائل WhatsApp
                </div>
                
                <div class="endpoint">
                    <strong>POST /status-callback</strong><br>
                    تحديثات حالة الرسائل
                </div>
                
                <div class="endpoint">
                    <strong>GET /health</strong><br>
                    فحص حالة النظام
                </div>
            </div>
            
            <div style="margin-top: 30px; text-align: center;">
                <a href="/health" class="btn">فحص الحالة</a>
                <a href="/send-message" class="btn">إرسال رسالة</a>
            </div>
            
            <p style="text-align: center; margin-top: 30px; color: #666;">
                تم النشر على Render.com | الإصدار 2.0
            </p>
        </div>
    </body>
    </html>
    '''

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'الصفحة غير موجودة'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed', 'message': 'طريقة الطلب غير مسموحة'}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Internal server error: {error}")
    return jsonify({'error': 'Internal server error', 'message': 'حدث خطأ داخلي'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Starting WhatsApp Bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)