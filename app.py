from fastapi import logger
from twilio.rest import Client
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

app = Flask(__name__)

# الحصول على بيانات الاعتماد من متغيرات البيئة
ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')

# التحقق من وجود بيانات الاعتماد
if not all([ACCOUNT_SID, AUTH_TOKEN]):
    raise ValueError("❌ يرجى تعيين TWILIO_ACCOUNT_SID و TWILIO_AUTH_TOKEN في متغيرات البيئة")

# تهيئة Twilio client
client = Client(ACCOUNT_SID, AUTH_TOKEN)

def process_command(message, sender):
    """معالجة الأوامر المختلفة مع دعم اللغة العربية"""
    message_lower = message.lower()
    
    commands = {
        'help': '🆘 الأوامر المتاحة:\n• حالة - لعرض حالة النظام\n• طلب - لإنشاء طلب جديد\n• معلومات - لمعلومات عن الخدمة\n• دعم - للاتصال بالدعم الفني',
        'حالة': '✅ حالة النظام تعمل بشكل طبيعي\n🕒 آخر تحديث: ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'طلب': '📝 لإنشاء طلب جديد، يرجى زيارة:\nhttps://your-site.com/orders/new\nأو تواصل معنا على الرقم: ٠٥٠٠٠٠٠٠٠٠',
        'معلومات': '🤖 هذا نظام آلي للرد على رسائل واتساب\n🔄 الإصدار: 2.0\n📅 تاريخ التحديث: 2024',
        'دعم': '📞 للدعم الفني:\nالهاتف: ٠٥٠٠٠٠٠٠٠٠\nالبريد: support@your-site.com\nالموقع: https://your-site.com/support',
        'hello': 'مرحباً! 👋\nكيف يمكنني مساعدتك اليوم؟',
        'hi': 'أهلاً وسهلاً! 😊'
    }
    
    # البحث في الأوامر
    for key in commands:
        if key in message_lower:
            return commands[key]
    
    # الرد الافتراضي
    return '''📱 شكراً لتواصلك معنا!

للحصول على المساعدة، يمكنك استخدام إحدى الأوامر التالية:
• "حالة" - لعرض حالة النظام
• "طلب" - لإنشاء طلب جديد
• "معلومات" - لمعلومات عن الخدمة
• "دعم" - للاتصال بالدعم الفني

أو تواصل معنا مباشرة على:
📞 ٠٥٠٠٠٠٠٠٠٠
✉️ info@your-site.com'''

@app.route('/whatsapp', methods=['POST'])
def handle_whatsapp():
    """معالجة رسائل WhatsApp الواردة"""
    try:
        incoming_msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '')
        
        if not incoming_msg:
            return 'No message body', 400
        
        # معالجة الرسالة
        response_text = process_command(incoming_msg, sender)
        
        # إرسال الرد
        resp = MessagingResponse()
        resp.message(response_text)
        
        # تسجيل الرسالة
        log_message(sender, incoming_msg, response_text)
        
        return str(resp)
    
    except Exception as e:
        app.logger.error(f"❌ خطأ في معالجة الرسالة: {str(e)}")
        resp = MessagingResponse()
        resp.message("⚠️ عذراً، حدث خطأ في النظام. يرجى المحاولة لاحقاً.")
        return str(resp)

