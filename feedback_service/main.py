from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncmy
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uvicorn
import logging



# Создаём логгер для main.py
LOGGER = logging.getLogger("main")
LOGGER.setLevel(logging.INFO)

# Создаём папку logs, если её ещё нет
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Файл для логов main в папке logs
log_file = os.path.join(log_dir, "main.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

LOGGER.addHandler(file_handler)




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
    feedback: str
    user_id: int  # Добавляем обязательное поле

async def get_db_connection():
    try:
        conn = await asyncmy.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'feedback_user'),
            password=os.getenv('DB_PASSWORD', ''),
            db=os.getenv('DB_NAME', 'feedback_db'),
        )
        LOGGER.info("Database connection established successfully")
        return conn
    except Exception as e:
        LOGGER.error(f"Database connection failed: {str(e)}")
        return None


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
        LOGGER.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        """if conn is not None:  # Проверяем, что соединение было создано
            await conn.close()"""

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

if __name__ == "__main__":
    LOGGER.info("uvicorn is run on host='0.0.0.0', port=8001;  reload=True")
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)