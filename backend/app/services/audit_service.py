"""
Audit Service — append-only event logging for security-sensitive operations.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.models.submission import AuditEvent

logger = logging.getLogger(__name__)


class AuditService:
    """
    Creates immutable audit events. Never updates or deletes rows.
    Silently logs errors rather than crashing the main request — audit failures
    must never block the primary operation.
    """

    @staticmethod
    def log(
        db: Session,
        action: str,
        actor_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append a single audit event.

        Parameters
        ----------
        action      : Short uppercase verb, e.g. "SUBMISSION_VERIFIED", "ROLE_CHANGED"
        actor_id    : User ID performing the action (None for system events)
        entity_type : "SUBMISSION", "USER", "OBSERVATION", etc.
        entity_id   : Primary key of the entity
        metadata    : Non-sensitive JSON-serialisable context (never include passwords,
                      tokens, or private keys)
        """
        try:
            event = AuditEvent(
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                event_metadata=metadata or {},
            )
            db.add(event)
            db.flush()
        except Exception as exc:
            # Roll back only the failed audit flush so the calling transaction
            # can still commit its primary change (audit failure must never
            # block the primary operation).
            try:
                db.rollback()
            except Exception:
                pass
            logger.error("Failed to write audit event [%s]: %s", action, exc)