@app.route('/send-message', methods=['POST'])
def send_message():
    """واجهة برمجية لإرسال رسائل WhatsApp"""
    try:
        data = request.json
        
        if not data or 'to' not in data or 'message' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        to_number = data['to']
        message_body = data['message']
        
        # إرسال الرسالة
        message = client.messages.create(
            from_=f'whatsapp:{TWILIO_WHATSAPP_NUMBER}' if TWILIO_WHATSAPP_NUMBER else 'whatsapp:+14155238886',
            body=message_body,
            to=f'whatsapp:{to_number}'
        )
        
        # تسجيل الرسالة الصادرة
        log_message(f'whatsapp:{to_number}', 'SYSTEM_SENT', message_body, 'outgoing')
        
        return jsonify({
            'success': True,
            'message_sid': message.sid,
            'status': message.status
        })
    
    except Exception as e:
        app.logger.error(f"❌ خطأ في إرسال الرسالة: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/status-callback', methods=['POST'])
def status_callback():
    """استقبال تحديثات حالة الرسائل من Twilio"""
    try:
        message_sid = request.values.get('MessageSid', '')
        message_status = request.values.get('MessageStatus', '')
        error_code = request.values.get('ErrorCode', '')
        to_number = request.values.get('To', '')
        
        logger.info(f"📊 Message Status Update: {message_sid} -> {message_status}")
        
        if message_status in ['failed', 'undelivered']:
            logger.error(f"❌ Message failed: {message_sid}, Error: {error_code}, To: {to_number}")
        
        # يمكنك حفظ هذه المعلومات في قاعدة بيانات
        save_message_status({
            'message_sid': message_sid,
            'status': message_status,
            'error_code': error_code,
            'to': to_number,
            'timestamp': datetime.now().isoformat()
        })
        
        return '', 200
    
    except Exception as e:
        logger.error(f"❌ Error in status callback: {str(e)}")
        return '', 200

def save_message_status(status_data):
    """حفظ حالة الرسالة"""
    try:
        os.makedirs('status_logs', exist_ok=True)
        log_file = f'status_logs/status_{datetime.now().strftime("%Y-%m-%d")}.json'
        
        # قراءة السجلات الموجودة
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        logs = json.loads(f'[{content.replace("}{", "},{")}]')
            except:
                logs = []
        
        # إضافة السجل الجديد
        logs.append(status_data)
        
        # حفظ الملف
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved status: {status_data['message_sid']} -> {status_data['status']}")
    
    except Exception as e:
        logger.error(f"❌ Error saving status: {str(e)}")
        
@app.route('/health', methods=['GET'])
def health_check():
    """فحص حالة التطبيق"""
    return jsonify({
        'status': 'healthy',
        'service': 'whatsapp-bot',
        'timestamp': datetime.now().isoformat(),
        'twilio_configured': bool(ACCOUNT_SID and AUTH_TOKEN)
    })

def log_message(sender, incoming, response, direction='incoming'):
    """تسجيل الرسائل في ملف JSON"""
    try:
        log_entry = {
            'sender': sender,
            'incoming': incoming,
            'response': response,
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
                        logs = json.loads(f'[{content.replace("}{", "},{")}]')
            except json.JSONDecodeError:
                logs = []
        
        # إضافة السجل الجديد
        logs.append(log_entry)
        
        # حفظ الملف
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        # طباعة في السجلات (لـ Render)
        print(f"📝 {direction.upper()} LOG: {sender} -> {incoming[:50]}...")
    
    except Exception as e:
        app.logger.error(f"❌ خطأ في التسجيل: {str(e)}")

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return '''
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>نظام WhatsApp Bot</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #128C7E; text-align: center; }
            .status { background: #25D366; color: white; padding: 10px; border-radius: 5px; text-align: center; }
            .endpoints { margin-top: 30px; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-right: 4px solid #128C7E; }
            code { background: #eee; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 نظام WhatsApp Bot</h1>
            <div class="status">
                ✅ النظام يعمل بشكل طبيعي
            </div>
            
            <div class="endpoints">
                <h2>📋 نقاط الواجهة البرمجية:</h2>
                
                <div class="endpoint">
                    <strong>POST /whatsapp</strong><br>
                    نقطة استقبال رسائل WhatsApp من Twilio
                </div>
                
                <div class="endpoint">
                    <strong>POST /send-message</strong><br>
                    إرسال رسالة WhatsApp<br>
                    <code>{ "to": "+966500000000", "message": "مرحباً" }</code>
                </div>
                
                <div class="endpoint">
                    <strong>GET /health</strong><br>
                    فحص حالة النظام
                </div>
            </div>
            
            <p style="text-align: center; margin-top: 30px; color: #666;">
                ℹ️ تم النشر على Render.com | {timestamp}
            </p>
        </div>
        
        <script>
            document.body.innerHTML = document.body.innerHTML.replace('{timestamp}', new Date().toLocaleString('ar-SA'));
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)