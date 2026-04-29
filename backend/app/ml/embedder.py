import torch
from sentence_transformers import SentenceTransformer

# Используем многоязычную модель, которая понимает русский текст
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # paraphrase-multilingual — понимает русский язык
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _model


def embed(text: str) -> torch.Tensor:
    """Преобразует текст в вектор"""
    model = get_model()
    vector = model.encode(text, convert_to_tensor=True)
    return vector