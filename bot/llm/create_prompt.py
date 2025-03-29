import logging
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
from .db_to_texts import *
import os
from .find import *

# Создаём логгер для create_prompt.py
LOGGER = logging.getLogger("create_prompt")
LOGGER.setLevel(logging.INFO)

# Создаём папку logs, если её ещё нет
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Файл для логов clinicBot.py в папке logs
log_file = os.path.join(log_dir, "create_prompt.log")
file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

LOGGER.addHandler(file_handler)


Model_Sentence_Transformer = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


# Загрузка базы сценариев
def load_knowledge_base():
  knowledge_base = []
  with open('files/knowledge_base.csv', 'r', encoding='utf-8') as f:
      reader = csv.DictReader(f)
      for row in reader:
          knowledge_base.append(row)
  return knowledge_base

# Проверка
knowledge_base = load_knowledge_base()

LOGGER.info("Получаем данные из БД")
# Получаем данные из БД
schedule_data = get_grouped_schedule()
LOGGER.info("данные из БД получены")

# Форматируем в текст
LOGGER.info("Форматируем в текст")
schedule_text = format_schedule_as_text(schedule_data)
LOGGER.info("Форматируем в текст - ок")


# сохранение контактов в переменную
contacts_text = get_contacts_as_text()


df_price=pd.read_csv("files/service.csv")
# Заполнение пустых значений, тк в нашем датасете с услугами оно есть
df_price["Категория"] = df_price["Категория"].fillna("")
df_price["Цена (руб.)"] = df_price["Цена (руб.)"].fillna("0")

# Создание полного описания
df_price["Полное_описание"] = (
    df_price["Услуга"].apply(preprocess_text) +
    " (" + df_price["Категория"].apply(preprocess_text)
)



df_tests = pd.read_csv("files/preparation.csv")


df_tests["вопрос_preprocessed"] = df_tests["вопрос"].apply(preprocess_text)
df_tests["ответ_preprocessed"] = df_tests["ответ"].apply(preprocess_text)
df_tests["эмбеддинги_вопросов"] = df_tests["вопрос_preprocessed"].apply(lambda x: Model_Sentence_Transformer.encode(x))

"""
import pickle
with open("preparation_embeddings.pkl", "rb") as f:
    loaded_embeddings = pickle.load(f)
df2["эмбеддинги_вопросов"] = loaded_embeddings
"""

import pickle

with open("files/service_embeddings.pkl", "rb") as f:
    service_embeddings = pickle.load(f)


"""# TODO нужно 1 раз
# создание векторов для описаний услуг
LOGGER.info("создание эмбеддингов для описаний услуг")
service_embeddings = Model_Sentence_Transformer.encode(df_price["Полное_описание"].tolist())
LOGGER.info("создание эмбеддингов для описаний услуг готово")"""


for entry in knowledge_base:
    entry["context_preprocessed"] = preprocess_text(entry["context"])

for entry in knowledge_base:
    entry["embedding"] = Model_Sentence_Transformer.encode(entry["context_preprocessed"])


# Функция поиска похожих услуг
def find_similar_services(query, top_k=5):
    query = preprocess_text(query)
    query_embedding = Model_Sentence_Transformer.encode([query])

    # Вычисление косинусного сходства
    LOGGER.info("Вычисление косинусного сходства")
    similarities = util.cos_sim(query_embedding, service_embeddings)[0]

    # Сортировка индексов по убыванию :(
    LOGGER.info("Сортировка индексов по убыванию :(")
    top_indices = similarities.argsort(descending=True)[:top_k]

    LOGGER.info("начало какой-то херни")
    response = ''
    for idx in top_indices:
        similarity_score = similarities[idx].item()
        row = df_price.iloc[int(idx)]
        response += f"- {row['Услуга']} ({row['Категория']}) - {row['Цена (руб.)']} руб. -{row['Срок выполнения']}\n"

    return response



