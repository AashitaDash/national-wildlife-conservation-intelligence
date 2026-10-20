from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from backend.app.dependencies import get_db, get_current_active_user
from backend.app.models.user import User
from backend.app.schemas.report import (
    ReportType,
    ExportFormat,
    ReportTypeMetadata,
    ReportFilterOptions,
    ReportPreviewRequest,
    ReportPreviewResponse,
    ReportGenerateRequest,
)
from backend.app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Conservation Intelligence Reports"])


@router.get("/types", response_model=List[ReportTypeMetadata])
def get_report_types(
    current_user: User = Depends(get_current_active_user),
):
    """
    List available conservation report templates, supported formats, and valid filters.
    Available to all authenticated personnel.
    """
    return ReportService.get_supported_types()


@router.post("/preview", response_model=ReportPreviewResponse)
def preview_report(
    payload: ReportPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Calculate dynamic scope and summary aggregations before full report generation.
    """
    try:
        preview_data = ReportService.get_preview(payload.report_type, payload.filters, db)
        return ReportPreviewResponse(**preview_data)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report preview: {str(e)}",
        )


@router.post("/generate")
def generate_report(
    payload: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Compile real conservation data and stream the generated file (PDF, CSV, or XLSX).
    """
    try:
        if payload.format == ExportFormat.CSV:
            data_bytes, filename = ReportService.generate_csv(payload.report_type, payload.filters, db)
            media_type = "text/csv; charset=utf-8"
        elif payload.format == ExportFormat.XLSX:
            data_bytes, filename = ReportService.generate_xlsx(payload.report_type, payload.filters, db)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif payload.format == ExportFormat.PDF:
            data_bytes, filename = ReportService.generate_pdf(payload.report_type, payload.filters, db)
            media_type = "application/pdf"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {payload.format}")

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
        return StreamingResponse(io.BytesIO(data_bytes), media_type=media_type, headers=headers)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation error: {str(e)}",
        )
