#!/usr/bin/env node

/**
 * Скрипт настройки веб-сервера
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

console.log(`
╔════════════════════════════════════════╗
║     Настройка веб-сервера              ║
║     Verification System                ║
╚════════════════════════════════════════╝
`);

// Проверка существующих файлов
const filesToCheck = [
    '.env',
    'package.json',
    'server.js'
];

console.log('📁 Проверка файлов...');
filesToCheck.forEach(file => {
    if (fs.existsSync(file)) {
        console.log(`  ✓ ${file}`);
    } else {
        console.log(`  ✗ ${file} - не найден`);
    }
});

// Создание необходимых директорий
const directories = [
    'public',
    'public/css',
    'public/js',
    'public/images',
    'data',
    'logs'
];

console.log('\n📁 Создание директорий...');
directories.forEach(dir => {
    const dirPath = path.join(__dirname, dir);
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
        console.log(`  ✓ Создана: ${dir}`);
    } else {
        console.log(`  ✓ Уже существует: ${dir}`);
    }
});

// Создание .env файла если нет
if (!fs.existsSync('.env')) {
    console.log('\n🔧 Создание .env файла...');
    
    const envContent = `# Server Configuration
PORT=3000
NODE_ENV=development

# Security
API_SECRET=${require('crypto').randomBytes(32).toString('hex')}
SESSION_SECRET=${require('crypto').randomBytes(32).toString('hex')}

# Telegram Bot Integration
BOT_WEBHOOK_URL=http://localhost:8080/webhook
BOT_API_SECRET=${require('crypto').randomBytes(32).toString('hex')}

# Logging
LOG_LEVEL=info
LOG_FILE=logs/server.log
`;
    
    fs.writeFileSync('.env', envContent);
    console.log('  ✓ .env файл создан с случайными ключами безопасности');
}

// Проверка зависимостей
console.log('\n📦 Проверка зависимостей...');
try {
    const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    console.log(`  ✓ package.json загружен (${packageJson.name} v${packageJson.version})`);
    
    if (fs.existsSync('node_modules')) {
        console.log('  ✓ node_modules существует');
    } else {
        console.log('  ⚠ node_modules не найден. Запустите: npm install');
    }
} catch (error) {
    console.log('  ✗ Ошибка чтения package.json:', error.message);
}

console.log('\n✅ Настройка завершена!');
console.log('\nСледующие шаги:');
console.log('1. Установите зависимости: npm install');
console.log('2. Запустите сервер: npm start');
console.log('3. Откройте в браузере: http://localhost:3000');
console.log('\nДля разработки: npm run dev');

rl.close();