# Поиск ответов на вопросы о подготовке
def find_answer(query, df, top_k=1):
    query_preprocessed = preprocess_text(query)
    query_embedding = Model_Sentence_Transformer.encode(query_preprocessed)

    # Вычисление косинусного сходства
    similarities = df["эмбеддинги_вопросов"].apply(
        lambda x: cosine_similarity([query_embedding], [x])[0][0]
    )

    top_indices = similarities.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        similarity_score = similarities.iloc[idx]
        response = df.iloc[idx]["ответ"]
        results.append((response, similarity_score))

    return results

# Sorry, but i'm not that kinda guy
# I won't buy you flowers just to see your smile
# Определение подходяшего сценария на основе knowledge_base и query
def find_similar_context(query, knowledge_base, top_k=1):
    query_preprocessed = preprocess_text(query)
    query_embedding = Model_Sentence_Transformer.encode(query_preprocessed)


    similarities = []
    for entry in knowledge_base:
        similarity = cosine_similarity([query_embedding], [entry["embedding"]])[0][0]
        similarities.append((similarity, entry))


    similarities.sort(reverse=True, key=lambda x: x[0])


    results = []
    for similarity, entry in similarities[:top_k]:
        #results.append({"type": entry["type"]})
        results.append({
            "type": entry["type"],
            "similarity": float(similarity),  # явное приведение к float для сериализации
            "is_confident": similarity > 0.6  # флаг уверенности
        })

    return results


def create_prompt(category, query, prompt_out=None):
    """
    Создает промт в зависимости от категории и запроса.

    Args:
        category (str): Категория запроса ("price_and_timing", "preparation", "contacts")
        query (str): Текст запроса пользователя
        prompt_out (list): Список для возврата сгенерированного промта (опционально)

    Returns:
        bool: True если промт успешно создан, False если произошла ошибка
    """
    try:
        if category == "price_and_timing":
            services = find_response(
                query=query,
                embeddings_file="files/service_embeddings.pkl",
                df=df_services,
                top_k=1
            )
            prompt = (
                f"Ты — бот, который помогает найти информацию о ценах и сроках выполнения медицинских анализов. "
                f"Дай точный ответ на вопрос пользователя'. Для ответа используй дополнительную информацию (INFO)"
                f"Вопрос: '{query}'. Дополнительная информация (INFO): "
                f"{services}\n\n"
            )

        elif category == "preparation":
            answers = find_response(
                query=query,
                embeddings_file="files/preparation_embeddings.pkl",
                df=df_questions,
                top_k=1
            )
            prompt = (
                f"Ты — бот, который помогает найти информацию о правилах подготовки к медицинским исследованиям. "
                f"Дай точный ответ на вопрос пользователя'. Для ответа используй дополнительную информацию (INFO)"
                f"Вопрос: '{query}'. Дополнительная информация (INFO): "
                f"{answers}\n\n"
            )

        elif category == "schedule":
            prompt = (
                f"Ты — бот, который помогает найти информацию о режиме работы медицинских учреждений. "
                f"Дай точный ответ на вопрос пользователя'. Для ответа используй дополнительную информацию (INFO). Соритруй дни недели и обязательно выводи адрес организации и название."
                f"Вопрос: '{query}'. Дополнительная информация (INFO): "
                f"{schedule_text}\n\n"
            )
        elif category == "contacts":
            prompt = (
                f"Ты — бот, который предоставляет контактную информацию медицинских учреждений. "
                f"Дай точный ответ на вопрос пользователя'. Для ответа используй дополнительную информацию (INFO)."
                f"Вопрос: '{query}'. Дополнительная информация (INFO): "
                f"{contacts_text}\n\n"
            )
        elif category == "cow":
            prompt = (
                f"Ты — бот, который рассказывает шутку про корову в поликлинике "
                f"Дай смешную и добрую шутку на основе запроса пользователя"
                f"Запрос: '{query}'\n\n"
            )


        else:
            return False

        # Если передан параметр prompt_out, сохраняем туда промт
        if prompt_out is not None and isinstance(prompt_out, list):
            prompt_out.clear()
            prompt_out.append(prompt)

        return True

    except Exception as e:
        print(f"Error creating prompt: {e}")
        return False
    


if __name__ == "__main__":
    print('__name__ == "__main__"')


