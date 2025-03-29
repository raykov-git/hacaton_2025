from ClinicBot import ClinicBot
from fastapi import FastAPI, Form, Request  
import logging
import uvicorn
import os
from pydantic import BaseModel

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

# Эндпоинт для GET-запроса "/help"
@app.get("/help")
def get_help():
    LOGGER.info("эндпоинт /help выполнен")
    return {"response": bot.help()}


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
        "timestamp": "2025-03-31T12:00:00Z"
    }



class RequestModel(BaseModel):
    question: str


# Описание: Принимает вопрос, возвращает ответ
@app.post("/qa")
async def process_message(request: RequestModel):
    proces_time = 0 # время обработки запроса
    reply = bot.process_message(request.question)
    LOGGER.info("эндпоинт /qa выполнен")
    return{
        "answer": reply,
        "processing_time": proces_time
    }


if __name__ == "__main__":
    LOGGER.info("uvicorn is run on host='0.0.0.0', port=8000;  reload=True")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)