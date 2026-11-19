import re
from typing import List


class TextPreprocessor:
    """
    Standard preprocessing, sentence boundary segmentation,
    and tokenization utility for conservation text processing.
    """

    STOPWORDS = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
        "did", "do", "does", "doing", "don't", "down", "during", "each", "few", "for",
        "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
        "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
        "it", "its", "itself", "more", "most", "my", "myself", "no", "nor", "not",
        "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
        "ourselves", "out", "over", "own", "same", "she", "should", "so", "some",
        "such", "than", "that", "the", "their", "theirs", "them", "themselves",
        "then", "there", "these", "they", "this", "those", "through", "to", "too",
        "under", "until", "up", "very", "was", "we", "were", "what", "when", "where",
        "which", "while", "who", "whom", "why", "with", "would", "you", "your", "yours"
    }

    @staticmethod
    def clean(text: str) -> str:
        """
        Removes non-printable characters, standardizes quotes and dashes,
        and collapses irregular whitespace.
        """
        if not text:
            return ""
        # Remove non-ASCII control characters
        t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Normalize typographic quotes and dashes
        t = t.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        t = t.replace("—", " - ").replace("–", " - ")
        # Collapse whitespace
        t = re.sub(r"\s+", " ", t)
        return t.strip()

    clean_text = clean

    @staticmethod
    def segment_sentences(text: str) -> List[str]:
        """
        Splits clean text into individual sentences using punctuation boundary rules,
        preserving standard abbreviations like 'Dr.', 'Fig.', 'e.g.', 'sp.'.
        """
        if not text:
            return []
        # Protect common scientific and linguistic abbreviations
        protected = text
        abbrevs = ["Dr.", "Mr.", "Mrs.", "Fig.", "e.g.", "i.e.", "sp.", "subsp.", "al."]
        for i, abbr in enumerate(abbrevs):
            protected = protected.replace(abbr, f"__ABBR_{i}__")

        # Split on standard terminal sentence delimiters followed by whitespace/capital
        raw_sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"])", protected)

        sentences = []
        for s in raw_sentences:
            s_clean = s.strip()
            # Restore protected abbreviations
            for i, abbr in enumerate(abbrevs):
                s_clean = s_clean.replace(f"__ABBR_{i}__", abbr)
            if len(s_clean) > 3:
                sentences.append(s_clean)

        return sentences

    @classmethod
    def tokenize(cls, text: str, remove_stopwords: bool = False, lowercase: bool = True) -> List[str]:
        """
        Extracts alphanumeric tokens with optional lowercasing and stopword removal.
        """
        if lowercase:
            text = text.lower()
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text)
        if remove_stopwords:
            tokens = [tok for tok in tokens if tok.lower() not in cls.STOPWORDS]
        return tokens

    @staticmethod
    def segment_sections(text: str) -> List[dict]:
        """
        Splits text into logical document sections (Abstract, Intro, Body, Conclusion).
        Returns a list of dicts with section name and text.
        """
        if not text:
            return [{"section": "BODY", "text": ""}]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]
        sections = []
        for idx, p in enumerate(paragraphs):
            sec_type = "BODY"
            if idx == 0 and len(paragraphs) > 1:
                sec_type = "ABSTRACT" if "abstract" in p.lower() else "INTRODUCTION"
            sections.append({"section": sec_type, "text": p})
        return sections

    @staticmethod
    def classify_document_type(text: str, title: str = "") -> str:
        """
        Categorizes document as INCIDENT_LOG, FIELD_REPORT, RESEARCH_PAPER, or GENERAL_CONSERVATION_DOC.
        """
        combined = f"{title} {text}".lower()
        if any(w in combined for w in ["incident", "poaching", "corridor", "encounter", "arrest", "seizure", "fir"]):
            return "INCIDENT_LOG"
        elif any(w in combined for w in ["field report", "survey", "census", "monitoring", "sighting"]):
            return "FIELD_REPORT"
        elif any(w in combined for w in ["abstract", "methodology", "study", "analysis", "journal", "published"]):
            return "RESEARCH_PAPER"
        return "GENERAL_CONSERVATION_DOC"


