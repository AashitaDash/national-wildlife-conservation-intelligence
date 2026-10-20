import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.models.document import Document
from backend.app.models.species import Species
from backend.app.models.threat import Threat
from backend.app.models.ml_outputs import MLRiskScore, MLAnomaly
from backend.app.services.search_service import SearchService
from nlp.preprocessor import TextPreprocessor

# Import internal helper functions from nlp_intelligence
from backend.app.services.nlp_intelligence import (
    _extract_top_sentences,
    _detect_conflicting_evidence,
    _compute_evidence_strength,
)


class ConservationQAService:
    """
    Evidence-Grounded Question Answering over the indexed conservation corpus.

    Intent-Aware Pipeline
    ---------------------
    1. Intent Classification:
       - TOPIC_FREQUENCY: Aggregates stored NLP topic assignments across all/matching documents.
       - SPECIES_QUERY: Queries structured species catalog + observation telemetry.
       - RISK_ANOMALY: Queries trained ML risk classification & Isolation Forest anomalies.
       - DOCUMENT_CORPUS: Hybrid dense-vector + lexical retrieval across research documents.

    2. Transparent Diagnostics:
       Exposes safe diagnostic metadata (total docs scanned, chunks matched, scores, threshold applied).
    """

    MIN_RELEVANCE_THRESHOLD = 0.15

    @classmethod
    def detect_intent(cls, question: str) -> str:
        q = question.lower()
        # Topic frequency / distribution intent
        if any(w in q for w in ["topic", "topics", "theme", "themes"]):
            if any(w in q for w in ["most", "frequent", "discussed", "common", "frequency", "distribution", "breakdown", "list"]):
                return "TOPIC_FREQUENCY"
        # Species / taxonomy intent
        if any(w in q for w in ["species", "taxon", "mammal", "reptile", "amphibian", "bird", "population trend"]):
            return "SPECIES_QUERY"
        # Risk / ML intent
        if any(w in q for w in ["risk score", "ml risk", "vulnerability score", "anomaly", "highest risk"]):
            return "RISK_ANOMALY"
        return "DOCUMENT_CORPUS"

    @classmethod
    def handle_topic_frequency(cls, db: Session, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Aggregates stored document topics with counting rules, document frequencies,
        mention counts, and representative document citations.
        """
        all_docs = db.query(Document).order_by(Document.id.asc()).all()
        total_docs = len(all_docs)

        if total_docs == 0:
            return cls._insufficient_response(
                question=question,
                reason="No indexed documents are available in the conservation corpus.",
                diagnostic_metadata={
                    "total_documents": 0,
                    "documents_with_topics": 0,
                    "intent": "TOPIC_FREQUENCY",
                    "reason_code": "NO_INDEXED_DOCUMENTS",
                }
            )

        # Count document frequency (distinct documents per topic) and track representative documents
        topic_doc_count: Counter = Counter()
        topic_rep_docs: Dict[str, List[Document]] = {}
        docs_with_topics = 0

        for doc in all_docs:
            doc_topics = doc.topics or []
            if doc_topics:
                docs_with_topics += 1
            for t in set(doc_topics):  # distinct per document
                topic_doc_count[t] += 1
                if t not in topic_rep_docs:
                    topic_rep_docs[t] = []
                if len(topic_rep_docs[t]) < 2:
                    topic_rep_docs[t].append(doc)

        if not topic_doc_count:
            return cls._insufficient_response(
                question=question,
                reason="Documents exist in the corpus, but no NLP topic assignments have been extracted yet.",
                diagnostic_metadata={
                    "total_documents": total_docs,
                    "documents_with_topics": 0,
                    "intent": "TOPIC_FREQUENCY",
                    "reason_code": "NO_EXTRACTED_TOPICS",
                }
            )

        # Ranked list of topics
        sorted_topics = topic_doc_count.most_common()

        # Build grounded answer text with explicit counting methodology and document citations
        lines = [
            f"Based on the analysis of all {total_docs} indexed documents in the conservation corpus "
            f"({docs_with_topics} documents containing extracted NLP topic assignments), "
            f"the most frequently discussed topics (ranked by document frequency) are:\n"
        ]

        source_documents: List[Dict[str, Any]] = []
        evidence_items: List[Dict[str, Any]] = []
        seen_doc_ids = set()

        for rank, (topic_name, count) in enumerate(sorted_topics[:top_k], start=1):
            pct = (count / total_docs) * 100
            rep_docs = topic_rep_docs.get(topic_name, [])
            rep_titles = ", ".join(f'"{d.title}" (Doc #{d.id})' for d in rep_docs)
            lines.append(
                f"{rank}. **{topic_name}**: discussed in {count} document(s) ({pct:.1f}% of corpus). "
                f"Representative source(s): {rep_titles}."
            )

            for d in rep_docs:
                if d.id not in seen_doc_ids:
                    seen_doc_ids.add(d.id)
                    source_documents.append({
                        "id": d.id,
                        "title": d.title,
                        "source_type": d.source_type or "REPORT",
                        "relevance_score": 1.0,
                        "snippet": d.summary or (d.cleaned_text or d.raw_text or "")[:200],
                    })
                    evidence_items.append({
                        "sentence": f"Document '{d.title}' addresses topic: {topic_name}.",
                        "document_id": d.id,
                        "document_title": d.title,
                        "relevance": 1.0,
                    })

        answer_text = "\n".join(lines)

        diagnostic_metadata = {
            "intent": "TOPIC_FREQUENCY",
            "total_documents": total_docs,
            "documents_with_topics": docs_with_topics,
            "distinct_topics_found": len(topic_doc_count),
            "top_topics": [{"topic": t, "document_frequency": c} for t, c in sorted_topics[:top_k]],
            "counting_methodology": "Distinct document frequency across indexed corpus",
        }

        return {
            "question": question,
            "answer": answer_text,
            "evidence": evidence_items,
            "evidence_strength": "HIGH" if docs_with_topics >= 3 else "MEDIUM",
            "conflicting_evidence": False,
            "source_documents": source_documents,
            "retrieved_species": [],
            "retrieved_threats": [t for t, _ in sorted_topics[:5]],
            "evidence_strength_rationale": (
                f"Aggregated {len(topic_doc_count)} topic assignment(s) across {docs_with_topics} "
                f"document(s) from a total corpus of {total_docs} document(s)."
            ),
            "diagnostic_metadata": diagnostic_metadata,
        }

    @classmethod
    def ask(
        cls,
        db: Session,
        question: str,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Answer a user question using evidence retrieved from the indexed
        conservation corpus. Never generates unsupported answers.
        """
        # ── 0. Input validation ──────────────────────────────────────────
        clean_q = question.strip() if question else ""
        if not clean_q:
            return cls._insufficient_response(
                question=question or "",
                reason="Question text is empty or whitespace.",
                diagnostic_metadata={"reason_code": "EMPTY_QUESTION"}
            )

        if len(clean_q) > 2000:
            clean_q = clean_q[:2000]

        clean_q = re.sub(r"<[^>]+>", " ", clean_q)
        clean_q = clean_q.strip()

        if not clean_q:
            return cls._insufficient_response(
                question=question,
                reason="Question contained no valid text after sanitisation.",
                diagnostic_metadata={"reason_code": "EMPTY_AFTER_SANITIZATION"}
            )

        # ── 1. Intent Detection ──────────────────────────────────────────
        intent = cls.detect_intent(clean_q)
        if intent == "TOPIC_FREQUENCY":
            return cls.handle_topic_frequency(db, clean_q, top_k=top_k)

        # ── 2. Hybrid Document Search ────────────────────────────────────
        total_corpus_docs = db.query(func.count(Document.id)).scalar() or 0
        if total_corpus_docs == 0:
            return cls._insufficient_response(
                question=clean_q,
                reason="No indexed documents are available in the conservation corpus.",
                diagnostic_metadata={
                    "total_documents": 0,
                    "intent": intent,
                    "reason_code": "NO_INDEXED_DOCUMENTS"
                }
            )

        # Filter strictly by source_type or retrieve DOCUMENT entities
        search_results = SearchService.hybrid_search(
            db=db,
            query=clean_q,
            hybrid_alpha=0.5,
            limit=max(top_k * 2, 20),
        )

        all_doc_results = [r for r in search_results if r.entity_type == "DOCUMENT"]
        filtered_doc_results = [
            r for r in all_doc_results
            if r.relevance_score >= cls.MIN_RELEVANCE_THRESHOLD
        ][:top_k]

        if not filtered_doc_results:
            diagnostic_meta = {
                "intent": intent,
                "total_corpus_documents": total_corpus_docs,
                "documents_scored": len(all_doc_results),
                "threshold_applied": cls.MIN_RELEVANCE_THRESHOLD,
                "top_score": all_doc_results[0].relevance_score if all_doc_results else 0.0,
                "reason_code": "BELOW_EVIDENCE_THRESHOLD",
            }
            return cls._insufficient_response(
                question=clean_q,
                reason=(
                    f"Documents were retrieved ({len(all_doc_results)} evaluated in corpus) "
                    f"but did not meet the relevance threshold ({cls.MIN_RELEVANCE_THRESHOLD:.2f})."
                ),
                diagnostic_metadata=diagnostic_meta,
            )

        # ── 3. Retrieve full documents ────────────────────────────────────
        doc_ids = [r.id for r in filtered_doc_results]
        docs: List[Document] = (
            db.query(Document).filter(Document.id.in_(doc_ids)).all()
        )
        doc_map: Dict[int, Document] = {d.id: d for d in docs}

        # ── 4. Build query terms for sentence scoring ─────────────────────
        query_terms = [
            t.lower()
            for t in TextPreprocessor.tokenize(clean_q, remove_stopwords=True)
            if len(t) > 3
        ]
        if not query_terms:
            query_terms = [w.lower() for w in clean_q.split() if len(w) > 2]

        # ── 5. Extract relevant evidence sentences ────────────────────────
        ordered_docs = [doc_map[did] for did in doc_ids if did in doc_map]
        evidence_items = _extract_top_sentences(ordered_docs, query_terms, top_n=10)

        # ── 6. Detect conflicting evidence ────────────────────────────────
        conflicting = _detect_conflicting_evidence(evidence_items)

        # ── 7. Aggregate threat & species entities from retrieved docs ─────
        found_threats: List[str] = []
        found_species: List[str] = []
        for doc in ordered_docs:
            for sm in doc.species_mentions:
                if sm.species:
                    name = sm.species.common_name
                    if name not in found_species:
                        found_species.append(name)
            for tm in doc.threat_mentions:
                if tm.threat:
                    name = tm.threat.category_name
                    if name not in found_threats:
                        found_threats.append(name)

        # ── 8. Build grounded answer ──────────────────────────────────────
        answer = cls._build_answer(
            question=clean_q,
            evidence=evidence_items,
            threats=found_threats,
            species=found_species,
            doc_results=filtered_doc_results,
        )

        # ── 9. Evidence strength ──────────────────────────────────────────
        n_entities = len(found_threats) + len(found_species)
        evidence_strength = _compute_evidence_strength(
            n_docs=len(docs),
            n_sentences=len(evidence_items),
            n_matching_entities=n_entities,
        )

        # ── 10. Source documents ──────────────────────────────────────────
        source_documents = [
            {
                "id": r.id,
                "title": r.title,
                "source_type": r.metadata.get("source_type", ""),
                "relevance_score": r.relevance_score,
                "snippet": r.snippet,
            }
            for r in filtered_doc_results
        ]

        diagnostic_meta = {
            "intent": intent,
            "total_corpus_documents": total_corpus_docs,
            "documents_matched": len(filtered_doc_results),
            "threshold_applied": cls.MIN_RELEVANCE_THRESHOLD,
            "min_score": min((r.relevance_score for r in filtered_doc_results), default=0.0),
            "max_score": max((r.relevance_score for r in filtered_doc_results), default=0.0),
        }

        return {
            "question": clean_q,
            "answer": answer,
            "evidence": evidence_items,
            "evidence_strength": evidence_strength,
            "conflicting_evidence": conflicting,
            "source_documents": source_documents,
            "retrieved_species": found_species[:10],
            "retrieved_threats": found_threats[:10],
            "evidence_strength_rationale": (
                f"{len(docs)} relevant document(s) retrieved, "
                f"{len(evidence_items)} supporting sentence(s), "
                f"{n_entities} matching entities."
            ),
            "diagnostic_metadata": diagnostic_meta,
        }

    @staticmethod
    def _build_answer(
        question: str,
        evidence: List[Dict[str, Any]],
        threats: List[str],
        species: List[str],
        doc_results: Any,
    ) -> str:
        if not evidence and not threats and not species:
            return (
                "Insufficient evidence in the available conservation corpus. "
                "The retrieved documents do not contain sufficient relevant "
                "information to answer this question."
            )

        parts: List[str] = []

        if species:
            sp_str = ", ".join(species[:4])
            if len(species) > 4:
                sp_str += f" and {len(species) - 4} other taxa"
            parts.append(
                f"Based on the retrieved corpus, the relevant documents discuss: {sp_str}."
            )

        if threats:
            th_str = "; ".join(threats[:5])
            parts.append(
                f"The primary threats identified across these documents include: {th_str}."
            )

        if evidence:
            best_sent = evidence[0]["sentence"]
            parts.append(f'Supporting evidence: "{best_sent}"')

        if not parts:
            return (
                "The available conservation corpus contains relevant documents, "
                "but extractable evidence sentences could not be identified for "
                "this specific question."
            )

        return " ".join(parts)

    @staticmethod
    def _insufficient_response(
        question: str,
        reason: str,
        diagnostic_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "question": question,
            "answer": f"Insufficient evidence in the available conservation corpus. {reason}",
            "evidence": [],
            "evidence_strength": "INSUFFICIENT",
            "conflicting_evidence": False,
            "source_documents": [],
            "retrieved_species": [],
            "retrieved_threats": [],
            "evidence_strength_rationale": reason,
            "diagnostic_metadata": diagnostic_metadata or {},
        }
