import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Document(Base):
    """
    Unstructured conservation document, research paper, forest incident dispatch,
    or public conservation article with extracted NLP intelligence and dense vector representations.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False, index=True)
    source_type = Column(String(100), nullable=False, index=True)  # RESEARCH_PAPER, GOVT_REPORT, INCIDENT_LOG, ARTICLE
    author = Column(String(200), nullable=True)
    publication_date = Column(DateTime, nullable=True)
    url = Column(String(500), nullable=True)

    raw_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    topics = Column(JSON, nullable=True)  # Extracted topic tags
    
    # 384-dimensional dense vector stored as JSON array (and pgvector compatible)
    embedding_json = Column(JSON, nullable=True)

    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    author_user = relationship("User", back_populates="documents_authored")
    species_mentions = relationship("DocumentSpecies", back_populates="document", cascade="all, delete-orphan")
    threat_mentions = relationship("DocumentThreat", back_populates="document", cascade="all, delete-orphan")
    nlp_results = relationship("NLPAnalysisResult", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title[:30]}...', type='{self.source_type}')>"


class DocumentSpecies(Base):
    """
    Associative table linking documents to extracted species mentions and frequency counts.
    """
    __tablename__ = "document_species"

    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    species_id = Column(Integer, ForeignKey("species.id", ondelete="CASCADE"), primary_key=True)
    mention_count = Column(Integer, default=1)

    document = relationship("Document", back_populates="species_mentions")
    species = relationship("Species", back_populates="document_associations")


class DocumentThreat(Base):
    """
    Associative table linking documents to extracted threat categories with extraction confidence.
    """
    __tablename__ = "document_threats"

    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    threat_id = Column(Integer, ForeignKey("threats.id", ondelete="CASCADE"), primary_key=True)
    confidence_score = Column(Float, default=1.0)

    document = relationship("Document", back_populates="threat_mentions")
    threat = relationship("Threat", back_populates="document_associations")


class NLPAnalysisResult(Base):
    """
    Audit log storing linguistic extraction artifacts from spaCy and transformer pipelines.
    """
    __tablename__ = "nlp_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    extracted_entities = Column(JSON, nullable=True)  # species, locations, organizations, dates
    topics = Column(JSON, nullable=True)
    raw_meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    document = relationship("Document", back_populates="nlp_results")
