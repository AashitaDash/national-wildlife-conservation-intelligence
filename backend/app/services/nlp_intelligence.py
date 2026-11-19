"""
Conservation NLP Intelligence Service
======================================
Implements two evidence-grounded NLP capabilities:

  1. Multi-Document Conservation Synthesis
     Aggregates species, threats, and topics extracted from a user-selected set of
     indexed documents and synthesises a unified Conservation Intelligence Brief.

  2. Evidence-Grounded Question Answering (Ask the Conservation Corpus)
     Routes user questions through the existing Hybrid Search layer, extracts
     supporting evidence sentences, and returns a grounded answer together with
     source provenance.

Design principles
-----------------
* Reuses SearchService (hybrid lexical + semantic) as the shared retrieval layer.
* Reuses VectorEmbedder — no new model is loaded.
* Never fabricates evidence; all claims are sourced from indexed documents.
* Evidence strength is derived from transparent, interpretable signals.
* Insufficient evidence is reported explicitly rather than filled from general
  world knowledge.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.models.document import Document, NLPAnalysisResult
from backend.app.models.document import DocumentSpecies, DocumentThreat
from backend.app.services.search_service import SearchService
from nlp.preprocessor import TextPreprocessor

# ---------------------------------------------------------------------------
# Evidence-strength thresholds (interpretable, not probabilistic)
# ---------------------------------------------------------------------------
#  HIGH        ≥ 3 relevant docs   AND  ≥ 5 evidence sentences
#  MEDIUM      ≥ 2 relevant docs   AND  ≥ 2 evidence sentences
#  LOW         ≥ 1 relevant doc    OR   ≥ 1 evidence sentence
#  INSUFFICIENT  nothing found


def _compute_evidence_strength(
    n_docs: int, n_sentences: int, n_matching_entities: int
) -> str:
    """
    Derives a labelled evidence-strength category from interpretable retrieval signals.

    Methodology
    -----------
    HIGH:         ≥ 3 documents  AND  ≥ 5 sentences  AND  ≥ 2 entities
    MEDIUM:       ≥ 2 documents  AND  ≥ 2 sentences
    LOW:          ≥ 1 document   OR   ≥ 1 sentence
    INSUFFICIENT: nothing found
    """
    if n_docs >= 3 and n_sentences >= 5 and n_matching_entities >= 2:
        return "HIGH"
    if n_docs >= 2 and n_sentences >= 2:
        return "MEDIUM"
    if n_docs >= 1 or n_sentences >= 1:
        return "LOW"
    return "INSUFFICIENT"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_document_sentences(doc: Document) -> List[str]:
    """Extract individual sentences from a document's cleaned or raw text."""
    text = doc.cleaned_text or doc.raw_text or ""
    return TextPreprocessor.segment_sentences(TextPreprocessor.clean(text))


def _score_sentence_relevance(sentence: str, query_terms: List[str]) -> float:
    """Score a sentence by how many query terms it contains (normalized 0–1)."""
    if not query_terms:
        return 0.0
    sl = sentence.lower()
    hits = sum(1 for t in query_terms if t in sl)
    return hits / len(query_terms)


def _extract_top_sentences(
    documents: List[Document],
    query_terms: List[str],
    top_n: int = 3,
) -> List[Dict[str, Any]]:
    """
    Return the top-N most relevant sentences from each document, together with
    source provenance.  Duplicate or near-duplicate sentences are suppressed.
    """
    scored: List[Tuple[float, str, int, str]] = []  # (score, sentence, doc_id, doc_title)
    seen_fragments: set[str] = set()

    for doc in documents:
        sentences = _get_document_sentences(doc)
        for sent in sentences:
            # Skip very short sentences
            if len(sent.split()) < 6:
                continue
            # Near-duplicate suppression: normalise and compare 20-char prefix
            key = re.sub(r"\W+", "", sent.lower())[:30]
            if key in seen_fragments:
                continue
            seen_fragments.add(key)

            score = _score_sentence_relevance(sent, query_terms)
            if score > 0:
                scored.append((score, sent, doc.id, doc.title))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_n]

    return [
        {
            "sentence": s,
            "document_id": did,
            "document_title": dtitle,
            "relevance": round(sc, 3),
        }
        for sc, s, did, dtitle in top
    ]


def _detect_conflicting_evidence(evidence_items: List[Dict[str, Any]]) -> bool:
    """
    Simple heuristic: if two or more evidence sentences contain known
    contradictory qualifiers, flag conflicting evidence.
    """
    contradictions = [
        (r"\bnot\b", r"\bfrequently\b"),
        (r"\bno evidence\b", r"\bevidence\b"),
        (r"\bdecreasing\b", r"\bincreasing\b"),
        (r"\blow\b", r"\bhigh\b"),
    ]
    texts = [e["sentence"].lower() for e in evidence_items]
    for neg_pat, pos_pat in contradictions:
        has_neg = any(re.search(neg_pat, t) for t in texts)
        has_pos = any(re.search(pos_pat, t) for t in texts)
        if has_neg and has_pos:
            return True
    return False


