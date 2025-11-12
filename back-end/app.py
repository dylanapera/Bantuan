"""
Bantuan - Multi-lingual ASEAN Support Bot Backend
Python Flask application that integrates with Azure AI Foundry
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from openai import AzureOpenAI
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for frontend communication
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuration
app.config['JSON_SORT_KEYS'] = False

# AI Foundry Configuration (to be set via environment variables)
AI_FOUNDRY_ENDPOINT = os.getenv('AI_FOUNDRY_ENDPOINT', '')
AI_FOUNDRY_KEY = os.getenv('AI_FOUNDRY_KEY', '')
AI_FOUNDRY_DEPLOYMENT = os.getenv('AI_FOUNDRY_DEPLOYMENT', '')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Bantuan Backend',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint that processes user messages and returns AI responses
    
    Expected JSON payload:
    {
        "message": "user message",
        "language": "en",
        "category": "general"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'message' not in data:
            logger.warning("Chat request missing 'message' field")
            return jsonify({'error': 'Missing required field: message'}), 400
        
        user_message = data.get('message', '').strip()
        language = data.get('language', 'en')
        category = data.get('category', 'general')
        
        if not user_message:
            logger.warning("Chat request received with empty message")
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Log the incoming request
        logger.info(f"📨 Chat Request - Message: '{user_message[:100]}...' | Language: {language} | Category: {category}")
        
        # Call AI Foundry to process the message
        ai_response = call_ai_foundry(user_message, language, category)
        
        response_data = {
            'status': 'success',
            'message': user_message,
            'response': ai_response,
            'language': language,
            'category': category,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Chat Response - Generated: '{ai_response[:100]}...'")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing chat request: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


# Initialize Azure OpenAI client
def get_azure_client():
    """Initialize and return Azure OpenAI client"""
    api_key = os.getenv('AI_FOUNDRY_KEY')
    endpoint = os.getenv('AI_FOUNDRY_ENDPOINT')
    
    if not api_key or not endpoint:
        logger.warning("AI_FOUNDRY_KEY or AI_FOUNDRY_ENDPOINT not configured")
        return None
    
    return AzureOpenAI(
        api_key=api_key,
        api_version="2024-05-01-preview",
        azure_endpoint=endpoint
    )


def call_ai_foundry(message: str, language: str, category: str) -> str:
    """
    Call Azure AI Foundry (OpenAI) to get AI response
    
    Uses the Azure OpenAI API to process user messages and generate intelligent responses
    
    Args:
        message: User message
        language: Language code
        category: Support category
        
    Returns:
        AI-generated response
    """
    try:
        client = get_azure_client()
        
        if not client:
            logger.warning("Azure OpenAI client not configured, using fallback response")
            return get_fallback_response(language)
        
        # Build the system prompt
        system_prompt = f"""You are Bantuan, a friendly multilingual support assistant for ASEAN countries.
You speak fluent {language} and help users in the {category} category.
You are helpful, professional, and patient.
Keep responses concise (2-3 sentences max).
Always respond in {language}.
User's current category: {category}

Available categories:
- technical: For technical issues and troubleshooting
- account: For account and profile related queries
- billing: For billing and payment questions
- general: For general inquiries

Respond naturally to the user's message in their language."""

        logger.info(f"Calling Azure OpenAI with message: '{message[:50]}...' in language: {language}, category: {category}")
        
        # Call Azure OpenAI API
        deployment_name = os.getenv('AI_FOUNDRY_DEPLOYMENT', 'gpt-35-turbo')
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=200,
            top_p=0.95
        )
        
        ai_response = response.choices[0].message.content.strip()
        logger.info(f"AI Response: '{ai_response[:100]}...'")
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error calling Azure AI Foundry: {str(e)}")
        logger.info("Using fallback response due to AI Foundry error")
        return get_fallback_response(language)


def generate_chatbot_response(message: str, language: str, category: str) -> str:
    """
    DEPRECATED: This function is kept for reference only.
    The backend now uses Azure AI Foundry for all responses.
    """
    logger.info("⚠️  Using fallback response - Azure AI Foundry not configured")
    return get_fallback_response(language)


