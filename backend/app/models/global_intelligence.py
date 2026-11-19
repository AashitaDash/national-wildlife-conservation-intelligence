from sqlalchemy import Column, Integer
from backend.app.database import Base

class GlobalSourceRegistry(Base):
    """Placeholder model for future global source registry.
    Only a primary key is defined because the current code never accesses
    any other column. This satisfies imports and allows automatic table
    creation via Base.metadata.create_all().
    """
    __tablename__ = "global_source_registry"
    id = Column(Integer, primary_key=True, index=True)

class GlobalIntelligenceRecord(Base):
    """Placeholder model for global intelligence records.
    No fields beyond a primary key are required for the existing
    application – the RAG service only imports the class for typing.
    """
    __tablename__ = "global_intelligence_record"
    id = Column(Integer, primary_key=True, index=True)

