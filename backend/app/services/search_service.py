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

    COMMON_STOPWORDS = {
        "which", "what", "where", "when", "who", "whom", "whose", "why", "how",
        "are", "is", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "the", "a", "an", "and", "or", "but", "in", "on",
        "at", "to", "for", "with", "about", "against", "between", "into", "through",
        "during", "before", "after", "above", "below", "from", "up", "down", "of",
        "associated", "related", "found", "reported", "observed", "occurs"
    }

    @classmethod
    def search_documents(
        cls,
        db: Session,
        query: str,
        species_id: Optional[int] = None,
        source_type: Optional[str] = None,
        hybrid_alpha: float = 0.5,
        limit: int = 20
    ) -> List[SearchResultItem]:
        """
        Executes dedicated hybrid lexical and semantic search specifically across documents.
        Guarantees that corpus QA evaluates top document candidates without interference from
        other entities.
        """
        results: List[SearchResultItem] = []
        clean_q = query.strip().lower()
        if not clean_q:
            return results

        # 1. Generate query embedding
        embedder = cls.get_embedder()
        query_vec = embedder.embed_text(query)

        # 2. Extract meaningful search tokens
        all_tokens = [w for w in clean_q.split() if len(w) > 2]
        meaningful_tokens = [w for w in all_tokens if w not in cls.COMMON_STOPWORDS]
        tokens_for_matching = meaningful_tokens if meaningful_tokens else all_tokens

        # 3. Query documents
        doc_query = db.query(Document)
        if source_type:
            doc_query = doc_query.filter(Document.source_type == source_type)
        if species_id:
            doc_query = doc_query.filter(
                Document.species_mentions.any(species_id=species_id)
            )

        documents = doc_query.all()
        for doc in documents:
            text_corpus = f"{doc.title} {doc.summary or ''} {doc.cleaned_text or doc.raw_text or ''}".lower()

            # Lexical matching
            lexical_score = 0.0
            if tokens_for_matching:
                matches = sum(1 for w in tokens_for_matching if w in text_corpus)
                lexical_score = min(1.0, matches / len(tokens_for_matching))

            # Phrase bonus
            if clean_q in text_corpus:
                lexical_score = max(lexical_score, 0.9)
            else:
                # Check 2-word n-gram matches (e.g. "human-wildlife conflict" or "habitat loss")
                for i in range(len(all_tokens) - 1):
                    bigram = f"{all_tokens[i]} {all_tokens[i+1]}"
                    if bigram in text_corpus and bigram not in cls.COMMON_STOPWORDS:
                        lexical_score = max(lexical_score, min(1.0, lexical_score + 0.25))

            # Vector score
            vector_score = 0.0
            if doc.embedding_json and isinstance(doc.embedding_json, list) and len(doc.embedding_json) > 0:
                vector_score = max(0.0, cls.cosine_similarity(query_vec, doc.embedding_json))
            else:
                vector_score = lexical_score

            combined_score = ((1.0 - hybrid_alpha) * lexical_score) + (hybrid_alpha * vector_score)

            if combined_score >= 0.12 or lexical_score >= 0.25:
                snippet = doc.summary or ((doc.raw_text or '')[:200] + "...")
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

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:limit]

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
        Executes multi-entity hybrid search.
        Balances document candidates and species candidates so neither entity type
        crowds out the other.
        """
        clean_q = query.strip().lower()
        if not clean_q:
            return []

        doc_limit = max(10, limit // 2)
        doc_results = cls.search_documents(
            db=db,
            query=query,
            species_id=species_id,
            source_type=source_type,
            hybrid_alpha=hybrid_alpha,
            limit=doc_limit
        )

        # Species matching with meaningful tokens (ignoring stop words like 'which', 'are', 'with')
        all_tokens = [w for w in clean_q.split() if len(w) > 2]
        meaningful_tokens = [w for w in all_tokens if w not in cls.COMMON_STOPWORDS]

        species_results: List[SearchResultItem] = []
        if meaningful_tokens:
            species_query = db.query(Species).all()
            for sp in species_query:
                c_lower = sp.common_name.lower()
                s_lower = sp.scientific_name.lower()
                sp_text = f"{c_lower} {s_lower} {sp.description or ''} {sp.family or ''}".lower()

                sp_lexical = 0.0
                if clean_q in c_lower or clean_q in s_lower:
                    sp_lexical = 1.0
                elif any(tok in c_lower or tok in s_lower for tok in meaningful_tokens):
                    sp_lexical = 0.8
                elif any(tok in sp_text for tok in meaningful_tokens):
                    sp_lexical = 0.4

                if sp_lexical > 0:
                    species_results.append(
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

            species_results.sort(key=lambda r: r.relevance_score, reverse=True)
            species_results = species_results[:max(5, limit // 2)]

        combined = doc_results + species_results
        combined.sort(key=lambda r: r.relevance_score, reverse=True)
        return combined[:limit]

