from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ReportType(str, Enum):
    CONSERVATION_OVERVIEW = "CONSERVATION_OVERVIEW"
    SPECIES_CONSERVATION = "SPECIES_CONSERVATION"
    GEOGRAPHIC_INTELLIGENCE = "GEOGRAPHIC_INTELLIGENCE"
    THREAT_RISK_ASSESSMENT = "THREAT_RISK_ASSESSMENT"
    RESEARCH_DOCUMENT_INTELLIGENCE = "RESEARCH_DOCUMENT_INTELLIGENCE"


class ExportFormat(str, Enum):
    PDF = "PDF"
    CSV = "CSV"
    XLSX = "XLSX"


class ReportFilterOptions(BaseModel):
    species_id: Optional[int] = Field(None, description="Target species ID for species report")
    location_id: Optional[int] = Field(None, description="Target protected area / location ID")
    taxonomic_class: Optional[str] = Field(None, description="Mammalia, Aves, Reptilia, Amphibia")
    iucn_category: Optional[str] = Field(None, description="CR, EN, VU, NT, LC")
    threat_category: Optional[str] = Field(None, description="Target threat category name")
    start_date: Optional[str] = Field(None, description="Start date ISO string")
    end_date: Optional[str] = Field(None, description="End date ISO string")
    limit: Optional[int] = Field(1000, description="Max tabular rows to include (default 1000, max 5000)")


class ReportTypeMetadata(BaseModel):
    type_id: ReportType
    name: str
    description: str
    supported_formats: List[ExportFormat]
    available_filters: List[str]


class ReportPreviewRequest(BaseModel):
    report_type: ReportType
    filters: Optional[ReportFilterOptions] = None


class ReportPreviewResponse(BaseModel):
    report_type: ReportType
    title: str
    estimated_records: int
    summary_metrics: Dict[str, Any]
    sections: List[str]
    scientific_limitations: List[str]
    supported_formats: List[ExportFormat]


class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    format: ExportFormat
    filters: Optional[ReportFilterOptions] = None
