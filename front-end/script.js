// DOM Elements with error handling
let chatMessages, messageInput, sendBtn, voiceBtn, clearChat, downloadChat, languageSelect, categoryBtns;

// State
let currentLanguage = 'en';
let currentCategory = 'general';
let isListening = false;
let recognition = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    try {
        chatMessages = document.getElementById('chatMessages');
        messageInput = document.getElementById('messageInput');
        sendBtn = document.getElementById('sendBtn');
        voiceBtn = document.getElementById('voiceBtn');
        clearChat = document.getElementById('clearChat');
        downloadChat = document.getElementById('downloadChat');
        languageSelect = document.getElementById('languageSelect');
        categoryBtns = document.querySelectorAll('.category-btn');
        
        if (!chatMessages || !messageInput) {
            throw new Error('Required DOM elements not found. Check that index.html is properly loaded.');
        }
        
        initializeApp();
    } catch (error) {
        console.error('Failed to initialize Bantuan Bot:', error);
        document.body.innerHTML = '<div style="padding: 2rem; color: red; font-size: 1.2rem;">Error loading application. Please check the browser console.</div>';
    }
});

function initializeApp() {
    try {
        setupEventListeners();
        setupSpeechRecognition();
        updateChatPlaceholder();
        
        // Focus on input for better UX
        if (messageInput) {
            messageInput.focus();
        }
        
        console.log('🚀 Bantuan Support Bot initialized successfully!');
        console.log('📍 Current environment: ' + (window.location.hostname || 'localhost'));
    } catch (error) {
        console.error('Error during initialization:', error);
    }
}

function setupEventListeners() {
    try {
        // Send message events
        if (sendBtn) sendBtn.addEventListener('click', handleSendMessage);
        if (messageInput) messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
            }
        });

        // Voice input
        if (voiceBtn) voiceBtn.addEventListener('click', toggleVoiceRecognition);

        // Clear chat
        if (clearChat) clearChat.addEventListener('click', handleClearChat);

        // Download chat
        if (downloadChat) downloadChat.addEventListener('click', handleDownloadChat);

        // Language selection
        if (languageSelect) languageSelect.addEventListener('change', handleLanguageChange);

        // Category selection
        if (categoryBtns && categoryBtns.length > 0) {
            categoryBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    handleCategoryChange(this.dataset.category, this);
                });
            });
        }

        // Auto-resize input
        if (messageInput) {
            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            });
        }
    } catch (error) {
        console.error('Error setting up event listeners:', error);
    }
}

function setupSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = getLanguageCode(currentLanguage);

        recognition.onstart = function() {
            isListening = true;
            voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
            voiceBtn.style.background = 'var(--error)';
            showStatusMessage('Listening... Speak now');
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            messageInput.value = transcript;
            messageInput.focus();
        };

        recognition.onend = function() {
            isListening = false;
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            voiceBtn.style.background = '';
            hideStatusMessage();
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            showStatusMessage('Voice recognition error. Please try again.', 'error');
            setTimeout(hideStatusMessage, 3000);
        };
    } else {
        voiceBtn.style.display = 'none';
        console.warn('Speech recognition not supported in this browser');
    }
}

function handleSendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage('user', message);
    
    // Clear input
    messageInput.value = '';
    messageInput.style.height = 'auto';

    // Show loading indicator
    showStatusMessage('Processing your request...', 'info');

    // Call backend API
    sendMessageToBackend(message);
}

async function sendMessageToBackend(message) {
    try {
        // Determine backend API endpoint
        const apiEndpoint = getApiEndpoint();
        const fullUrl = `${apiEndpoint}/api/chat`;
        
        console.log('📤 Sending message to backend:', {
            url: fullUrl,
            message: message,
            language: currentLanguage,
            category: currentCategory
        });
        
        const response = await fetch(fullUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                language: currentLanguage,
                category: currentCategory
            })
        });

        console.log('📥 Backend response status:', response.status, response.statusText);

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('📨 Backend response data:', data);
        
        if (data.status === 'success') {
            hideStatusMessage();
            addMessage('bot', data.response);
        } else {
            throw new Error(data.error || 'Unknown error from API');
        }
    } catch (error) {
        console.error('❌ Error communicating with backend:', error);
        hideStatusMessage();
        showStatusMessage(`Error: ${error.message}`, 'error');
        // Fallback to local response if API fails
        setTimeout(() => {
            const fallbackResponse = generateBotResponse(message);
            addMessage('bot', fallbackResponse);
        }, 1000);
    }
}

