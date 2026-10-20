import re
import datetime
from typing import Dict, Any, Optional


class DocumentParser:
    """
    Parser for unstructured conservation literature, field incident dispatches,
    and government reports. Cleans and extracts foundational metadata.
    """

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        Normalizes unstructured text by stripping control characters,
        standardizing line breaks, and collapsing excessive whitespaces.
        """
        if not raw_text:
            return ""
        # Remove control characters except standard whitespace
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw_text)
        # Collapse multiple blank lines
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        # Collapse repeated spaces/tabs
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    @classmethod
    def parse_document(
        cls,
        title: str,
        raw_text: str,
        source_type: str = "GOVERNMENT_REPORT",
        author: Optional[str] = None,
        publication_date: Optional[datetime.datetime] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates, cleans, and packages an unstructured document for database persistence
        and downstream NLP processing.
        """
        cleaned = cls.clean_text(raw_text)
        pub_dt = publication_date or datetime.datetime.now(datetime.timezone.utc)

        return {
            "title": title.strip(),
            "source_type": source_type.upper(),
            "author": author.strip() if author else "Forest Department / Conservation Bureau",
            "publication_date": pub_dt,
            "url": url,
            "raw_text": raw_text.strip(),
            "cleaned_text": cleaned,
            "word_count": len(cleaned.split()),
            "character_count": len(cleaned)
        }
