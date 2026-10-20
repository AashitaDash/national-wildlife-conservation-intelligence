from typing import Dict, Any, List
from nlp.preprocessor import TextPreprocessor


class ConservationSummarizer:
    """
    Extractive and structured summarization engine for conservation reports.
    Synthesizes critical operational intelligence (affected species, primary threats,
    geographic locus, and intervention takeaways) from long-form documents.
    """

    @classmethod
    def summarize(
        cls,
        text: str,
        species_info: List[Dict[str, Any]] = None,
        threat_info: List[Dict[str, Any]] = None,
        max_sentences: int = 3
    ) -> Dict[str, Any]:
        """
        Extracts salient sentences and synthesizes structured intelligence bullet points.
        """
        clean_text = TextPreprocessor.clean(text)
        sentences = TextPreprocessor.segment_sentences(clean_text)

        if not sentences:
            return {
                "extractive_summary": "",
                "structured_takeaways": [],
                "sentence_count": 0
            }

        if len(sentences) <= max_sentences:
            extractive = " ".join(sentences)
        else:
            # Score each sentence by entity density, threat keywords, and position
            scored_sentences = []
            for idx, sent in enumerate(sentences):
                score = 0.0
                sent_lower = sent.lower()

                # Position bias: early and closing sentences typically carry findings
                if idx == 0:
                    score += 2.0
                elif idx == len(sentences) - 1:
                    score += 1.5

                # Boost if sentence mentions recognized species
                if species_info:
                    for sp in species_info:
                        if sp["canonical_name"].lower() in sent_lower:
                            score += 2.5

                # Boost if sentence mentions recognized threats
                if threat_info:
                    for th in threat_info:
                        if th["category_name"].lower() in sent_lower:
                            score += 2.0

                scored_sentences.append((score, idx, sent))

            # Select top N sentences ordered by original document flow
            scored_sentences.sort(key=lambda x: x[0], reverse=True)
            top_sentences = scored_sentences[:max_sentences]
            top_sentences.sort(key=lambda x: x[1])
            extractive = " ".join([s[2] for s in top_sentences])

        # Synthesize structured takeaways
        takeaways = []
        if species_info:
            sp_names = ", ".join([s["canonical_name"] for s in species_info[:3]])
            takeaways.append(f"Affected Taxa: {sp_names}")

        if threat_info:
            th_names = ", ".join([t["category_name"] for t in threat_info[:3]])
            takeaways.append(f"Key Threat Drivers: {th_names}")

        return {
            "extractive_summary": extractive,
            "structured_takeaways": takeaways,
            "is_ai_generated": True,
            "original_sentence_count": len(sentences),
            "summary_sentence_count": min(len(sentences), max_sentences)
        }
