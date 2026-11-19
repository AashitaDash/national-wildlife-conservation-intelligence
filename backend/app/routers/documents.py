from typing import List, Optional
import datetime
import time
import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from backend.app.dependencies import get_db, get_optional_user, require_roles
from backend.app.models.document import Document, DocumentSpecies, DocumentThreat, NLPAnalysisResult
from backend.app.models.species import Species
from backend.app.models.threat import Threat
from backend.app.models.user import User
from backend.app.schemas.document import (
    DocumentResponse, DocumentDetailResponse, DocumentCreate,
    SpeciesExtractionItem, ThreatExtractionItem,
    SynthesisRequest, SynthesisResponse, EvidenceItem, SourceDocumentSummary,
    QARequest, QAResponse,
)
from backend.app.services.nlp_intelligence import (
    ConservationSynthesisService, ConservationQAService,
)

# NLP Pipeline Components
from nlp.preprocessor import TextPreprocessor
from nlp.entity_extractor import GazetteerEntityExtractor
from nlp.threat_matcher import ThreatKeywordMatcher
from nlp.topic_classifier import TopicClassifier
from nlp.summarizer import ConservationSummarizer
from nlp.embeddings import VectorEmbedder

# PDF size limit — configurable via environment variable MAX_PDF_UPLOAD_MB (default 10)
_MAX_PDF_MB = int(os.environ.get("MAX_PDF_UPLOAD_MB", "10"))
MAX_PDF_UPLOAD_BYTES = _MAX_PDF_MB * 1024 * 1024

router = APIRouter(prefix="/documents", tags=["Unstructured Documents & NLP Intelligence"])

# Cache NLP singletons
_extractor = None
_threat_matcher = None
_topic_classifier = None
_summarizer = None
_embedder = None


def get_nlp_pipeline():
    global _extractor, _threat_matcher, _topic_classifier, _summarizer, _embedder
    if _extractor is None:
        _extractor = GazetteerEntityExtractor()
    if _threat_matcher is None:
        _threat_matcher = ThreatKeywordMatcher()
    if _topic_classifier is None:
        _topic_classifier = TopicClassifier()
    if _summarizer is None:
        _summarizer = ConservationSummarizer()
    if _embedder is None:
        _embedder = VectorEmbedder()
    return _extractor, _threat_matcher, _topic_classifier, _summarizer, _embedder


