import pytest
from nlp.preprocessor import TextPreprocessor
from nlp.entity_extractor import EntityExtractor
from nlp.threat_matcher import ThreatMatcher
from nlp.topic_classifier import TopicClassifier
from nlp.summarizer import ConservationSummarizer
from nlp.embeddings import VectorEmbedder


def test_text_preprocessor():
    raw = "  Severe   snaring \x00 in Similipal national park...  "
    clean = TextPreprocessor.clean(raw)
    assert "\x00" not in clean
    assert clean == "Severe snaring in Similipal national park..."

    sentences = TextPreprocessor.segment_sentences("Tuskers entered the village. Farmers alerted forest rangers! Patrol deployed.")
    assert len(sentences) == 3

    tokens = TextPreprocessor.tokenize("Asian elephant in Similipal", remove_stopwords=True)
    assert "asian" in tokens
    assert "elephant" in tokens
    assert "in" not in tokens


def test_section_13_example_transformation():
    """
    Validates Section 13 of the project specification:
    Input: "Recent elephant sightings have increased around Similipal due to habitat fragmentation and agricultural expansion."
    Expected output:
      Species: Asian Elephant
      Location: Similipal
      Threats: Habitat Fragmentation, Agricultural Expansion
      Topic: Habitat Loss
    """
    text = "Recent elephant sightings have increased around Similipal due to habitat fragmentation and agricultural expansion."

    # 1. NER Extraction
    extractor = EntityExtractor()
    entities = extractor.extract_entities(text)

    species_names = [s["canonical_name"] for s in entities["species"]]
    location_names = [l["canonical_name"] for l in entities.get("locations", [])] + [
        p["canonical_name"] for p in entities.get("protected_areas", [])
    ]

    assert "Asian Elephant" in species_names
    assert any("Similipal" in loc for loc in location_names)

    # 2. Threat Extraction
    threats = ThreatMatcher.extract_threats(text)
    threat_categories = [t["category_name"] for t in threats]

    assert "Habitat Fragmentation & Encroachment" in threat_categories
    assert "Agricultural Expansion & Deforestation" in threat_categories

    # 3. Topic Classification
    topics = TopicClassifier.classify(text)
    top_topic = topics[0]["topic"]

    assert "Habitat" in top_topic or "Human-Wildlife Conflict" in top_topic

    # 4. Summarization
    summary = ConservationSummarizer.summarize(text, entities["species"], threats)
    assert summary["is_ai_generated"] is True
    assert len(summary["structured_takeaways"]) >= 2


def test_vector_embeddings_and_cosine_ranking():
    text_a = "Elephant migration corridors in Similipal"
    text_b = "Asian elephants traversing forested landscapes"
    text_unrelated = "Marine coral reef bleached in deep oceanic shelf"

    emb_a = VectorEmbedder.encode(text_a)
    emb_b = VectorEmbedder.encode(text_b)
    emb_unrelated = VectorEmbedder.encode(text_unrelated)

    assert len(emb_a) == 384
    assert len(emb_b) == 384

    # Related documents should have higher cosine similarity than unrelated ones
    sim_related = VectorEmbedder.cosine_similarity(emb_a, emb_b)
    sim_unrelated = VectorEmbedder.cosine_similarity(emb_a, emb_unrelated)

    assert sim_related > sim_unrelated

    # Test document ranking
    docs = [
        {"id": 1, "cleaned_text": text_unrelated},
        {"id": 2, "cleaned_text": text_b}
    ]
    ranked = VectorEmbedder.rank_documents(emb_a, docs)
    assert ranked[0]["id"] == 2