def get_greeting_response(language: str) -> str:
    """Generate greeting response based on language"""
    greetings = {
        'en': "Hello! Welcome to Bantuan Support. How can I help you today?",
        'id': "Halo! Selamat datang di Dukungan Bantuan. Bagaimana cara saya membantu Anda hari ini?",
        'ms': "Halo! Selamat datang ke Sokongan Bantuan. Bagaimana saya boleh membantu anda hari ini?",
        'th': "สวัสดี! ยินดีต้อนรับสู่ Bantuan Support วันนี้ฉันสามารถช่วยคุณได้อย่างไร",
        'vi': "Xin chào! Chào mừng bạn đến với Hỗ trợ Bantuan. Tôi có thể giúp bạn như thế nào hôm nay?",
        'tl': "Halo! Maligayang pagdating sa Bantuan Support. Paano ko kayo matutulungan ngayong araw?",
        'my': "ဟယ်လို! Bantuan Support သို့ လှိုက်လှိုက်လှိုက်သည့် ကြိုဆိုပါသည်။ ယနေ့ ကျွန်ုပ်သည် သင့်အား မည်သည့်နည်းဖြင့် ကူညီပေးနိုင်သည်နည်း",
        'km': "សាលូប! សូមស្វាគមន៍មកយុទ្ធសាលា Bantuan Support ។ ខ្ញុំអាចជួយអ្នកដោយរបៀបណា?",
        'lo': "ສະ​ບາຍ​ດີ! ຍິນ​ດີ​ຕ້ອນ​ຮັບ​ເข້າ​ສູ່​ Bantuan Support ຂ້ອຍ​ສາ​ມາດ​ຊ່ວຍ​ເຫຼື້ອ​ທ່ານ​ໃນ​ວັນ​ນີ້​ໂດຍ​ວິ​ທີ​ໃດ",
        'bn': "হ্যালো! Bantuan সাপোর্টে স্বাগতম। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?"
    }
    return greetings.get(language, greetings['en'])


def get_status_response(language: str) -> str:
    """Generate response to 'how are you' type questions"""
    responses = {
        'en': "I'm doing great, thank you for asking! I'm here and ready to assist you with any questions or support you need.",
        'id': "Saya baik-baik saja, terima kasih sudah bertanya! Saya siap membantu Anda dengan pertanyaan atau dukungan apa pun yang Anda butuhkan.",
        'ms': "Saya baik-baik saja, terima kasih telah bertanya! Saya siap membantu anda dengan sebarang soalan atau sokongan yang anda perlukan.",
        'th': "ฉันสบายดี ขอบคุณที่ถาม! ฉันพร้อมที่จะช่วยเหลือคำถามหรือการสนับสนุนใด ๆ ที่คุณต้องการ",
        'vi': "Tôi đang khỏe, cảm ơn vì đã hỏi! Tôi sẵn sàng giúp bạn với bất kỳ câu hỏi hoặc hỗ trợ nào bạn cần.",
        'tl': "Ako ay gumagana nang maayos, salamat sa pagtatanong! Handa akong tumulong sa iyo sa anumang katanungan o suporta na kailangan mo.",
        'my': "ကျွန်ုပ်ကောင်းမွန်နေပါသည် မေးမြန်းပေးသည့်အတွက် ကျေးဇူးပြု၍ အမှုတင်သည်။ ကျွန်ုပ်သည် သင့်အား မည်သည့်မေးခွန်း သို့မဟုတ် အကူအညီကို ကူညီပေးရန် အသင့်ရှိပါသည်။",
        'km': "ខ្ញុំស្ថិតក្នុងលក្ខណៈល្អ សូមគេង! ខ្ញុំត្រៀមខ្លួនដែលក្នុងក្រោយដែលដើម្បីផ្តល់ជូនលេខយុទ្ធសាលា ឬការរទប្បិទលម្អិតដែលអ្នកត្រូវការ។",
        'lo': "ຂ້ອຍສະບາຍດີ ຂອບໃຈທີ່ຖາມ! ຂ້ອຍພ້ອມທີ່ຈະຊ່ວຍເຫຼື້ອທ່ານກັບໂจ့ຕໍ່າໃດຕໍ່າຫລືຄວາມຊ່ວຍເຫຼື້ອໃດທີ່ທ່ານຕ້ອງການ",
        'bn': "আমি ভাল আছি, আপনার জন্য ধন্যবাদ! আমি আপনার যে কোনও প্রশ্ন বা সহায়তার জন্য সাহায্য করতে প্রস্তুত।"
    }
    return responses.get(language, responses['en'])