def _format_document_response(doc: Document, nlp_res: Optional[NLPAnalysisResult] = None) -> DocumentResponse:
    species_items = []
    # Check if we have extracted species evidence from nlp_res
    species_evidence_map = {}
    if nlp_res and nlp_res.extracted_entities:
        for s in nlp_res.extracted_entities.get("species", []):
            if isinstance(s, dict) and s.get("canonical_name"):
                species_evidence_map[s["canonical_name"].lower()] = s.get("evidence_passage")

    for sm in doc.species_mentions:
        if sm.species:
            c_lower = sm.species.common_name.lower()
            species_items.append(
                SpeciesExtractionItem(
                    species_id=sm.species_id,
                    common_name=sm.species.common_name,
                    scientific_name=sm.species.scientific_name,
                    mention_count=sm.mention_count,
                    evidence_passage=species_evidence_map.get(c_lower)
                )
            )

    threat_meta_map = {}
    if nlp_res and nlp_res.raw_meta:
        for th in nlp_res.raw_meta.get("threat_extractions", []):
            if isinstance(th, dict) and th.get("category_name"):
                threat_meta_map[th["category_name"].lower()] = th

    threat_items = []
    for tm in doc.threat_mentions:
        if tm.threat:
            cat_lower = tm.threat.category_name.lower()
            th_meta = threat_meta_map.get(cat_lower, {})
            threat_items.append(
                ThreatExtractionItem(
                    threat_id=tm.threat_id,
                    category_name=tm.threat.category_name,
                    mention_count=th_meta.get("mention_count", 1),
                    confidence_score=th_meta.get("confidence_score") or tm.confidence_score or 0.8,
                    evidence_status=th_meta.get("evidence_status", "REPORTED_SOURCE"),
                    supporting_passage=th_meta.get("supporting_passage"),
                    section_type=th_meta.get("section_type", "BODY"),
                    score_type=th_meta.get("score_type", "CALIBRATED_PROBABILITY"),
                    explanation=th_meta.get("explanation")
                )
            )

    doc_type = "GENERAL_CONSERVATION_DOC"
    topic_breakdown = None
    if nlp_res and nlp_res.raw_meta:
        doc_type = nlp_res.raw_meta.get("document_type", "GENERAL_CONSERVATION_DOC")
        topic_breakdown = nlp_res.raw_meta.get("topic_breakdown")

    return DocumentResponse(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        document_type=doc_type,
        author=doc.author,
        publication_date=doc.publication_date,
        url=doc.url,
        summary=doc.summary,
        topics=doc.topics or [],
        topic_breakdown=topic_breakdown,
        created_at=doc.created_at,
        species_mentions=species_items,
        threat_mentions=threat_items
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    source_type: Optional[str] = Query(None, description="Filter by source type (e.g. INCIDENT_LOG, RESEARCH_PAPER)"),
    species_id: Optional[int] = Query(None, description="Filter by extracted species ID"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List processed intelligence documents with extracted entities and threat tags.
    """
    query = db.query(Document)
    if source_type:
        query = query.filter(Document.source_type == source_type)
    if species_id:
        query = query.filter(Document.species_mentions.any(species_id=species_id))

    docs = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    doc_ids = [d.id for d in docs]
    nlp_results = {
        nr.document_id: nr
        for nr in db.query(NLPAnalysisResult).filter(NLPAnalysisResult.document_id.in_(doc_ids)).all()
    } if doc_ids else {}
    return [_format_document_response(d, nlp_results.get(d.id)) for d in docs]


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
def get_document_detail(doc_id: int, db: Session = Depends(get_db)):
    """
    Retrieve full document details, cleaned transcript, and NLP analysis breakdown.
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document ID {doc_id} not found")

    nlp_res = db.query(NLPAnalysisResult).filter(NLPAnalysisResult.document_id == doc_id).first()
    base = _format_document_response(doc, nlp_res)

    raw_meta = (nlp_res.raw_meta if nlp_res and nlp_res.raw_meta else {})
    nlp_payload = {
        "extracted_entities": nlp_res.extracted_entities if nlp_res else {},
        "topics": nlp_res.topics if nlp_res else [],
        "sentiment_score": raw_meta.get("sentiment_score", 0.0),
        "urgency_score": raw_meta.get("urgency", 0.0),
        "processing_time_ms": raw_meta.get("processing_time_ms", 0.0),
        "document_type": raw_meta.get("document_type", "GENERAL_CONSERVATION_DOC"),
        "threat_extractions": raw_meta.get("threat_extractions", []),
        "topic_breakdown": raw_meta.get("topic_breakdown", [])
    }

    return DocumentDetailResponse(
        **base.model_dump(),
        cleaned_text=doc.cleaned_text or doc.raw_text,
        nlp_results=nlp_payload
    )


@router.post("", response_model=DocumentDetailResponse, status_code=status.HTTP_201_CREATED)
def upload_and_process_document(
    doc_in: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("RESEARCHER", "FOREST_OFFICER", "ADMIN", "NGO"))
):
    """
    Ingest unstructured document or incident dispatch:
    Executes automated preprocessing, section segmentation, document classification,
    evidence-grounded entity recognition, calibrated threat categorization,
    topic modeling, extractive summarization, and dense vector embedding.
    """
    extractor, threat_matcher, topic_classifier, summarizer, embedder = get_nlp_pipeline()

    start_time = datetime.datetime.now(datetime.timezone.utc)
    t0 = time.time()

    # 1. Preprocessing & Section Segmentation
    cleaned_text = TextPreprocessor.clean_text(doc_in.raw_text)
    sections = TextPreprocessor.segment_sections(doc_in.raw_text)
    doc_type = TextPreprocessor.classify_document_type(doc_in.raw_text, title=doc_in.title)
    t1 = time.time()
    print(f"[NLP PERF] Text preprocessing, sections={len(sections)}, type={doc_type} = {(t1 - t0) * 1000:.2f} ms")

    # 2. Hybrid NER with supporting passages and section context
    try:
        entities = extractor.extract_entities(cleaned_text, sections=sections)
    except TypeError:
        entities = extractor.extract_entities(cleaned_text)
    t2 = time.time()
    print(f"[NLP PERF] Entity extraction = {(t2 - t1) * 1000:.2f} ms")

    # 3. Calibrated Threat Extraction with supporting passages and evidence status
    try:
        threat_extractions = threat_matcher.extract_threats(
            cleaned_text,
            document_type=doc_type,
            sections=sections
        )
    except TypeError:
        threat_extractions = threat_matcher.extract_threats(cleaned_text)
    t3 = time.time()
    print(f"[NLP PERF] Threat extraction ({len(threat_extractions)} found) = {(t3 - t2) * 1000:.2f} ms")

    # 4. Topic Modeling with Section-Aware weighting
    try:
        topic_breakdown = topic_classifier.classify(cleaned_text, sections=sections)
    except TypeError:
        topic_breakdown = topic_classifier.classify(cleaned_text)
    topics = [t["topic"] for t in topic_breakdown]
    t4 = time.time()
    print(f"[NLP PERF] Topic classification = {(t4 - t3) * 1000:.2f} ms")

    # 5. Extractive Summarization
    summary_res = summarizer.summarize(cleaned_text, max_sentences=3)
    summary_text = summary_res.get("extractive_summary", "") if isinstance(summary_res, dict) else str(summary_res)
    t5 = time.time()
    print(f"[NLP PERF] Summarization = {(t5 - t4) * 1000:.2f} ms")

    # 6. Dense Vector Embedding (384-d)
    embedding = embedder.embed_text(cleaned_text)
    t6 = time.time()
    print(f"[NLP PERF] Total embedder.embed_text call = {(t6 - t5) * 1000:.2f} ms")

    # 7. Persist Document
    doc = Document(
        title=doc_in.title,
        source_type=doc_in.source_type,
        author=doc_in.author,
        publication_date=doc_in.publication_date,
        url=doc_in.url,
        raw_text=doc_in.raw_text,
        cleaned_text=cleaned_text,
        summary=summary_text,
        topics=topics,
        embedding_json=embedding,
        author_user_id=getattr(current_user, "id", None) if current_user and not hasattr(current_user, "dependency") else None
    )
    db.add(doc)
    db.flush()
    t7 = time.time()
    print(f"[NLP PERF] Database insertion (Document) = {(t7 - t6) * 1000:.2f} ms")

    # 8. Link Species Associations
    species_by_common = {s.common_name.lower(): s.id for s in db.query(Species).all()}
    species_by_sci = {s.scientific_name.lower(): s.id for s in db.query(Species).all()}
    for sp_entity in entities.get("species", []):
        c_name = (sp_entity.get("canonical_name") or sp_entity.get("name", "")).lower()
        s_name = sp_entity.get("scientific_name", "").lower()
        sp_id = species_by_common.get(c_name) or species_by_sci.get(s_name)
        if sp_id:
            existing_link = db.query(DocumentSpecies).filter_by(document_id=doc.id, species_id=sp_id).first()
            if not existing_link:
                doc_sp = DocumentSpecies(
                    document_id=doc.id,
                    species_id=sp_id,
                    mention_count=sp_entity.get("mention_count", 1)
                )
                db.add(doc_sp)

    # 9. Link Threat Associations with Calibrated Confidence
    threat_map = {t.category_name.lower(): t.id for t in db.query(Threat).all()}
    for th in threat_extractions:
        cat_lower = th.get("category_name", "").lower()
        threat_id = threat_map.get(cat_lower)
        if not threat_id:
            new_threat = Threat(category_name=th["category_name"])
            db.add(new_threat)
            db.flush()
            threat_id = new_threat.id
            threat_map[cat_lower] = threat_id

        doc_th = DocumentThreat(
            document_id=doc.id,
            threat_id=threat_id,
            confidence_score=th.get("confidence_score", 0.50)
        )
        db.add(doc_th)

    # 10. Store Full NLP Result
    proc_time_ms = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds() * 1000.0
    nlp_res = NLPAnalysisResult(
        document_id=doc.id,
        extracted_entities=entities,
        topics=topics,
        raw_meta={
            "processing_time_ms": proc_time_ms,
            "document_type": doc_type,
            "threat_extractions": threat_extractions,
            "topic_breakdown": topic_breakdown,
            "urgency": 0.8 if any(t.get("evidence_status") == "DIRECTLY_OBSERVED" for t in threat_extractions) else 0.3
        }
    )
    db.add(nlp_res)

    db.commit()
    t8 = time.time()
    print(f"[NLP PERF] Database associations & commit = {(t8 - t7) * 1000:.2f} ms")

    db.refresh(doc)
    return get_document_detail(doc.id, db)


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract plain text from a PDF byte stream using PyMuPDF (fitz).
    Raises HTTPException for unreadable, empty, or image-only PDFs.
    Does NOT perform OCR.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF extraction library (PyMuPDF) is not installed on this server."
        )

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file could not be opened as a valid PDF. It may be corrupted or password-protected."
        )

    pages_text = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text:
            pages_text.append(text.strip())

    doc.close()

    combined = "\n\n".join(pages_text).strip()
    if not combined:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "This PDF does not contain extractable text. "
                "It may be a scanned image-only document. "
                "OCR support is not currently enabled."
            )
        )
    return combined


