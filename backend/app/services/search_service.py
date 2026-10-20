from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from backend.app.models.document import Document
from backend.app.models.species import Species
from backend.app.models.observation import Observation
from backend.app.schemas.search import SearchResultItem
from nlp.embeddings import VectorEmbedder


class SearchService:
    """
    Multi-Modal Hybrid Search Engine.
    Combines exact/lexical matching with dense semantic vector similarity
    across unstructured documents, species profiles, and spatial observations.
    """

    _embedder = None

    @classmethod
    def get_embedder(cls):
        if cls._embedder is None:
            cls._embedder = VectorEmbedder()
        return cls._embedder

    @classmethod
    def cosine_similarity(cls, vec1: List[float], vec2: List[float]) -> float:
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    @classmethod
    def hybrid_search(
        cls,
        db: Session,
        query: str,
        species_id: Optional[int] = None,
        source_type: Optional[str] = None,
        hybrid_alpha: float = 0.5,
        limit: int = 20
    ) -> List[SearchResultItem]:
        """
        Executes hybrid lexical and semantic search.
        Score = (1 - alpha) * lexical_score + alpha * vector_score
        """
        results: List[SearchResultItem] = []
        clean_q = query.strip().lower()
        if not clean_q:
            return results

        # 1. Generate query embedding
        embedder = cls.get_embedder()
        query_vec = embedder.embed_text(query)

        # 2. Search Documents
        doc_query = db.query(Document)
        if source_type:
            doc_query = doc_query.filter(Document.source_type == source_type)
        if species_id:
            doc_query = doc_query.filter(
                Document.species_mentions.any(species_id=species_id)
            )

        documents = doc_query.all()
        for doc in documents:
            # Lexical score
            text_corpus = f"{doc.title} {doc.summary or ''} {doc.cleaned_text or doc.raw_text}".lower()
            lexical_score = 0.0
            query_words = [w for w in clean_q.split() if len(w) > 2]
            if query_words:
                matches = sum(1 for w in query_words if w in text_corpus)
                lexical_score = min(1.0, matches / len(query_words))
            if clean_q in text_corpus:
                lexical_score = max(lexical_score, 0.9)

            # Vector score
            vector_score = 0.0
            if doc.embedding_json and isinstance(doc.embedding_json, list) and len(doc.embedding_json) > 0:
                vector_score = max(0.0, cls.cosine_similarity(query_vec, doc.embedding_json))
            else:
                vector_score = lexical_score

            combined_score = ((1.0 - hybrid_alpha) * lexical_score) + (hybrid_alpha * vector_score)

            if combined_score > 0.15 or lexical_score > 0.3:
                snippet = doc.summary or (doc.raw_text[:200] + "...")
                results.append(
                    SearchResultItem(
                        id=doc.id,
                        entity_type="DOCUMENT",
                        title=doc.title,
                        snippet=snippet,
                        relevance_score=round(float(combined_score), 4),
                        metadata={
                            "source_type": doc.source_type,
                            "author": doc.author,
                            "topics": doc.topics or [],
                            "publication_date": doc.publication_date.isoformat() if doc.publication_date else None
                        }
                    )
                )

        # 3. Search Species Catalog (Lexical + Semantic)
        species_query = db.query(Species).all()
        for sp in species_query:
            sp_text = f"{sp.common_name} {sp.scientific_name} {sp.description or ''} {sp.family or ''}".lower()
            sp_lexical = 0.0
            if clean_q in sp.common_name.lower() or clean_q in sp.scientific_name.lower():
                sp_lexical = 1.0
            elif any(w in sp_text for w in query_words):
                sp_lexical = 0.6

            if sp_lexical > 0:
                results.append(
                    SearchResultItem(
                        id=sp.id,
                        entity_type="SPECIES",
                        title=f"{sp.common_name} ({sp.scientific_name})",
                        snippet=sp.description or f"Catalogued IUCN status: {sp.iucn_category}",
                        relevance_score=round(float(sp_lexical), 4),
                        metadata={
                            "iucn_category": sp.iucn_category,
                            "family": sp.family,
                            "image_url": sp.image_url
                        }
                    )
                )

        # Rank results descending by combined relevance score
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:limit]
