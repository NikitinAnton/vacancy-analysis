import torch
from sentence_transformers import SentenceTransformer

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _model


def embed(text: str) -> torch.Tensor:
    model = get_model()
    vector = model.encode(text, convert_to_tensor=True)
    return vector