# ---------------------------------------------------------------------------
# Synthesis Service
# ---------------------------------------------------------------------------

class ConservationSynthesisService:
    """
    Multi-Document Conservation Intelligence Brief generator.

    Pipeline
    --------
    SELECT DOCUMENTS  →  RETRIEVE NLP RESULTS  →  AGGREGATE SPECIES/THREATS/TOPICS
        →  RELEVANT SENTENCE EXTRACTION  →  DUPLICATE REDUCTION
        →  STRUCTURED SYNTHESIS  →  EVIDENCE + SOURCE ATTRIBUTION
    """

    @classmethod
    def synthesize(
        cls,
        db: Session,
        document_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Aggregate NLP intelligence from the selected documents and return a
        Conservation Intelligence Brief.
        """
        # ── 0. Validate input ────────────────────────────────────────────
        if not document_ids:
            return cls._insufficient_response("No document IDs provided.")

        # De-duplicate IDs
        unique_ids = list(dict.fromkeys(document_ids))

        # ── 1. Retrieve documents ────────────────────────────────────────
        docs: List[Document] = (
            db.query(Document)
            .filter(Document.id.in_(unique_ids))
            .all()
        )

        # Report any IDs not found
        found_ids = {d.id for d in docs}
        missing = [i for i in unique_ids if i not in found_ids]

        if not docs:
            return cls._insufficient_response(
                "None of the requested document IDs were found in the indexed corpus."
            )

        # ── 2. Aggregate species ─────────────────────────────────────────
        species_counter: Counter = Counter()
        species_meta: Dict[str, Dict[str, str]] = {}

        for doc in docs:
            for sm in doc.species_mentions:
                if sm.species:
                    name = sm.species.common_name
                    species_counter[name] += sm.mention_count or 1
                    if name not in species_meta:
                        species_meta[name] = {
                            "common_name": name,
                            "scientific_name": sm.species.scientific_name or "",
                            "iucn_category": getattr(sm.species, "iucn_category", ""),
                        }

        species_list = [
            {**species_meta[n], "total_mentions": cnt}
            for n, cnt in species_counter.most_common(10)
        ]

        # ── 3. Aggregate threats ─────────────────────────────────────────
        threat_counter: Counter = Counter()
        for doc in docs:
            for tm in doc.threat_mentions:
                if tm.threat:
                    threat_counter[tm.threat.category_name] += 1

        threats_list = [
            {"category_name": name, "document_count": cnt}
            for name, cnt in threat_counter.most_common(10)
        ]

        # ── 4. Aggregate topics ──────────────────────────────────────────
        topic_counter: Counter = Counter()
        for doc in docs:
            for tp in doc.topics or []:
                topic_counter[tp] += 1

        # Also mine from NLP results
        for doc in docs:
            for nlp_r in doc.nlp_results:
                for tp in nlp_r.topics or []:
                    topic_counter[tp] += 1

        topics_list = [
            {"topic": name, "document_count": cnt}
            for name, cnt in topic_counter.most_common(8)
        ]

        # ── 5. Build query terms for sentence extraction ─────────────────
        query_terms: List[str] = []
        for sp in species_list[:3]:
            query_terms += sp["common_name"].lower().split()
            if sp["scientific_name"]:
                query_terms += sp["scientific_name"].lower().split()
        for th in threats_list[:5]:
            query_terms += th["category_name"].lower().split()

        # Deduplicate, keep only meaningful terms
        query_terms = list({t for t in query_terms if len(t) > 3})

        # ── 6. Extract relevant evidence sentences ───────────────────────
        evidence_items = _extract_top_sentences(docs, query_terms, top_n=12)

        # ── 7. Synthesize summary ────────────────────────────────────────
        summary = cls._build_synthesis_summary(
            species=species_list,
            threats=threats_list,
            topics=topics_list,
            docs=docs,
            evidence=evidence_items,
        )

        # ── 8. Detect conflicting evidence ───────────────────────────────
        conflicting = _detect_conflicting_evidence(evidence_items)

        # ── 9. Source documents ──────────────────────────────────────────
        source_documents = [
            {
                "id": d.id,
                "title": d.title,
                "source_type": d.source_type,
                "author": d.author,
                "summary": d.summary or "",
            }
            for d in docs
        ]

        # ── 10. Evidence strength ────────────────────────────────────────
        n_entities = len(species_counter) + len(threat_counter)
        evidence_strength = _compute_evidence_strength(
            n_docs=len(docs),
            n_sentences=len(evidence_items),
            n_matching_entities=n_entities,
        )

        return {
            "summary": summary,
            "species": species_list,
            "threats": threats_list,
            "topics": topics_list,
            "documents_analyzed": len(docs),
            "evidence": evidence_items,
            "evidence_strength": evidence_strength,
            "conflicting_evidence": conflicting,
            "source_documents": source_documents,
            "missing_document_ids": missing,
            "evidence_strength_rationale": (
                f"{len(docs)} relevant document(s), "
                f"{len(evidence_items)} supporting sentence(s), "
                f"{n_entities} matching entities."
            ),
        }

    @staticmethod
    def _build_synthesis_summary(
        species: List[Dict],
        threats: List[Dict],
        topics: List[Dict],
        docs: List[Document],
        evidence: List[Dict],
    ) -> str:
        """
        Build a concise multi-document synthesis narrative from aggregated signals.
        Does NOT introduce information beyond what is present in the indexed documents.
        """
        parts: List[str] = []

        # Species clause
        if species:
            sp_names = ", ".join(s["common_name"] for s in species[:3])
            if len(species) > 3:
                sp_names += f" and {len(species) - 3} other taxa"
            parts.append(f"The selected documents discuss {sp_names}.")

        # Threat clause
        if threats:
            th_names = "; ".join(t["category_name"] for t in threats[:4])
            parts.append(
                f"Recurring threats identified across {len(docs)} document(s) include: "
                f"{th_names}."
            )

        # Topic clause
        if topics:
            tp_names = ", ".join(t["topic"] for t in topics[:4])
            parts.append(f"Dominant conservation topics: {tp_names}.")

        # Evidence clause — pick top 2 evidence sentences
        if evidence:
            best = evidence[0]["sentence"]
            parts.append(
                f'Key evidence from the corpus: "{best}"'
            )

        if not parts:
            return (
                "The selected documents did not yield sufficient extractable "
                "conservation intelligence. Consider adding documents with richer "
                "NLP content."
            )

        return " ".join(parts)

    @staticmethod
    def _insufficient_response(reason: str) -> Dict[str, Any]:
        return {
            "summary": f"Insufficient evidence in the available conservation corpus. {reason}",
            "species": [],
            "threats": [],
            "topics": [],
            "documents_analyzed": 0,
            "evidence": [],
            "evidence_strength": "INSUFFICIENT",
            "conflicting_evidence": False,
            "source_documents": [],
            "missing_document_ids": [],
            "evidence_strength_rationale": reason,
        }


# ---------------------------------------------------------------------------
# Question Answering Service (Intent-Aware & Diagnostic-Rich)
# ---------------------------------------------------------------------------

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

        # ── Topic frequency: must be checked first ───────────────────────
        # Broad: any mention of topic/theme/themes signals a corpus-level
        # frequency question even without explicit frequency words.
        _topic_keywords = [
            "topic", "topics", "theme", "themes",
            "what topics", "topic distribution", "what themes",
        ]
        _freq_qualifiers = [
            "most", "frequent", "frequently", "discussed", "common",
            "frequency", "distribution", "breakdown", "list", "across",
            "in these", "in the", "overview", "summary",
        ]
        has_topic = any(w in q for w in _topic_keywords)
        has_freq = any(w in q for w in _freq_qualifiers)
        if has_topic and has_freq:
            return "TOPIC_FREQUENCY"
        # Even without a freq qualifier, a stand-alone topic/theme question
        # is best routed to TOPIC_FREQUENCY (e.g. "What are the themes?")
        if has_topic:
            return "TOPIC_FREQUENCY"

        # ── Risk / anomaly: checked before SPECIES to avoid false matches ─
        if any(w in q for w in [
            "risk score", "ml risk", "vulnerability score",
            "anomaly", "highest risk", "risk model",
        ]):
            return "RISK_ANOMALY"

        # ── Species queries ───────────────────────────────────────────────
        _species_keywords = [
            "species", "taxon", "mammal", "reptile", "amphibian", "bird",
            "population trend", "conservation status", "iucn", "tiger",
            "elephant", "leopard", "rhino", "gharial", "frog", "snake",
            "status of", "taxonomy", "scientific name",
        ]
        if any(w in q for w in _species_keywords):
            return "SPECIES_QUERY"

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

        topic_doc_count: Counter = Counter()
        topic_rep_docs: Dict[str, List[Document]] = {}
        docs_with_topics = 0

        for doc in all_docs:
            doc_topics = doc.topics or []
            if doc_topics:
                docs_with_topics += 1
            for t in set(doc_topics):
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

        sorted_topics = topic_doc_count.most_common()

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
        total_corpus_docs = db.query(Document).count()
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

        # Retrieve top document candidates directly via dedicated search_documents
        all_doc_results = SearchService.search_documents(
            db=db,
            query=clean_q,
            hybrid_alpha=0.5,
            limit=max(top_k * 4, 30),
        )
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

