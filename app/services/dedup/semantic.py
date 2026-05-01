import os
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from app.core.config import get_settings

logger = logging.getLogger("psc_agent.dedup.semantic")
settings = get_settings()

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_model = None
_index = None
_embeddings = []


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def load_index() -> tuple[faiss.Index | None, list]:
    global _index, _embeddings

    if _index is not None:
        return _index, _embeddings

    index_path = settings.faiss_index_path
    meta_path = index_path + ".meta.npy"

    if os.path.exists(index_path) and os.path.exists(meta_path):
        try:
            _index = faiss.read_index(index_path)
            _embeddings = np.load(meta_path).tolist()
            logger.info(f"Loaded FAISS index with {len(_embeddings)} embeddings")
            return _index, _embeddings
        except Exception as e:
            logger.error(f"Failed to load FAISS index, rebuilding: {e}")
            _index = None
            _embeddings = []

    dimension = 384
    _index = faiss.IndexFlatIP(dimension)
    _embeddings = []
    logger.info("Created new FAISS index")
    return _index, _embeddings


def save_index():
    global _index, _embeddings
    if _index is None:
        return

    index_path = settings.faiss_index_path
    meta_path = index_path + ".meta.npy"

    os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)
    faiss.write_index(_index, index_path)
    np.save(meta_path, np.array(_embeddings))
    logger.info(f"Saved FAISS index with {len(_embeddings)} embeddings")


def is_semantic_duplicate(text: str, threshold: float | None = None) -> bool:
    threshold = threshold or settings.semantic_similarity_threshold
    index, embeddings = load_index()

    if index.ntotal == 0:
        return False

    model = get_model()
    embedding = model.encode([text], normalize_embeddings=True)

    similarities, _ = index.search(embedding, k=1)
    best_score = similarities[0][0]

    if best_score > threshold:
        logger.info(f"Semantic duplicate detected (similarity={best_score:.3f}, threshold={threshold})")
        return True

    return False


def add_embedding(text: str):
    index, embeddings = load_index()
    model = get_model()
    embedding = model.encode([text], normalize_embeddings=True)

    index.add(embedding)
    _embeddings.append(text)
    save_index()


def build_index_from_texts(texts: list[str]):
    global _index, _embeddings

    model = get_model()
    dimension = 384
    _index = faiss.IndexFlatIP(dimension)
    _embeddings = []

    if texts:
        embeddings = model.encode(texts, normalize_embeddings=True)
        _index.add(embeddings.astype("float32"))
        _embeddings = list(texts)

    save_index()
    logger.info(f"Built FAISS index from {len(texts)} texts")