def get_appreciation_response(language: str) -> str:
    """Generate response to thanks/appreciation"""
    responses = {
        'en': "You're very welcome! I'm always happy to help. Is there anything else I can assist you with?",
        'id': "Dengan senang hati! Saya selalu senang membantu. Ada yang lain yang bisa saya bantu?",
        'ms': "Sama-sama! Saya selalu gembira membantu. Adakah perkara lain yang boleh saya bantu anda?",
        'th': "ยินดีมากครับ! ฉันยินดีที่จะช่วยเสมอ มีอะไรอื่นที่ฉันสามารถช่วยได้หรือไม่",
        'vi': "Không có gì! Tôi luôn vui lòng giúp đỡ. Có điều gì khác tôi có thể giúp bạn không?",
        'tl': "Malugod na tanggapin! Lagi akong masaya na tumulong. May iba pang alam mo na makakatulong?",
        'my': "များစွာ အလွမ်းမြတ်! ကျွန်ုပ်သည် အမြဲလျှင် ကူညီရန် ဝမ်းသာပါသည်။ ကျွန်ုပ်ကိုကူညီပေးနိုင်သည့် အခြားအရာများ ရှိပါသလား?",
        'km': "សូមស្វាគមន៍ច្រើន! ខ្ញុំពេលវេលាដែលហេមម័ត្ថ។ តើមានចាក់សក្ដនដែលទៀងទាត់ដែលខ្ញុំបង្គរលាម?",
        'lo': "ທ່ານໄດ້ຍິນທີ່ຮາກ! ຂ້ອຍ​ສະ​ນົ່ງ​ໆ​ດີ​ໃຈ​ທີ່​ຈະ​ຊ່ວຍ​ເຫຼື້ອ​ໃດ​ບາດ​ທີ່ອື່ນ​ທີ່ຂ້ອຍ​ສາ​ມາດ​ຊ່ວຍ​ເຫຼື້ອ​ທ່ານ​ໄດ້",
        'bn': "আপনার স্বাগত! আমি সর্বদা সাহায্য করতে খুশি। আর কিছু আছে যা আমি আপনাকে সাহায্য করতে পারি?"
    }
    return responses.get(language, responses['en'])


def get_goodbye_response(language: str) -> str:
    """Generate goodbye response"""
    responses = {
        'en': "Goodbye! Thank you for using Bantuan Support. Have a great day!",
        'id': "Sampai jumpa! Terima kasih telah menggunakan Dukungan Bantuan. Semoga hari Anda menyenangkan!",
        'ms': "Selamat tinggal! Terima kasih telah menggunakan Sokongan Bantuan. Semoga anda mempunyai hari yang bagus!",
        'th': "ลาก่อน! ขอบคุณที่ใช้ Bantuan Support มีวันที่ดี!",
        'vi': "Tạm biệt! Cảm ơn bạn đã sử dụng Hỗ trợ Bantuan. Có một ngày tuyệt vời!",
        'tl': "Paalam! Salamat sa paggamit ng Bantuan Support. Magkaroon ng magandang araw!",
        'my': "さようなら ကျွန်ုပ်သည် Bantuan Support ကိုအသုံးပြု၍ ကျေးဇူးပြု၍ မည်သည့်ကုန်ကျုံရေသည့် သည့် အခြားက္တ",
        'km': "សារលាដ! សូមស្វាគមន៍សម្រាប់ការប្រើប្រាស់ Bantuan Support ។ មានថ្ងៃដ៏ល្អ!",
        'lo': "ສະ​ບາຍ​ດີ​ ຂອບ​ໃຈ​ທີ່​ໃຊ້ Bantuan Support ມີ​ວັນ​ທີ່ ທີ່ດີ!",
        'bn': "বিদায়! Bantuan সাপোর্ট ব্যবহার করার জন্য আপনাকে ধন্যবাদ। দুর্দান্ত দিন থাকুক!"
    }
    return responses.get(language, responses['en'])


