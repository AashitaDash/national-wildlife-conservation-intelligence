import re
from typing import Dict, Any, List


class TopicClassifier:
    """
    Topic classification engine for conservation reports and incident narratives.
    Utilizes weighted term association vectors to categorize unstructured text
    into functional operational domains.
    """

    TOPIC_VECTORS = {
        "Habitat Loss & Fragmentation": [
            ("habitat", 2.0), ("fragmentation", 3.0), ("corridor", 2.5), ("encroachment", 2.5),
            ("deforestation", 3.0), ("canopy", 1.5), ("severed", 2.0), ("clearance", 2.0)
        ],
        "Human-Wildlife Conflict": [
            ("conflict", 2.5), ("crop", 2.0), ("raiding", 2.5), ("retaliatory", 3.0),
            ("paddy", 2.0), ("depredation", 2.5), ("village", 1.5), ("farmer", 1.5)
        ],
        "Poaching & Illegal Trade": [
            ("poaching", 3.5), ("snare", 3.0), ("trapping", 2.5), ("illegal", 2.0),
            ("tusk", 3.0), ("horn", 3.0), ("carcass", 2.5), ("seized", 2.0), ("arrested", 2.0)
        ],
        "Linear Infrastructure Hazard": [
            ("railway", 3.0), ("highway", 2.5), ("collision", 3.0), ("train", 2.5),
            ("transmission", 2.5), ("electrocution", 3.0), ("powerline", 2.5), ("cable", 2.0)
        ],
        "Population Survey & Biodiversity Census": [
            ("census", 3.0), ("survey", 2.5), ("camera trap", 3.0), ("population", 2.0),
            ("sighting", 2.0), ("density", 2.0), ("individual", 1.5), ("pugmark", 2.5)
        ],
        "Policy, Protection & Reserve Management": [
            ("patrol", 2.5), ("ranger", 2.0), ("sanctuary", 2.0), ("enforcement", 2.5),
            ("drone", 2.0), ("eco-guard", 2.5), ("protocol", 2.0), ("recommendation", 2.0)
        ]
    }

    @classmethod
    def classify(cls, text: str, threshold: float = 0.15) -> List[Dict[str, Any]]:
        """
        Calculates normalized topical probabilities for input text.
        """
        text_lower = text.lower()
        topic_scores = {}

        for topic, vector in cls.TOPIC_VECTORS.items():
            score = 0.0
            for term, weight in vector:
                count = len(re.findall(rf"\b{re.escape(term)}\b", text_lower))
                if count > 0:
                    score += count * weight
            topic_scores[topic] = score

        total_score = sum(topic_scores.values())
        if total_score == 0:
            return [{"topic": "General Conservation Intelligence", "confidence": 1.0}]

        ranked_topics = []
        for topic, raw in topic_scores.items():
            prob = raw / total_score
            if prob >= threshold:
                ranked_topics.append({
                    "topic": topic,
                    "confidence": round(prob, 3)
                })

        ranked_topics.sort(key=lambda x: x["confidence"], reverse=True)
        return ranked_topics

    @classmethod
    def classify_topics(cls, text: str, threshold: float = 0.15) -> List[str]:
        """Convenience method returning list of classified topic names."""
        results = cls.classify(text, threshold=threshold)
        return [r["topic"] for r in results]
