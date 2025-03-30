CREATE DATABASE feedback_db;
USE feedback_db;

CREATE TABLE feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    feedback_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем пользователя для микросервиса
CREATE USER 'feedback_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON feedback_db.* TO 'feedback_user'@'localhost';
FLUSH PRIVILEGES;


USE feedback_db;
SELECT * FROM feedbacks;