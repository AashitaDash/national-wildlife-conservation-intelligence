import re
import math
import hashlib
import hashlib
import logging
import time
from typing import List, Dict, Any, Optional

HAS_SENTENCE_TRANSFORMERS = True

import threading

logger = logging.getLogger("wildlife_platform.nlp.embeddings")

_MODEL_INSTANCE = None
_MODEL_LOAD_FAILED = False
_MODEL_LOCK = threading.Lock()


class VectorEmbedder:
    """
    Dense semantic vector embedding engine for documents and queries.
    Utilizes Sentence-Transformers 'all-MiniLM-L6-v2' (384 dimensions)
    with unit-norm cosine projection.

    Lazily loaded on first request with a thread lock to ensure minimal
    resident memory footprint at application startup (preventing 512MB OOM kills).
    """

    DIMENSION = 384

    @classmethod
    def preload_model(cls):
        """
        Deprecated: Kept for backwards compatibility. Eager preloading at startup
        is disabled on resource-constrained environments (512MB RAM).
        Loading is deferred until the first vector embedding request.
        """
        pass

    @classmethod
    def _get_model(cls):
        """
        Thread-safe on-demand lazy loader for SentenceTransformer.
        Loads 'all-MiniLM-L6-v2' on CPU and caches the singleton instance.
        """
        global _MODEL_INSTANCE, _MODEL_LOAD_FAILED

        if _MODEL_INSTANCE is not None:
            return _MODEL_INSTANCE
        if _MODEL_LOAD_FAILED:
            return None

        with _MODEL_LOCK:
            # Double-checked locking
            if _MODEL_INSTANCE is not None:
                return _MODEL_INSTANCE
            if _MODEL_LOAD_FAILED:
                return None

            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Initializing SentenceTransformer('all-MiniLM-L6-v2') on-demand (CPU)...")
                t0 = time.time()
                _MODEL_INSTANCE = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
                logger.info(f"SentenceTransformer loaded successfully in {(time.time() - t0)*1000:.1f}ms.")
                return _MODEL_INSTANCE
            except Exception as e:
                logger.warning(
                    f"Could not load SentenceTransformer on demand ({e}). "
                    "Falling back gracefully to deterministic FastText-style hash vector projection."
                )
                _MODEL_LOAD_FAILED = True
                return None

    @classmethod
    def generate_hash_embedding(cls, text: str) -> List[float]:
        """
        Deterministic, unit-normalized 384-dimensional dense vector generator
        using subword n-grams (FastText style) as an academic fallback.
        Ensures morphological variations ('elephant' and 'elephants') share dense features.
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
                        features.append(w_clean[i:i+n])

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
        """
        if not text or not text.strip():
            return [0.0] * cls.DIMENSION

        t_get_model_start = time.time()
        model = cls._get_model()
        t_get_model_end = time.time()
        print(f"[NLP PERF] cls._get_model call = {(t_get_model_end - t_get_model_start) * 1000:.2f} ms")
        
        if model is not None:
            try:
                t_emb_start = time.time()
                emb = model.encode(text, normalize_embeddings=True)
                t_emb_end = time.time()
                print(f"[NLP PERF] SentenceTransformer embedding generation = {(t_emb_end - t_emb_start) * 1000:.2f} ms")
                return [round(float(x), 5) for x in emb.tolist()]
            except Exception as e:
                logger.warning(f"Model encode failed ({e}), falling back to hash embedding.")

        t_hash_start = time.time()
        res = cls.generate_hash_embedding(text)
        t_hash_end = time.time()
        print(f"[NLP PERF] generate_hash_embedding = {(t_hash_end - t_hash_start) * 1000:.2f} ms")
        return res

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

        similarity = dot_product / (norm_a * norm_b)
        return max(-1.0, min(1.0, float(similarity)))

    @classmethod
    def rank_documents(
        cls,
        query_embedding: List[float],
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Ranks document records by cosine similarity to query embedding.
        """
        scored = []
        for doc in documents:
            doc_emb = doc.get("embedding_json") or doc.get("embedding")
            if not doc_emb:
                # Dynamically generate if missing
                doc_emb = cls.encode(doc.get("cleaned_text") or doc.get("raw_text") or "")

            score = cls.cosine_similarity(query_embedding, doc_emb)
            scored.append({
                **doc,
                "similarity_score": round(score, 4)
            })

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]