def get_help_response(category: str, language: str) -> str:
    """Generate help response based on category"""
    help_responses = {
        'technical': {
            'en': "I can help with technical issues! Please describe the problem you're experiencing, and I'll do my best to assist you.",
            'id': "Saya dapat membantu dengan masalah teknis! Silakan jelaskan masalah yang Anda alami, dan saya akan membantu Anda.",
            'ms': "Saya boleh membantu dengan masalah teknis! Sila terangkan masalah yang anda hadapi, dan saya akan membantu anda.",
        },
        'account': {
            'en': "I can help with account-related questions! What would you like to know about your account?",
            'id': "Saya dapat membantu dengan pertanyaan terkait akun! Apa yang ingin Anda ketahui tentang akun Anda?",
            'ms': "Saya boleh membantu dengan soalan berkaitan akaun! Apa yang anda ingin tahu tentang akaun anda?",
        },
        'billing': {
            'en': "I can assist with billing inquiries! Please let me know what information you need about your billing.",
            'id': "Saya dapat membantu dengan pertanyaan tagihan! Beri tahu saya informasi apa yang Anda butuhkan tentang penagihan Anda.",
            'ms': "Saya boleh membantu dengan pertanyaan pengebilan! Beritahu saya maklumat apa yang anda perlukan tentang pengebilan anda.",
        },
        'general': {
            'en': "I'm here to help! Please tell me what you need assistance with, and I'll do my best to support you.",
            'id': "Saya siap membantu! Beri tahu saya apa yang Anda butuhkan, dan saya akan melakukan yang terbaik untuk membantu Anda.",
            'ms': "Saya siap membantu! Beritahu saya apa yang anda perlukan, dan saya akan berusaha sebaik mungkin untuk membantu anda.",
        }
    }
    
    if category not in help_responses:
        category = 'general'
    
    return help_responses[category].get(language, help_responses[category]['en'])


def get_technical_response(message: str, language: str) -> str:
    """Generate technical support response"""
    responses = {
        'en': f"Thank you for reporting this technical issue: '{message[:50]}...'. I'm analyzing your request and will provide troubleshooting steps shortly. Please describe any error messages you see.",
        'id': f"Terima kasih telah melaporkan masalah teknis ini: '{message[:50]}...'. Saya menganalisis permintaan Anda dan akan memberikan langkah pemecahan masalah segera. Harap jelaskan pesan kesalahan apa pun yang Anda lihat.",
        'ms': f"Terima kasih telah melaporkan masalah teknis ini: '{message[:50]}...'. Saya menganalisis permintaan anda dan akan memberikan langkah penyelesaian masalah tidak lama lagi. Sila terangkan sebarang mesej ralat yang anda lihat.",
    }
    return responses.get(language, responses['en'])


def get_account_response(message: str, language: str) -> str:
    """Generate account support response"""
    responses = {
        'en': f"Regarding your account inquiry: '{message[:50]}...'. I can help you with account settings, profile information, and related matters. What specific information do you need?",
        'id': f"Mengenai pertanyaan akun Anda: '{message[:50]}...'. Saya dapat membantu Anda dengan pengaturan akun, informasi profil, dan hal-hal terkait. Informasi spesifik apa yang Anda butuhkan?",
        'ms': f"Mengenai pertanyaan akaun anda: '{message[:50]}...'. Saya boleh membantu anda dengan tetapan akaun, maklumat profil, dan perkara berkaitan. Maklumat khusus apa yang anda perlukan?",
    }
    return responses.get(language, responses['en'])


