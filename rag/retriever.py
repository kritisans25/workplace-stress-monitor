import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load knowledge base
with open("rag/knowledge_base.json", "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

documents = [
    f"{item['topic']} {' '.join(item['keywords'])} {item['content']}"
    for item in knowledge_base
]
# TF-IDF setup
vectorizer = TfidfVectorizer(
    stop_words='english',
    ngram_range=(1,2)
)
tfidf_matrix = vectorizer.fit_transform(documents)


def retrieve_context(user_query, top_k=2):

    query_vector = vectorizer.transform([user_query])

    similarities = cosine_similarity(query_vector, tfidf_matrix)

    best_indices = similarities[0].argsort()[-top_k:][::-1]

    retrieved_docs = [
        knowledge_base[idx]["content"]
        for idx in best_indices
    ]

    return "\n".join(retrieved_docs)