function getApiEndpoint() {
    // Determine API endpoint based on environment
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // If opening index.html as file:// (local file), try localhost backend
    if (protocol === 'file:') {
        return 'http://localhost:5000';
    }
    
    // If running on localhost server, use localhost backend
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:5000';
    }
    
    // If running on Azure Static Web App, use the separate backend Web App
    // This is the Flask app running on Azure App Service
    if (hostname.includes('azurestaticapps.net')) {
        return 'https://bantuan-bjgjgwgrhmcwetah.australiaeast-01.azurewebsites.net';
    }
    
    // Fallback: check sessionStorage for custom backend URL
    const backendUrl = sessionStorage.getItem('backendUrl');
    if (backendUrl) {
        return backendUrl;
    }
    
    // Default fallback
    return `${protocol}//${hostname}`;
}

function addMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const header = document.createElement('div');
    header.className = 'message-header';
    
    const senderSpan = document.createElement('span');
    senderSpan.className = 'message-sender';
    senderSpan.textContent = sender === 'bot' ? 'Bantuan Bot' : 'You';
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = new Date().toLocaleTimeString();
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;
    
    header.appendChild(senderSpan);
    header.appendChild(timeSpan);
    content.appendChild(header);
    content.appendChild(messageText);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function generateBotResponse(userMessage) {
    const responses = {
        general: [
            `I understand you need help. Based on your message "${userMessage}", I'm here to assist you. What specific issue are you experiencing?`,
            `Thank you for reaching out! I've noted your concern about "${userMessage}". Let me help you resolve this step by step.`,
            `I see you mentioned "${userMessage}". I'm processing this in ${getLanguageName(currentLanguage)} and will provide the best assistance possible.`
        ],
        technical: [
            `I can help with technical issues. Regarding "${userMessage}", let me walk you through some troubleshooting steps.`,
            `Technical support activated! For the issue "${userMessage}", I recommend we start with basic diagnostics.`,
            `I understand you're experiencing technical difficulties with "${userMessage}". Let's solve this together.`
        ],
        account: [
            `I can assist with account-related inquiries. About "${userMessage}", I'll need to verify some information first.`,
            `For account issues like "${userMessage}", I can guide you through the resolution process securely.`,
            `Account support here! I see your concern about "${userMessage}". Let me help you with that.`
        ],
        billing: [
            `I can help with billing questions. Regarding "${userMessage}", let me provide you with the relevant information.`,
            `For billing inquiries about "${userMessage}", I can assist you with explanations and next steps.`,
            `Billing support activated! I understand your question about "${userMessage}". Let me clarify this for you.`
        ]
    };

    const categoryResponses = responses[currentCategory] || responses.general;
    const randomResponse = categoryResponses[Math.floor(Math.random() * categoryResponses.length)];
    
    return randomResponse;
}

function toggleVoiceRecognition() {
    if (!recognition) {
        showStatusMessage('Voice recognition not supported in this browser', 'error');
        setTimeout(hideStatusMessage, 3000);
        return;
    }

    if (isListening) {
        recognition.stop();
    } else {
        recognition.lang = getLanguageCode(currentLanguage);
        recognition.start();
    }
}

function handleClearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-sender">Bantuan Bot</span>
                        <span class="message-time">Just now</span>
                    </div>
                    <div class="message-text">
                        Hello! I'm Bantuan, your multi-lingual support assistant. I can help you in multiple ASEAN languages. How can I assist you today?
                    </div>
                </div>
            </div>
        `;
        showStatusMessage('Chat cleared successfully', 'success');
        setTimeout(hideStatusMessage, 2000);
    }
}

function handleDownloadChat() {
    const messages = chatMessages.querySelectorAll('.message');
    let chatLog = `Bantuan Support Chat Log\n`;
    chatLog += `Generated: ${new Date().toLocaleString()}\n`;
    chatLog += `Language: ${getLanguageName(currentLanguage)}\n`;
    chatLog += `Category: ${currentCategory}\n`;
    chatLog += `${'='.repeat(50)}\n\n`;

    messages.forEach(message => {
        const sender = message.querySelector('.message-sender').textContent;
        const time = message.querySelector('.message-time').textContent;
        const text = message.querySelector('.message-text').textContent;
        
        chatLog += `[${time}] ${sender}:\n${text}\n\n`;
    });

    const blob = new Blob([chatLog], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bantuan-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);

    showStatusMessage('Chat log downloaded successfully', 'success');
    setTimeout(hideStatusMessage, 2000);
}

function handleLanguageChange() {
    currentLanguage = languageSelect.value;
    updateChatPlaceholder();
    
    // Update speech recognition language
    if (recognition) {
        recognition.lang = getLanguageCode(currentLanguage);
    }
    
    addMessage('bot', `Language changed to ${getLanguageName(currentLanguage)}. How can I help you?`);
}

function handleCategoryChange(category, btnElement) {
    currentCategory = category;
    
    // Update active button
    categoryBtns.forEach(btn => btn.classList.remove('active'));
    btnElement.classList.add('active');
    
    const categoryName = btnElement.textContent.trim();
    addMessage('bot', `Switched to ${categoryName} support. What can I help you with?`);
}

function updateChatPlaceholder() {
    const placeholders = {
        en: 'Type your message here... (Press Enter to send)',
        id: 'Ketik pesan Anda di sini... (Tekan Enter untuk mengirim)',
        ms: 'Taip mesej anda di sini... (Tekan Enter untuk hantar)',
        th: 'พิมพ์ข้อความของคุณที่นี่... (กด Enter เพื่อส่ง)',
        vi: 'Nhập tin nhắn của bạn tại đây... (Nhấn Enter để gửi)',
        tl: 'I-type ang inyong mensahe dito... (Pindutin ang Enter para ipadala)',
        my: 'သင့်စာကိုဤနေရာတွင်ရိုက်ပါ... (ပို့ရန် Enter ကိုနှိပ်ပါ)',
        km: 'បញ្ចូលសាររបស់អ្នកនៅទីនេះ... (ចុច Enter ដើម្បីផ្ញើ)',
        lo: 'ພິມຂໍ້ຄວາມຂອງທ່ານທີ່ນີ້... (ກົດ Enter ເພື່ອສົ່ງ)',
        bn: 'এখানে আপনার বার্তা টাইপ করুন... (পাঠাতে Enter চাপুন)'
    };
    
    messageInput.placeholder = placeholders[currentLanguage] || placeholders.en;
}

function getLanguageName(code) {
    const languages = {
        en: 'English',
        id: 'Bahasa Indonesia',
        ms: 'Bahasa Malaysia',
        th: 'ไทย (Thai)',
        vi: 'Tiếng Việt',
        tl: 'Filipino',
        my: 'မြန်မာ (Myanmar)',
        km: 'ខ្មែរ (Khmer)',
        lo: 'ລາວ (Lao)',
        bn: 'বাংলা (Bengali)'
    };
    
    return languages[code] || 'Unknown';
}

function getLanguageCode(code) {
    const speechCodes = {
        en: 'en-US',
        id: 'id-ID',
        ms: 'ms-MY',
        th: 'th-TH',
        vi: 'vi-VN',
        tl: 'tl-PH',
        my: 'my-MM',
        km: 'km-KH',
        lo: 'lo-LA',
        bn: 'bn-BD'
    };
    
    return speechCodes[code] || 'en-US';
}

function showStatusMessage(message, type = 'info') {
    // Remove existing status message
    const existingStatus = document.querySelector('.status-message');
    if (existingStatus) {
        existingStatus.remove();
    }
    
    const statusDiv = document.createElement('div');
    statusDiv.className = 'status-message';
    statusDiv.textContent = message;
    
    const colors = {
        success: 'var(--success)',
        error: 'var(--error)',
        warning: 'var(--warning)',
        info: 'var(--accent-primary)'
    };
    
    statusDiv.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${colors[type] || colors.info};
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
        box-shadow: var(--shadow-lg);
    `;
    
    document.body.appendChild(statusDiv);
}

function hideStatusMessage() {
    const statusMessage = document.querySelector('.status-message');
    if (statusMessage) {
        statusMessage.style.animation = 'slideOut 0.3s ease-out forwards';
        setTimeout(() => statusMessage.remove(), 300);
    }
}

// Add slideOut animation to CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(100%); }
    }
`;
document.head.appendChild(style);

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to clear chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        handleClearChat();
    }
    
    // Ctrl/Cmd + S to download chat
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleDownloadChat();
    }
    
    // Escape to stop voice recognition
    if (e.key === 'Escape' && isListening) {
        recognition.stop();
    }
});

console.log('🤖 Bantuan Support Bot loaded successfully!');
console.log('💡 Keyboard shortcuts:');
console.log('  • Ctrl/Cmd + K: Clear chat');
console.log('  • Ctrl/Cmd + S: Download chat');
console.log('  • Enter: Send message');
console.log('  • Escape: Stop voice recognition');