def get_billing_response(message: str, language: str) -> str:
    """Generate billing support response"""
    responses = {
        'en': f"Regarding your billing question: '{message[:50]}...'. I can assist with invoice details, payment methods, subscription plans, and billing inquiries. How can I help?",
        'id': f"Mengenai pertanyaan penagihan Anda: '{message[:50]}...'. Saya dapat membantu dengan detail faktur, metode pembayaran, rencana langganan, dan pertanyaan penagihan. Bagaimana saya bisa membantu?",
        'ms': f"Mengenai soalan pengebilan anda: '{message[:50]}...'. Saya boleh membantu dengan butiran invois, kaedah pembayaran, pelan langganan, dan pertanyaan pengebilan. Bagaimana saya boleh membantu?",
    }
    return responses.get(language, responses['en'])


def get_general_response(message: str, language: str) -> str:
    """Generate general response for any message"""
    responses = {
        'en': f"Thank you for your message: '{message[:50]}...'. I'm here to assist you. Could you provide more details about what you need help with?",
        'id': f"Terima kasih atas pesan Anda: '{message[:50]}...'. Saya siap membantu Anda. Bisakah Anda memberikan lebih detail tentang apa yang Anda butuhkan?",
        'ms': f"Terima kasih atas mesej anda: '{message[:50]}...'. Saya siap membantu anda. Bolehkah anda memberikan lebih banyak butiran tentang apa yang anda perlukan?",
        'th': f"ขอบคุณสำหรับข้อความของคุณ: '{message[:50]}...' ฉันพร้อมที่จะช่วยเหลือคุณ คุณสามารถให้รายละเอียดเพิ่มเติมเกี่ยวกับสิ่งที่คุณต้องการได้หรือไม่",
        'vi': f"Cảm ơn bạn về tin nhắn của bạn: '{message[:50]}...'. Tôi sẵn sàng giúp bạn. Bạn có thể cung cấp thêm chi tiết về những gì bạn cần giúp không?",
        'tl': f"Salamat sa iyong mensahe: '{message[:50]}...'. Ako ay handa na tumulong sa iyo. Mayroon kang magbigay ng higit pang detalye tungkol sa kung ano ang kailangan mo ng tulong?",
        'my': f"သင့်အမေးခွန်းအတွက် ကျေးဇူးပြု၍ '{message[:50]}...'. ကျွန်ုပ်သည် သင့်အား ကူညီရန် အသင့်ရှိပါသည်။ သင်မည်သည့်အရာ လိုအပ်သည်နှင့်ပတ်သက်။ သက်သက်ပိုမိုအသေးစိတ်ကို ပေးနိုင်ပါသလား?",
        'km': f"សូមស្វាគមន៍សម្រាប់សារ: '{message[:50]}...'. ខ្ញុំនឹងផ្តល់ជូនលេខយុទ្ធសាលា តើអ្នកនិយាយថាលម្អិតលម្អិតដែលបន្ថែមផ្សេងទៀតអំពីអ្វីដែលអ្នកត្រូវការលេខយុទ្ធសាលា?",
        'lo': f"ຂອບໃຈສໍາລັບຂໍ້ຄວາມຂອງທ່ານ: '{message[:50]}...'. ຂ້ອຍພ້ອມທີ່ຈະຊ່ວຍເຫຼື້ອທ່ານ ທ່ານສາມາດໃຫ້ລາຍລະອຽດເພີ່ມເຕີມກ່ຽວກັບສິ່ງທີ່ທ່ານຕ້ອງການຄວາມຊ່ວຍເຫຼື້ອໃດ",
        'bn': f"আপনার বার্তার জন্য ধন্যবাদ: '{message[:50]}...' আমি আপনাকে সাহায্য করতে প্রস্তুত। আপনি কী সাহায্যের প্রয়োজন সে সম্পর্কে আরও বিশদ তথ্য দিতে পারেন?"
    }
    return responses.get(language, responses['en'])


