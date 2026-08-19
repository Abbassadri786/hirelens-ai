"""Local sentence-embedding similarity.

Runs 'all-MiniLM-L6-v2' in-process on CPU. This is a privacy decision as much
as a cost one: the matching step never transmits resume text to a third-party
embedding API, so the most sensitive operation in the pipeline happens entirely
on the host.

The module was previously unreachable -- its only importer was a dead duplicate
of the screening service -- and it imported 'numpy' and 'sentence_transformers',
neither of which was declared in 'requirements.txt'. Both are now declared, and
every exit degrades to a representable-scale score rather than raising,
so a machine without the model downloaded still serves requests.
"""

from __future__ import annotations

import logging
import math
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final

from app.core.config import settings

logger = logging.getLogger(__name__)

# Backend identifiers recorded on the screening result for provenance.
BACKEND_MINILM: Final = "minilm-local"
BACKEND_UNAVAILABLE: Final = "unavailable"
BACKEND_DISABLED: Final = "disabled"

# Raw cosine similarity between a resume and a job description in the same
# domain typically lands in roughly 0.25-0.85 rather than spanning 0-1.
CALIBRATION_FLOOR: Final = 0.20
CALIBRATION_CEILING: Final = 0.85

# Longest text handed to the encoder. MiniLM truncates at 256 word pieces, so
# anything beyond this is wasted work.
MAX_CHARS_PER_CHUNK: Final = 1_000
MAX_CHUNKS: Final = 12

# A single whole-resume embedding dilutes a strong match in one section across
# the whole document. Scoring chunks and combining the best with the mean
# captures a strong section without letting one lucky line dominate.
BEST_CHUNK_WEIGHT: Final = 0.6
MEAN_CHUNK_WEIGHT: Final = 0.4

_model: Any | None = None
_model_lock = threading.Lock()
_load_failed = False


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    """Similarity plus the backend that produced it."""

    score: float
    backend: str

    @property
    def available(self) -> bool:
        return self.backend == BACKEND_MINILM


def _load_model() -> Any | None:
    """Load the encoder once, tolerating absence.

    Guarded by a lock because FastAPI runs sync endpoints in a thread pool and
    two concurrent first-requests would otherwise load the model twice.
    """
    global _model, _load_failed

    if _model is not None:
        return _model
    if _load_failed:
        return None

    with _model_lock:
        if _model is not None:
            return _model
        if _load_failed:
            return None

        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading local embedding model %s", settings.EMBEDDING_MODEL)
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
            return _model
        except Exception:
            # Missing package, missing model cache, or no disk space. Semantic
            # matching is an enhancement; the deterministic score still stands.
            _load_failed = True
            logger.warning(
                "Embedding model %s unavailable; using lexical matching only",
                settings.EMBEDDING_MODEL,
                exc_info=True,
            )
            return None


def is_available() -> bool:
    """True when semantic matching can actually run."""
    return settings.EMBEDDINGS_ENABLED and _load_model() is not None


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed 'texts' as L2-normalized vectors. Empty list when unavailable."""
    if not texts:
        return []

    model = _load_model()
    if model is None:
        return []

    vectors = model.encode(list(texts), normalize_embeddings=True)
    return [list(map(float, vector)) for vector in vectors]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Cosine similarity without requiring numpy at the call site."""
    if not left or not right or len(left) != len(right):
        return 0.0

    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    denominator = left_norm * right_norm
    if denominator == 0.0:
        return 0.0
    return dot / denominator


def _calibrate(raw_cosine: float) -> float:
    """Rescale the useful cosine band onto 0-100."""
    span = CALIBRATION_CEILING - CALIBRATION_FLOOR
    normalized = (raw_cosine - CALIBRATION_FLOOR) / span
    return round(max(0.0, min(1.0, normalized)) * 100.0, 2)


def _chunk_text(text: str) -> list[str]:
    """Split text into paragraph-aligned chunks under the encoder's limit."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(buffer) + len(paragraph) + 2 <= MAX_CHARS_PER_CHUNK:
            buffer = f"{buffer}\n\n{paragraph}" if buffer else paragraph
            continue

        if buffer:
            chunks.append(buffer)
            buffer = ""

        # Break long paragraphs in a hard-split.
        while len(paragraph) > MAX_CHARS_PER_CHUNK:
            chunks.append(paragraph[:MAX_CHARS_PER_CHUNK])
            paragraph = paragraph[MAX_CHARS_PER_CHUNK:]
        buffer = paragraph

    if buffer:
        chunks.append(buffer)

    return chunks[:MAX_CHUNKS]


def semantic_similarity(resume_text: str, job_description: str) -> SimilarityResult:
    """Calibrated 0-100 similarity between a resume and a job description."""
    if not settings.EMBEDDINGS_ENABLED:
        return SimilarityResult(score=0.0, backend=BACKEND_DISABLED)

    if not resume_text.strip() or not job_description.strip():
        return SimilarityResult(score=0.0, backend=BACKEND_UNAVAILABLE)

    chunks = _chunk_text(resume_text)
    if not chunks:
        return SimilarityResult(score=0.0, backend=BACKEND_UNAVAILABLE)

    try:
        vectors = embed_texts([job_description[:MAX_CHARS_PER_CHUNK], *chunks])
    except Exception:
        logger.warning("Embedding inference failed", exc_info=True)
        return SimilarityResult(score=0.0, backend=BACKEND_UNAVAILABLE)

    if len(vectors) < 2:
        return SimilarityResult(score=0.0, backend=BACKEND_UNAVAILABLE)

    job_vector, *chunk_vectors = vectors
    similarities = [cosine_similarity(job_vector, cv) for cv in chunk_vectors]
    if not similarities:
        return SimilarityResult(score=0.0, backend=BACKEND_UNAVAILABLE)

    best = max(similarities)
    mean = sum(similarities) / len(similarities)
    combined = best * BEST_CHUNK_WEIGHT + mean * MEAN_CHUNK_WEIGHT

    return SimilarityResult(score=_calibrate(combined), backend=BACKEND_MINILM)


def semantic_score(resume_text: str, job_description: str) -> float:
    """Score-only helper for callers that do not need provenance."""
    return semantic_similarity(resume_text, job_description).score


def reset_model_cache() -> None:
    """Drop the cached model. Used by tests."""
    global _model, _load_failed
    with _model_lock:
        _model = None
        _load_failed = False