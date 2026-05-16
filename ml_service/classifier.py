import os
import json
import pickle
import torch
import torch.nn as nn
from embedder import embed

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, 'mlp_model.pkl')
META_PATH = os.path.join(BASE_DIR, 'model_metadata.json')


class MLPScorer(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.BatchNorm1d(512),
            nn.SiLU(),
            nn.Dropout(0.4),

            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.SiLU(),
            nn.Dropout(0.3),

            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.SiLU(),
            nn.Dropout(0.3),

            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.SiLU(),
            nn.Dropout(0.2),

            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.layers(x)


class _ModelUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == 'MLPScorer':
            return MLPScorer
        return super().find_class(module, name)


_model = None


def load_model():
    global _model
    if _model is None:
        with open(META_PATH, 'r') as f:
            meta = json.load(f)

        with open(MODEL_PATH, 'rb') as f:
            loaded = _ModelUnpickler(f).load()

        if isinstance(loaded, dict):
            _model = MLPScorer(input_dim=meta['input_dim'])
            _model.load_state_dict(loaded)
        elif isinstance(loaded, nn.Module):
            _model = loaded
        else:
            raise ValueError(f'Неизвестный формат модели: {type(loaded)}')

        _model.eval()
    return _model


def get_score(vacancy_text: str, resume_text: str) -> float:
    model = load_model()

    v_emb = embed(vacancy_text)
    r_emb = embed(resume_text)

    diff = v_emb - r_emb
    abs_diff = torch.abs(diff)
    prod = v_emb * r_emb

    combined = torch.cat([v_emb, r_emb, diff, abs_diff, prod]).unsqueeze(0)

    with torch.no_grad():
        score = model(combined.float()).item()

    return round(score, 4)
