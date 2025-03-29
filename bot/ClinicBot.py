import logging
from gigachat import GigaChat
import os
import sys
from pathlib import Path
from llm.create_prompt import *

# Добавляем корень проекта в PYTHONPATH
root_dir = Path(__file__).parent.parent  # Поднимаемся на два уровня вверх
sys.path.append(str(root_dir))

# Создаём логгер для clinicBot.py
LOGGER = logging.getLogger("clinic_bot")
LOGGER.setLevel(logging.INFO)

# Создаём папку logs, если её ещё нет
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Файл для логов clinicBot.py в папке logs
log_file = os.path.join(log_dir, "clinic_bot.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

LOGGER.addHandler(file_handler)


class ClinicBot:

    def __init__(self):
        # self.model = whisper.load_model("small")
        # logging.info(f"Using device: {self.device}")

        # TODO скрапер по api при инициализации и спустя время

        pass

    def help(self):
        return "Этот бот может..."
    

    def root(self):
        return "Добро пожаловать в ClinicBot API!"
    

    def get_all_doctors(self):
        return "Вот список докторов..."
    

    def get_doctor(self):
        return "Вот информация о докторе..."
    

    def add_doctor(self, name, specialty):
        return f"добавили доктора {name} со специальностью {specialty}"
   

    def get_answer_from_llm(self, user_text):

        result = find_similar_context(user_text, knowledge_base)
        LOGGER.info(result[0].get('type', 'unknown'),)
        prompt = []

        if create_prompt(result[0].get('type', 'unknown'), user_text, prompt):
            LOGGER.info(f"НАШ ПРОМПТ{prompt[0]}")
            # Для авторизации запросов используйте ключ, полученный в проекте GigaChat API
            with GigaChat(credentials=
                          "MzNjMzFhOWQtMWQzOS00OWI3LTkxYTMtMDU1NWJkMGUyYTFkOmI5Njg3MDZlLWIwZDctNDY3MS05YjY3LWVmNjI1NjM3MzA3NQ==", 
                        verify_ssl_certs=False, model="GigaChat-Max") as giga:
                response = giga.chat(prompt[0])

            return "Ответ от llm:" + "\n" + response.choices[0].message.content
        else:
            LOGGER.info('Извините, не корректный промпт')
            return('Извините, не корректный промпт')


    def process_message(self, user_text):
        if not user_text:
            LOGGER.error("бот не получил текст")
            return "бот не получил текст"
        
        if False:
            LOGGER.info("повторение текста пользователя")
            return "Вот Ваш запрос:\n" + user_text
        else:
            LOGGER.info("LLM ответ пользователю")
            #return("LLM ответ пользователю")
            return(user_text + "\n" + self.get_answer_from_llm(user_text))
        