@router.post(
    "/upload-pdf",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF for automated NLP processing",
    description=(
        "Upload a conservation research PDF. Text is extracted with PyMuPDF and "
        "immediately processed through the existing NLP pipeline: entity extraction, "
        "threat detection, topic classification, extractive summarization, and "
        "384-d sentence embedding. Image-only/scanned PDFs are rejected with a "
        "clear error. Max size is configurable via MAX_PDF_UPLOAD_MB (default 10 MB)."
    )
)
async def upload_pdf_document(
    file: UploadFile = File(..., description="PDF file to analyse (max 10 MB by default)"),
    title: Optional[str] = Query(None, description="Optional document title; defaults to the uploaded filename"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("RESEARCHER", "FOREST_OFFICER", "ADMIN", "NGO")),
):
    """
    Phase 1 – Validate
    Phase 2 – Extract text with PyMuPDF
    Phase 3 – Run existing NLP pipeline
    Phase 4 – Persist and return identical DocumentDetailResponse
    """
    # ── 1. Extension & MIME validation ─────────────────────────────────────
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF documents are supported. Please upload a file with a .pdf extension."
        )
    if file.content_type and file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid MIME type '{file.content_type}'. Only application/pdf is accepted."
        )

    # ── 2. Size validation ─────────────────────────────────────────────────
    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file is empty. Please select a valid PDF."
        )
    if len(pdf_bytes) > MAX_PDF_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF exceeds the maximum allowed size of {_MAX_PDF_MB} MB."
        )

    # ── 3. Magic-byte check (PDFs start with %PDF) ─────────────────────────
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file does not appear to be a valid PDF (missing %PDF header)."
        )

    # ── 4. Extract text ────────────────────────────────────────────────────
    raw_text = _extract_pdf_text(pdf_bytes)

    # ── 5. Run NLP pipeline (identical to text endpoint) ──────────────────
    doc_title = title or os.path.splitext(filename)[0] or "Uploaded PDF Document"

    doc_create = DocumentCreate(
        title=doc_title,
        source_type="PDF_UPLOAD",
        author=current_user.full_name if current_user else "PDF Upload",
        raw_text=raw_text,
    )

    # Delegate entirely to the existing text-based endpoint logic
    return upload_and_process_document(doc_create, db, current_user)


