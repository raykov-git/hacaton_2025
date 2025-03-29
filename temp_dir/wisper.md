Чтобы Whisper не тормозил вашего бота при одновременных запросах, лучше всего использовать **асинхронную очередь с ограничением потоков (`ThreadPoolExecutor` + `Semaphore`)**.

### **Оптимальное решение для вашего кода**
Добавим:
1. **Глобальный пул потоков** (`ThreadPoolExecutor`) — чтобы Whisper не блокировал асинхронный цикл.
2. **Семафор** (`asyncio.Semaphore`) — чтобы ограничить количество одновременных транскрибаций (особенно важно для GPU, чтобы не перегрузить видеопамять).

---

### **1. Доработанный код**
```python
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Настройки для Whisper
WHISPER_MODEL = whisper.load_model("small").to(device)
WHISPER_THREAD_POOL = ThreadPoolExecutor(max_workers=2)  # 2-4 потока для CPU/GPU
WHISPER_SEMAPHORE = asyncio.Semaphore(2)  # Не больше 2 транскрибаций одновременно

async def transcribe_audio(file_path: str) -> str:
    """Асинхронная транскрибация через ThreadPool."""
    async with WHISPER_SEMAPHORE:  # Ограничиваем нагрузку
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            WHISPER_THREAD_POOL,
            lambda: WHISPER_MODEL.transcribe(file_path)["text"]
        )
        return result

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

        # Используем асинхронную транскрибацию
        result = await transcribe_audio(mp3_path)
        LOGGER.info(f'Текст из аудио: {result}')
        return result

    except Exception as e:
        LOGGER.error(f"Ошибка при обработке аудио: {e}")
        await message.answer(f"Ошибка при обработке аудио: {e}")
        return None
    
    finally:
        if os.path.exists(oga_path):
            os.remove(oga_path)
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
```

---

### **2. Почему это лучше?**
| Проблема | Решение | Эффект |
|----------|---------|--------|
| Whisper блокирует асинхронный цикл | `ThreadPoolExecutor` | Транскрибация выполняется в фоне, не мешая другим запросам. |
| Перегрузка GPU/CPU | `Semaphore` | Ограничиваем число одновременных транскрибаций (например, 2). |
| Медленная обработка при высокой нагрузке | Очередь запросов | Пользователи не получают таймаут, их запросы обрабатываются по очереди. |

---

### **3. Дополнительные оптимизации**
#### **Для CPU**
- Увеличьте `max_workers` в `ThreadPoolExecutor` (по количеству ядер CPU).
- Пример:  
  ```python
  WHISPER_THREAD_POOL = ThreadPoolExecutor(max_workers=4)  # Для 4-ядерного CPU
  ```

#### **Для GPU**
- Уменьшите `max_workers` (например, `2`), чтобы не перегружать видеопамять.
- Используйте `fp16` для экономии памяти:
  ```python
  WHISPER_MODEL = whisper.load_model("small", device="cuda", fp16=True)
  ```

#### **Если Whisper всё ещё тормозит**
- Перейдите на **ProcessPoolExecutor** (но учтите, что модель будет загружаться в каждом процессе):
  ```python
  from concurrent.futures import ProcessPoolExecutor
  WHISPER_PROCESS_POOL = ProcessPoolExecutor(max_workers=2)  # Для CPU
  ```

---

### **4. Тестирование**
Проверьте бота под нагрузкой:
1. Отправьте 3-5 голосовых сообщений одновременно.
2. Следите за:
   - Логами (`telegram_aiohttp.log`).
   - Нагрузкой на CPU/GPU (через `htop` или `nvidia-smi`).

Если обработка занимает много времени, попробуйте:
- Уменьшить модель Whisper (например, `tiny` вместо `small`).
- Добавить прогресс-бар для пользователя:
  ```python
  processing_msg = await message.reply("🔍 Обрабатываю аудио (1/2)...")
  ```

---

### **Итог**
Ваш код станет устойчивее к нагрузке, если:
1. **Добавить `ThreadPoolExecutor` + `Semaphore`**.
2. **Настроить количество потоков/процессов** под ваше железо (CPU/GPU).
3. **Протестировать** при одновременных запросах.

Если нужно ещё больше скорости — рассмотрите **вынос транскрибации в отдельный микросервис** (например, на FastAPI с горизонтальным масштабированием).