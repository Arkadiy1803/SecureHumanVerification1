// Добавить в начало server.js
const mysql = require('mysql2/promise');

// MySQL соединение
const pool = mysql.createPool({
  host: process.env.DB_HOST || 'gondola.proxy.rlwy.net',
  port: process.env.DB_PORT || 15465,
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || 'QWGJtSPaTMCjODrfySWkTyHyxHzYwEDM',
  database: process.env.DB_NAME || 'railway',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  ssl: { rejectUnauthorized: false }
});

// Инициализация таблиц
async function initDatabase() {
  try {
    const connection = await pool.getConnection();
    
    // Создание таблиц
    await connection.execute(`
      CREATE TABLE IF NOT EXISTS verification_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        token VARCHAR(64) UNIQUE,
        telegram_id BIGINT,
        status ENUM('pending', 'completed', 'expired') DEFAULT 'pending',
        ip_address VARCHAR(45),
        user_agent TEXT,
        collected_data JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP NULL,
        INDEX idx_token (token),
        INDEX idx_telegram (telegram_id)
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    `);
    
    console.log('MySQL таблицы инициализированы');
    connection.release();
  } catch (error) {
    console.error('Ошибка инициализации БД:', error);
  }
}

// Вызвать инициализацию при старте
initDatabase();
