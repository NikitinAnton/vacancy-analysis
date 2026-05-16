from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from classifier import get_score

app = FastAPI(title="ML Scoring Service")


class ScoreRequest(BaseModel):
    vacancy_text: str
    resume_text: str


class ScoreResponse(BaseModel):
    score: float


@app.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest):
    if not request.vacancy_text or not request.resume_text:
        raise HTTPException(status_code=400, detail="vacancy_text и resume_text обязательны")
    result = get_score(request.vacancy_text, request.resume_text)
    return ScoreResponse(score=result)


@app.get("/health")
def health():
    return {"status": "ok"}
