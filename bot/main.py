from ClinicBot import ClinicBot
from fastapi import FastAPI, Form, Request  
import logging
import uvicorn
import os
from pydantic import BaseModel
from datetime import datetime
import time

# Создаём логгер для main.py
LOGGER = logging.getLogger("main")
LOGGER.setLevel(logging.INFO)

# Создаём папку logs, если её ещё нет
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Файл для логов clinicBot.py в папке logs
log_file = os.path.join(log_dir, "main.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

LOGGER.addHandler(file_handler)

bot = ClinicBot()
app = FastAPI()

# Корневой эндпоинт
@app.get("/api")
def api():      
    LOGGER.info("эндпоинт /api выполнен")
    return {"answer": bot.api()}


# здоровье... бота?
@app.get("/health")
def health():
    LOGGER.info("эндпоинт /health выполнен")
    return {
        "status": "ok",
        "timestamp": datetime.now()
    }


class RequestModel(BaseModel):
    question: str


@app.post("/qa")
async def process_message(request: RequestModel):
    """
    Description:
        эндпоинт для вопроса боту
    Args:
        param1 json с вопросом question
    
    Returns:
        type: json с ответом
    """
    start = time.perf_counter()  # Точный счетчик времени
    reply = bot.process_message(request.question)
    LOGGER.info("эндпоинт /qa выполнен")
    end = time.perf_counter()
    return{
        "answer": reply,
        "processing_time": end - start
    }


if __name__ == "__main__":
    LOGGER.info("uvicorn is run on host='0.0.0.0', port=8000;  reload=True")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)