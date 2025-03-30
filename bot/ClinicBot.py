import logging
from gigachat import GigaChat
import os
import sys
from pathlib import Path
from llm.create_prompt import *
import scraper
from apscheduler.schedulers.background import BackgroundScheduler
from abstractBot import AbstractBot

# TODO пути

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


class ClinicBot(AbstractBot):

    def __init__(self):
        super().__init__()
        LOGGER.info("Запуск бота")
        self.scheduler = BackgroundScheduler()
        # Запускать сразу + раз в сутки
        self.scheduler.add_job(self.run_scraper, 'interval', days=1)
        self.scheduler.start()
        # Ручной запуск при старте
        self.run_scraper()

    def run_scraper(self):
        try:
            scraper.main()
            LOGGER.info("Скраппер успешно выполнен")
        except Exception as e:
            LOGGER.error(f"Ошибка скрапера: {e}")
    

    def api(self):
        return "Здравствуйте! Вы обратились в чат-бот поликлиники. " \
        "Мы готовы ответить на ваши вопросы и помочь с записью к врачу, " \
        "информацией о расписании работы специалистов, " \
        "а также предоставить данные о необходимых документах и услугах нашей клиники. " \
        "Пожалуйста, уточните ваш вопрос или просьбу."



    def get_answer_from_llm(self, user_text):

        result = find_similar_context(user_text, knowledge_base)
        LOGGER.info(result[0].get('type', 'unknown'),)
        LOGGER.info(result[0].get('similarity', 'unknown'),)
        confidence  = result[0].get('is_confident', 'unknown')
        
        if(confidence == False):
            return ('Извините, я вас не понимаю. Попробуйте изменить запрос.')

        if result[0].get('type', 'unknown') == "feedback":
            return("Спасибо за ваш отзыв")
        
        # MzNjMzFhOWQtMWQzOS00OWI3LTkxYTMtMDU1NWJkMGUyYTFkOmI5Njg3MDZlLWIwZDctNDY3MS05YjY3LWVmNjI1NjM3MzA3NQ
        prompt = []
        if create_prompt(result[0].get('type', 'unknown'), user_text, prompt):
            LOGGER.info(f"НАШ ПРОМПТ{prompt[0]}")
            # Для авторизации запросов используйте ключ, полученный в проекте GigaChat API
            with GigaChat(credentials=
                          "N2EyMzFjNDMtYzkyMC00MzhiLWE1YWEtOGE1OGZjMDlmNjM5Ojg1ZTFkZTM1LWRhN2QtNDU0Yi05NzliLTk5MjY2ZGQyMWRiOQ==", 
                        verify_ssl_certs=False, model="GigaChat-Max") as giga:
                response = giga.chat(prompt[0])

            return response.choices[0].message.content
        else:
            LOGGER.info('Извините, не корректный промпт')
            return('Извините, я вас не понимаю. Попробуйте изменить запрос.')


    def process_message(self, user_text):
        """
        Description:
            ответ
        Args:
            param1 (type): Описание параметра
            uset_text (str): текст запроса
        
        Returns:
            type: Что возвращает
        """
        if not user_text:
            LOGGER.error("бот не получил текст")
            return "бот не получил текст"
        
        if False:
            LOGGER.info("повторение текста пользователя")
            return "Вот Ваш запрос:\n" + user_text
        else:
            LOGGER.info("LLM ответ пользователю")
            return(self.get_answer_from_llm(user_text))
        