def get_fallback_response(language: str) -> str:
    """
    Get fallback response if Azure AI Foundry is not available
    This is used when the AI service is not configured or experiences errors
    """
    fallback_messages = {
        'en': "I apologize, but I'm currently unable to process your request through AI Foundry. Please try again later or contact support.",
        'id': "Saya minta maaf, tetapi saya saat ini tidak dapat memproses permintaan Anda melalui AI Foundry. Silakan coba lagi nanti atau hubungi dukungan.",
        'ms': "Saya minta maaf, tetapi saya saat ini tidak dapat memproses permintaan anda melalui AI Foundry. Sila cuba lagi nanti atau hubungi sokongan.",
        'th': "ขอโทษ แต่ฉันไม่สามารถประมวลผลคำขอของคุณผ่าน AI Foundry ได้ในขณะนี้ โปรดลองใหม่ภายหลังหรือติดต่อการสนับสนุน",
        'vi': "Tôi xin lỗi, nhưng hiện tại tôi không thể xử lý yêu cầu của bạn qua AI Foundry. Vui lòng thử lại sau hoặc liên hệ với bộ phận hỗ trợ.",
        'tl': "Humingi ako ng patawad, ngunit hindi ko makakagawa ang iyong kahilingan sa pamamagitan ng AI Foundry sa kasalukuyan. Mangyaring subukan ulit mamaya o makipag-ugnayan sa suporta.",
        'my': "ကျွန်ုပ်သည် နှိမ့်ချပြန်လည်တောင်းခံပါသည်။ သို့သော်ကျွန်ုပ်သည် လက်ရှိတွင် AI Foundry မှတစ်ဆင့် သင့်အမေးခွန်းကို ပြုပြင်နိုင်မည်မဟုတ်ပါ။ နောက်ပိုင်းတွင် ထပ်မံစာကြောင်းသို့မဟုတ် ကျေးဇူးပြုတောင်းခံပါ။",
        'km': "សូមលាង ប៉ុន្តែខ្ញុំមិនអាចដំណើរការសូលិចរបស់អ្នកតាមរយៈ AI Foundry បានទេ។ សូមព្យាយាមម្តងទៀតក្រោយមក ឬទាក់ទងការគាំទ។",
        'lo': "ຂ້ອຍຂໍໂທດ, ແຕ່ຂ້ອຍບໍ່ສາມາດປະມວນຜົນຂໍ້ຮ້ອງຂໍຂອງທ່ານຜ່ານ AI Foundry ໄດ້ໃນປະຈຸບັນ. ກະລຸນາລອງໃຫມ່ກໍ່ຕໍ່ໄປ ຫລື ຕິດຕໍ່ສະ ບປ.",
        'bn': "আমি ক্ষমা চাইছি, কিন্তু আমি এখন AI Foundry এর মাধ্যমে আপনার অনুরোধ প্রক্রিয়া করতে পারছি না। অনুগ্রহ করে পরে আবার চেষ্টা করুন বা সহায়তার সাথে যোগাযোগ করুন।"
    }
    return fallback_messages.get(language, fallback_messages['en'])


@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get list of available AI models"""
    try:
        models = [
            {
                'id': 'default',
                'name': 'Default AI Model',
                'description': 'Default AI Foundry model for support',
                'languages': ['en', 'id', 'ms', 'th', 'vi', 'tl', 'my', 'km', 'lo', 'bn']
            }
        ]
        return jsonify({
            'status': 'success',
            'models': models
        }), 200
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        return jsonify({'error': 'Failed to fetch models'}), 500


@app.route('/api/languages', methods=['GET'])
def get_supported_languages():
    """Get list of supported languages"""
    languages = {
        'en': 'English',
        'id': 'Bahasa Indonesia',
        'ms': 'Bahasa Malaysia',
        'th': 'ไทย (Thai)',
        'vi': 'Tiếng Việt',
        'tl': 'Filipino',
        'my': 'မြန်မာ (Myanmar)',
        'km': 'ខ្មែរ (Khmer)',
        'lo': 'ລາວ (Lao)',
        'bn': 'বাংলা (Bengali)'
    }
    return jsonify({
        'status': 'success',
        'languages': languages
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Run the app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    logger.info(f"Starting Bantuan Backend on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
