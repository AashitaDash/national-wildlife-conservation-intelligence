import re
import math
import hashlib
import logging
import time
import threading
from typing import List, Dict, Any, Optional

logger = logging.getLogger("wildlife_platform.nlp.embeddings")

_MODEL_INSTANCE = None
_MODEL_LOAD_FAILED = False
_MODEL_LOCK = threading.Lock()

# --- Memory budget guard -------------------------------------------------
# SentenceTransformer all-MiniLM-L6-v2 requires ~85 MB resident.
# On Render free tier (512 MB) loading it immediately at startup
# causes OOM because PyTorch+transformers+spacy are already in memory.
# We defer loading until the first embedding request AND add a 5-minute
# cooldown so a failed load does not retry on every subsequent request.
_LAST_LOAD_ATTEMPT: float = 0.0
_LOAD_COOLDOWN_SECONDS: float = 300.0   # 5 minutes between retries


class VectorEmbedder:
    """
    Dense semantic vector embedding engine for documents and queries.
    Utilizes Sentence-Transformers 'all-MiniLM-L6-v2' (384 dimensions)
    with unit-norm cosine projection.

    Lazily loaded on first request with a thread lock to prevent
    simultaneous model initialization under concurrent requests.
    Falls back to deterministic FastText-style hash projection when
    the model cannot be loaded (e.g. OOM on constrained environments).
    """

    DIMENSION = 384

    @classmethod
    def preload_model(cls):
        """
        Deprecated: Kept for backwards compatibility.
        Eager preloading at startup is disabled on resource-constrained
        environments (512 MB RAM). Loading is deferred to the first
        vector embedding request.
        """
        pass

    @classmethod
    def _get_model(cls):
        """
        Thread-safe on-demand lazy loader for SentenceTransformer.
        Loads 'all-MiniLM-L6-v2' on CPU and caches the singleton.
        Includes a cooldown between failed attempts to prevent OOM loops.
        """
        global _MODEL_INSTANCE, _MODEL_LOAD_FAILED, _LAST_LOAD_ATTEMPT

        if _MODEL_INSTANCE is not None:
            return _MODEL_INSTANCE
        if _MODEL_LOAD_FAILED:
            # Retry after cooldown so a transient OOM doesn't disable
            # embeddings forever, but also doesn't spam retries.
            if time.time() - _LAST_LOAD_ATTEMPT < _LOAD_COOLDOWN_SECONDS:
                return None
            # Reset so we try again
            _MODEL_LOAD_FAILED = False

        with _MODEL_LOCK:
            # Double-checked locking
            if _MODEL_INSTANCE is not None:
                return _MODEL_INSTANCE
            if _MODEL_LOAD_FAILED:
                return None

            _LAST_LOAD_ATTEMPT = time.time()
            try:
                from sentence_transformers import SentenceTransformer
                import torch
                logger.info(
                    "Initializing SentenceTransformer('all-MiniLM-L6-v2') on-demand (CPU)..."
                )
                t0 = time.time()
                # Force CPU; disable gradient tracking to halve memory overhead
                with torch.no_grad():
                    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
                _MODEL_INSTANCE = model
                elapsed = (time.time() - t0) * 1000
                logger.info(
                    f"SentenceTransformer loaded in {elapsed:.0f}ms. "
                    f"Resident memory should increase ~85 MB."
                )
                return _MODEL_INSTANCE
            except Exception as e:
                logger.warning(
                    f"Could not load SentenceTransformer ({type(e).__name__}: {e}). "
                    "Falling back to deterministic FastText-style hash vector projection."
                )
                _MODEL_LOAD_FAILED = True
                return None

    @classmethod
    def generate_hash_embedding(cls, text: str) -> List[float]:
        """
        Deterministic, unit-normalized 384-dimensional dense vector generator
        using subword n-grams (FastText style) as a lightweight fallback.
        Ensures morphological variations ('elephant' and 'elephants') share
        dense features.
        """
        words = text.lower().split()
        vector = [0.0] * cls.DIMENSION

        if not words:
            return vector

        # Extract words and character n-grams (3-grams and 4-grams)
        features = list(words)
        for w in words:
            w_clean = re.sub(r"[^a-z0-9]", "", w)
            if len(w_clean) >= 3:
                for n in (3, 4):
                    for i in range(len(w_clean) - n + 1):
                        features.append(w_clean[i:i + n])

        for feat in features:
            h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16)
            bucket = h % cls.DIMENSION
            sign = 1.0 if (h >> 11) & 1 else -1.0
            vector[bucket] += sign

        # L2 Normalization to unit hypersphere
        sq_sum = sum(x * x for x in vector)
        if sq_sum > 0:
            norm = math.sqrt(sq_sum)
            vector = [round(x / norm, 5) for x in vector]

        return vector

    @classmethod
    def encode(cls, text: str) -> List[float]:
        """
        Encodes input string into a 384-dimensional unit vector.
        Uses SentenceTransformer when available; falls back to hash projection.
        """
        if not text or not text.strip():
            return [0.0] * cls.DIMENSION

        model = cls._get_model()

        if model is not None:
            try:
                import torch
                with torch.no_grad():
                    emb = model.encode(
                        text,
                        normalize_embeddings=True,
                        convert_to_numpy=True,
                        show_progress_bar=False,
                    )
                return [round(float(x), 5) for x in emb.tolist()]
            except Exception as e:
                logger.warning(
                    f"SentenceTransformer encode failed ({type(e).__name__}: {e}), "
                    "falling back to hash embedding."
                )

        return cls.generate_hash_embedding(text)

    # Alias so callers using either name work
    embed_text = encode

    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Calculates cosine similarity: dot(A, B) / (norm(A) * norm(B)).
        Vectors are pre-normalized, so dot product equals cosine similarity.
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return max(-1.0, min(1.0, dot_product / (norm_a * norm_b)))

    @classmethod
    def rank_documents(
        cls,
        query_embedding: List[float],
        documents: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Ranks document records by cosine similarity to query embedding.
        """
        scored = []
        for doc in documents:
            doc_emb = doc.get("embedding_json") or doc.get("embedding")
            if not doc_emb:
                doc_emb = cls.encode(doc.get("cleaned_text") or doc.get("raw_text") or "")

            score = cls.cosine_similarity(query_embedding, doc_emb)
            scored.append({**doc, "similarity_score": round(score, 4)})

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]
