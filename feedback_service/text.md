Вот пошаговая инструкция для настройки локальной базы данных MySQL и FastAPI микросервиса на **Windows**:

---

## 1. Установка MySQL на Windows

### 1.1. Скачивание и установка
1. Перейдите на [официальный сайт MySQL](https://dev.mysql.com/downloads/installer/)
2. Скачайте **MySQL Installer** (рекомендуется версия ≥8.0)
3. Запустите установщик и выберите:
   - Тип установки: **Custom**
   - Из списка компонентов добавьте:
     - **MySQL Server**
     - **MySQL Workbench** (GUI для управления БД - опционально)

### 1.2. Настройка сервера
1. В мастере настройки укажите:
   - **Standalone MySQL Server**
   - Тип конфигурации: **Development Computer**
   - Метод аутентификации: **Use Strong Password Encryption**
   - Задайте **root-пароль** (запомните его!)
2. Завершите установку.

### 1.3. Проверка работы MySQL
1. Откройте командную строку (**cmd**):
   ```bash
   mysql -u root -p
   ```
2. Введите пароль. Если видите приветствие MySQL — сервер работает.

---

## 2. Создание базы данных и таблицы

1. В той же командной строке MySQL выполните:
   ```sql
   CREATE DATABASE feedback_db;
   USE feedback_db;

   CREATE TABLE feedbacks (
       id INT AUTO_INCREMENT PRIMARY KEY,
       user_id BIGINT NOT NULL,
       feedback_text TEXT NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   -- Создаем пользователя для микросервиса
   CREATE USER 'feedback_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON feedback_db.* TO 'feedback_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
   Где `your_password` — замените на свой пароль.

---

## 3. Настройка FastAPI микросервиса

### 3.1. Подготовка окружения
1. Создайте папку для проекта, например `feedback_service`.
2. Откройте VS Code (или другой редактор) в этой папке.
3. Создайте файл `requirements.txt`:
   ```
   fastapi
   uvicorn
   python-dotenv
   asyncmy
   ```
4. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

### 3.2. Настройка `.env`
Создайте файл `.env` в корне проекта:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=feedback_user
DB_PASSWORD=your_password  # тот, что задали при создании пользователя
DB_NAME=feedback_db
```

### 3.3. Код микросервиса (`main.py`)
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncmy
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Разрешаем запросы с любых источников (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Feedback(BaseModel):
    user_id: int
    feedback: str

async def get_db_connection():
    return await asyncmy.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
    )

@app.post("/feedback")
async def add_feedback(fb: Feedback):
    conn = None
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO feedbacks (user_id, feedback_text) VALUES (%s, %s)",
                (fb.user_id, fb.feedback)
            )
        await conn.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()

@app.get("/feedbacks")
async def get_feedbacks():
    conn = None
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM feedbacks")
            feedbacks = await cursor.fetchall()
            return {"feedbacks": feedbacks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()
```

---

## 4. Запуск микросервиса

1. Откройте терминал в папке проекта.
2. Выполните:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
3. Сервис будет доступен по:  
   - Документация API: http://localhost:8000/docs  
   - Список отзывов: http://localhost:8000/feedbacks

---

## 5. Интеграция с Telegram ботом

Модифицируйте обработчик отзывов в боте:

```python
import aiohttp

FEEDBACK_SERVICE_URL = "http://localhost:8000"  # URL вашего локального сервиса

async def handle_feedback(message: Message, state: FSMContext):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{FEEDBACK_SERVICE_URL}/feedback",
                json={
                    "user_id": message.from_user.id,
                    "feedback": message.text
                }
            ) as resp:
                if resp.status == 200:
                    await message.reply("✅ Спасибо за отзыв!")
                else:
                    error = await resp.text()
                    await message.reply("❌ Ошибка при сохранении отзыва.")
    except Exception as e:
        await message.reply("⚠️ Сервис отзывов временно недоступен.")
        print(f"Ошибка: {e}")
    finally:
        await state.clear()
```

---

## 6. Проверка работы

1. Отправьте отзыв через бота.
2. Проверьте сохранение:
   - Через браузер: http://localhost:8000/feedbacks
   - Или в MySQL:
     ```sql
     USE feedback_db;
     SELECT * FROM feedbacks;
     ```

---

## Дополнительные советы для Windows

1. **Если MySQL не запускается**:
   - Проверьте службу MySQL в `Панель управления -> Администрирование -> Службы`.
   - Или запустите вручную:
     ```bash
     net start mysql
     ```

2. **Для визуального управления БД**:
   - Установите **MySQL Workbench** (был в установщике).
   - Подключитесь к `localhost` с логином `root` и вашим паролем.

3. **Если порт 8000 занят**:
   Измените порт в команде запуска:
   ```bash
   uvicorn main:app --reload --port 8001
   ```

4. **Для отладки**:
   - Логи FastAPI будут выводиться в консоль.
   - Проверяйте ошибки подключения к MySQL через Workbench.

Теперь у вас есть полностью рабочая система на Windows для сбора отзывов через Telegram бот с отдельным API сервисом!