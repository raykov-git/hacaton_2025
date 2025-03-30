import pandas as pd
import numpy as np
import pickle
import re
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import spacy

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

df_questions = pd.read_csv("files/preparation.csv")
df_services = pd.read_csv("files/service.csv")


def find_response(query, embeddings_file, df, top_k=1):
    query = lemmatize_text(query)
    query_embedding = model.encode([query])

    # Загрузка эмбобиков из файла
    with open(embeddings_file, "rb") as f:
        loaded_embeddings = pickle.load(f)

    # Преобразование загруженных эмбобиков
    if isinstance(loaded_embeddings, list):
        loaded_embeddings = np.array(loaded_embeddings)

    similarities = cosine_similarity(query_embedding, loaded_embeddings)[0]

    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    if embeddings_file == "files/preparation_embeddings.pkl":
        for idx in top_indices:
            row = df.iloc[int(idx)]
            results.append((row["ответ"], similarities[idx]))
    elif embeddings_file == "files/service_embeddings.pkl":
        for idx in top_indices:
            row = df.iloc[int(idx)]
            results.append((
                row["Услуга"],
                similarities[idx],
                row["Категория"],
                row["Цена (руб.)"],
                row["Срок выполнения"]
            ))

    return results


# Функция предобработки текста
def preprocess_text(text):
    if text is None:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-zа-яё\s]", "", text)
    return text.strip()




nlp = spacy.load("ru_core_news_sm")
def lemmatize_text(text):
    if pd.isna(text) or text is None:  
        return ""
    text = text.lower()
    
    text = re.sub(r"[^a-zA-Zа-яА-ЯёЁ\s]", "", text)
    
    doc = nlp(text)
    lemmatized_words = [token.lemma_ for token in doc]
    
    return " ".join(lemmatized_words).lower()

# results = find_response(
#     query=query,
#     embeddings_file="preparation_embeddings.pkl",
#     df=df_questions,
#     top_k=1
# )
