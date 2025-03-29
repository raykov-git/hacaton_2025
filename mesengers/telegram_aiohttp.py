from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import logging
import aiohttp
import asyncio
import os
from aiogram import F
from aiogram.types import Message
import whisper
import torch
from aiogram.types import Message
from pydub import AudioSegment

"""

обработка голоса внутри

"""

# Создаём логгер для telegram_aiohttp.py
LOGGER = logging.getLogger("telegram_aiohttp")
LOGGER.setLevel(logging.INFO)

# Создаём папку logs, если её ещё нет
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Файл для логов clinicBot.py в папке logs
log_file = os.path.join(log_dir, "telegram_aiohttp.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

LOGGER.addHandler(file_handler)


# Инициализация модели Whisper
device = "cuda" if torch.cuda.is_available() else "cpu"
LOGGER.info(f"Using device: {device}")
WHISPER_MODEL = whisper.load_model("small").to(device)

# Токен бота
BOT_TOKEN = "7902145577:AAHdr9SmhEpgCM3pdBU_TBGMYaL_aMAfACw"
BASE_URL = "http://127.0.0.1:8000/"

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    LOGGER.info(f"Получена команда /start от {message.from_user.id}")
    api_url = BASE_URL + "api"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    welcome_message = data.get("answer")
                    await message.answer(welcome_message)
                else:
                    await message.answer("Не удалось получить приветствие от сервера.")
    except Exception as e:
        LOGGER.error(f"Ошибка при запросе к API: {e}")
        await message.answer("Произошла ошибка при подключении к серверу.")


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    LOGGER.info(f"Получена команда /help от {message.from_user.id}")
    await message.answer("Задайте мне вопрос текстом или голосом")


async def process_user_text(text: str, message: types.Message, processing_msg):
    api_url = BASE_URL + "qa"
    # Изменяем payload согласно RequestModel (используем "message" вместо "text")
    payload = {"question": text}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    # Извлекаем ответ из вложенной структуры response.text
                    reply = data.get("answer")
                    await bot.delete_message(chat_id=processing_msg.chat.id, message_id=processing_msg.message_id)
                    await message.answer(reply)
                else:
                    error_text = await response.text()
                    LOGGER.error(f"Ошибка сервера: {response.status} - {error_text}")
                    await bot.delete_message(chat_id=processing_msg.chat.id, message_id=processing_msg.message_id)
                    await message.answer(f"Ошибка сервера: {response.status}")
    except Exception as e:
        LOGGER.error(f"Ошибка соединения: {e}")
        await bot.delete_message(chat_id=processing_msg.chat.id, message_id=processing_msg.message_id)
        await message.answer("Сервер не отвечает.")


@dp.message(F.text)
async def handle_text(message: Message):
    print(f"Обработка текста от {message.from_user.id}: {message.text}")
    LOGGER.info(f"Обработка текста от {message.from_user.id}: {message.text}")

    processing_msg = await message.reply("Обрабатываю текст...")
    await process_user_text(message.text, message, processing_msg)


@dp.message(F.voice)
async def handle_voice(message: types.Message):
    print("Обработка голоса")
    LOGGER.info("Обработка голоса")

    processing_msg = await message.reply("Обрабатываю голос...")

    result = await convert_message_to_str(message)
    if result:
        await process_user_text(result, message, processing_msg)
    else:
        await bot.delete_message(chat_id=processing_msg.chat.id, message_id=processing_msg.message_id)
        await message.answer("Не удалось распознать голос")


async def convert_message_to_str(message: Message) -> str:
    try:
        voice = message.voice
        voice_file = await bot.get_file(voice.file_id)
        downloaded_file = await bot.download_file(voice_file.file_path)
        
        oga_path = f"temp_{voice.file_id}.oga"
        mp3_path = f"converted_{voice.file_id}.mp3"
        
        with open(oga_path, "wb") as f:
            f.write(downloaded_file.getvalue())
        
        audio = AudioSegment.from_file(oga_path, format="ogg")
        audio.export(mp3_path, format="mp3")

        result = WHISPER_MODEL.transcribe(mp3_path)
        LOGGER.info(f'Текст из аудио {result["text"]}')
        return result["text"]

    except Exception as e:
        LOGGER.error(f"Ошибка при обработке аудио: {e}")
        await message.answer(f"Ошибка при обработке аудио: {e}")
        return None
    
    finally:
        if os.path.exists(oga_path):
            os.remove(oga_path)
        if os.path.exists(mp3_path):
            os.remove(mp3_path)


async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("Bot start")
        LOGGER.info("Bot start")
        await dp.start_polling(bot, skip_updates=True)

    except Exception as e:
        LOGGER.error(f"Ошибка в работе бота: {e}")
        
    finally:
        await bot.session.close()
        print("Bot stop")
        LOGGER.info("Bot stopp")


if __name__ == "__main__":
    try:
        print("Bot starting...")
        LOGGER.info("Bot starting...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
        LOGGER.info("Bot stopped by user")