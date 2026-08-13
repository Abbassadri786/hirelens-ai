from functools import lru_cache
from typing import Sequence
import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"

@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL_NAME)

def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = _model().encode(list(texts), normalize_embeddings=True)
    return [v.astype(float).tolist() for v in vectors]

def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    av = np.asarray(a, dtype=float)
    bv = np.asarray(b, dtype=float)
    denom = float(np.linalg.norm(av) * np.linalg.norm(bv))
    if denom == 0:
        return 0.0
    return float(np.dot(av, bv) / denom)

def semantic_score(resume_text: str, job_description: str) -> float:
    vectors = embed_texts([resume_text[:30000], job_description[:30000]])
    return round(max(0.0, min(100.0, cosine_similarity(vectors[0], vectors[1]) * 100.0)), 2)
