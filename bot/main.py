from ClinicBot import ClinicBot
from fastapi import FastAPI, Form, Request  
import logging
import uvicorn
import os
from pydantic import BaseModel


"""# Создаём логгер для main.py
LOGGER = logging.getLogger("main")
LOGGER.setLevel(logging.INFO)

# Файл для логов main.py
file_handler = logging.FileHandler("main.log", encoding="utf-8", mode="a")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

LOGGER.addHandler(file_handler)"""


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


"""# что это?
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)"""


@app.get("/doctors")
def get_doctors():
    return {"doctors": bot.get_all_doctors()}


@app.post("/some_doctor")
async def add_doctor(
    name: str = Form(...),  # Указываем, что параметр приходит из формы
    specialty: str = Form(...)
):
    return {"status": f"Добавлен доктор {name}, специальность: {specialty}"}


# как выбрать, про какого докторя я хочу узнать
@app.get("/doctor")
def get_doctors():
    return {"doctors": bot.get_doctor()}


# Эндпоинт для GET-запроса "/help"
@app.get("/help")
def get_help():
    return {"response": bot.help()}


# Корневой эндпоинт
@app.get("/")
def read_root():
    return {"message": bot.root()}


class RequestModel(BaseModel):
    message: str

@app.post("/process_message")
async def process_message(request: RequestModel):
    reply = bot.process_message(request.message)
    LOGGER.info("/process_message выполнен")
    return {
        "response": {
            "text": reply,
            "end_session": False
        },
        "version": "1.0"
    }


if __name__ == "__main__":
    LOGGER.info("uvicorn is run on host='0.0.0.0', port=8000;  reload=True")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)