# ─────────────────────────────────────────────────────────────────────────────
# Feature A — Multi-Document Conservation Intelligence Brief
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/synthesize",
    response_model=SynthesisResponse,
    summary="Generate a Conservation Intelligence Brief from selected documents",
    description=(
        "Accepts a list of indexed document IDs and synthesises a unified "
        "Conservation Intelligence Brief. Aggregates species, threats, and topics "
        "from existing NLP results; extracts supporting evidence sentences; and "
        "computes an interpretable evidence-strength label (HIGH/MEDIUM/LOW/INSUFFICIENT). "
        "Uses the existing Hybrid Search infrastructure as the shared retrieval layer. "
        "Does NOT fabricate information — all claims are sourced from indexed documents."
    ),
)
def synthesize_documents(
    req: SynthesisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("RESEARCHER", "FOREST_OFFICER", "ADMIN", "NGO")),
):
    """
    Multi-Document Conservation Synthesis endpoint.

    POST /api/v1/documents/synthesize
    Body: { "document_ids": [1, 2, 3] }
    """
    try:
        result = ConservationSynthesisService.synthesize(
            db=db,
            document_ids=req.document_ids,
        )
    except Exception as exc:
        # Never leak stack traces
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conservation synthesis failed due to an internal error. Please try again.",
        ) from exc

    # Coerce evidence dicts to EvidenceItem for response_model validation
    evidence_items = [
        EvidenceItem(**e) for e in result.get("evidence", [])
    ]
    source_docs = [
        SourceDocumentSummary(**sd) for sd in result.get("source_documents", [])
    ]

    return SynthesisResponse(
        summary=result["summary"],
        species=result["species"],
        threats=result["threats"],
        topics=result["topics"],
        documents_analyzed=result["documents_analyzed"],
        evidence=evidence_items,
        evidence_strength=result["evidence_strength"],
        conflicting_evidence=result["conflicting_evidence"],
        source_documents=source_docs,
        missing_document_ids=result.get("missing_document_ids", []),
        evidence_strength_rationale=result["evidence_strength_rationale"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Feature B — Ask the Conservation Corpus (Evidence-Grounded QA)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/ask",
    response_model=QAResponse,
    summary="Ask the Conservation Corpus — evidence-grounded question answering",
    description=(
        "Accepts a natural-language question and retrieves relevant documents using "
        "the existing Hybrid Search (lexical + semantic). Extracts supporting evidence "
        "sentences from the top-K retrieved documents and returns a grounded answer "
        "with full source provenance. "
        "If the corpus does not contain sufficient relevant evidence, returns an "
        "explicit INSUFFICIENT response rather than fabricating an answer. "
        "Answers questions only from the indexed conservation corpus — not from "
        "general world knowledge."
    ),
)
def ask_conservation_corpus(
    req: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("RESEARCHER", "FOREST_OFFICER", "ADMIN", "NGO")),
):
    """
    Evidence-Grounded Question Answering endpoint.

    POST /api/v1/documents/ask
    Body: { "question": "What are the major threats to Asian elephants?", "top_k": 5 }
    """
    try:
        result = ConservationQAService.ask(
            db=db,
            question=req.question,
            top_k=req.top_k,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Question answering failed due to an internal error. Please try again.",
        ) from exc

    evidence_items = [
        EvidenceItem(**e) for e in result.get("evidence", [])
    ]
    source_docs = [
        SourceDocumentSummary(**sd) for sd in result.get("source_documents", [])
    ]

    return QAResponse(
        question=result["question"],
        answer=result["answer"],
        evidence=evidence_items,
        evidence_strength=result["evidence_strength"],
        conflicting_evidence=result["conflicting_evidence"],
        source_documents=source_docs,
        retrieved_species=result.get("retrieved_species", []),
        retrieved_threats=result.get("retrieved_threats", []),
        evidence_strength_rationale=result["evidence_strength_rationale"],
        diagnostic_metadata=result.get("diagnostic_metadata"),
    )

