import os
import json
import pickle
import torch
import torch.nn as nn
from .embedder import embed

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, 'mlp_model.pkl')
META_PATH = os.path.join(BASE_DIR, 'model_metadata.json')

class MLPScorer(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.layers(x)


class _ModelUnpickler(pickle.Unpickler):
    """Перенаправляет __main__.MLPScorer на наш класс при десериализации"""
    def find_class(self, module, name):
        if name == 'MLPScorer':
            return MLPScorer
        return super().find_class(module, name)


# Глобальная модель — инициализируется один раз
_model = None


def load_model():
    global _model
    if _model is None:
        with open(META_PATH, 'r') as f:
            meta = json.load(f)

        with open(MODEL_PATH, 'rb') as f:
            loaded = _ModelUnpickler(f).load()

        if isinstance(loaded, dict):
            # pkl содержит state_dict
            _model = MLPScorer(input_dim=meta['input_dim'])
            _model.load_state_dict(loaded)

        elif isinstance(loaded, nn.Module):
            # pkl содержит готовый объект модели
            _model = loaded
        else:
            raise ValueError(f'Неизвестный формат модели: {type(loaded)}')

        _model.eval()
    return _model


def get_score(vacancy_text, resume_text):
    model = load_model()
    
    print(f"\n--- [ML INPUT START] ---")
    print(f"VACANCY: {vacancy_text[:100]}...")
    print(f"RESUME:  {resume_text[:100]}...")

    # Получаем эмбеддинги
    v_emb = embed(vacancy_text)
    r_emb = embed(resume_text)

    print(f"VECTORS: Vacancy({v_emb.shape}), Resume({r_emb.shape})")
    
    # Объединяем (cat) как в Jupyter
    combined = torch.cat([v_emb, r_emb]).unsqueeze(0) # добавляем размерность батча
    
    with torch.no_grad():
        score = model(combined.float()).item()

    print(f"PREDICTION SCORE: {score:.4f}")
    print(f"--- [ML INPUT END] ---\n")
    
    return round(score, 4)