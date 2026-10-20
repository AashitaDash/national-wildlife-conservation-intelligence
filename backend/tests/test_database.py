import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import (
    Role, User, Species, Location, DataSource, Observation,
    Threat, Document, DocumentSpecies, DocumentThreat,
    MLRiskScore, MLAnomaly, ConservationAlert, UserAlert
)

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def db_session():
    """
    Creates an isolated in-memory test database session with all tables.
    """
    test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_role_and_user_creation(db_session):
    # Create Role
    researcher_role = Role(name="RESEARCHER", description="Academic and field researcher")
    db_session.add(researcher_role)
    db_session.commit()
    db_session.refresh(researcher_role)

    assert researcher_role.id is not None
    assert researcher_role.name == "RESEARCHER"

    # Create User associated with Role
    user = User(
        email="researcher@wildlife.org",
        hashed_password="fake_hashed_pw",
        full_name="Dr. Aris Thorne",
        organization="Wildlife Institute of India",
        role_id=researcher_role.id
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.role.name == "RESEARCHER"
    assert len(researcher_role.users) == 1


def test_species_and_observation_creation(db_session):
    # 1. Species
    elephant = Species(
        scientific_name="Elephas maximus",
        common_name="Asian Elephant",
        order_name="Proboscidea",
        family="Elephantidae",
        iucn_category="EN",
        description="Endangered megaherbivore native to the Indian subcontinent and Southeast Asia."
    )
    db_session.add(elephant)
    db_session.commit()
    db_session.refresh(elephant)

    assert elephant.id is not None
    assert elephant.iucn_category == "EN"

    # 2. Location
    similipal = Location(
        name="Similipal Tiger Reserve",
        state="Odisha",
        district="Mayurbhanj",
        protected_area_type="Tiger Reserve",
        latitude=21.6667,
        longitude=86.3333,
        area_sq_km=2750.0
    )
    db_session.add(similipal)

    # 3. Data Source
    gbif = DataSource(name="GBIF", url="https://api.gbif.org", description="Global Biodiversity Information Facility")
    db_session.add(gbif)
    db_session.commit()
    db_session.refresh(similipal)
    db_session.refresh(gbif)

    # 4. Observation
    obs = Observation(
        species_id=elephant.id,
        location_id=similipal.id,
        source_id=gbif.id,
        observed_at=datetime.datetime.now(datetime.timezone.utc),
        latitude=21.6700,
        longitude=86.3400,
        accuracy_meters=15.0,
        verification_status="VERIFIED",
        notes="Herd of 4 individuals observed near buffer corridor."
    )
    db_session.add(obs)
    db_session.commit()
    db_session.refresh(obs)

    assert obs.id is not None
    assert obs.species.common_name == "Asian Elephant"
    assert obs.location.name == "Similipal Tiger Reserve"
    assert obs.source.name == "GBIF"


def test_threat_and_document_association(db_session):
    # 1. Threat
    poaching = Threat(
        category_name="Poaching & Snaring",
        iucn_threat_code="5.1.1",
        severity_weight=2.5,
        description="Intentional illegal hunting or capturing of wildlife."
    )
    db_session.add(poaching)
    db_session.commit()
    db_session.refresh(poaching)

    # 2. Document
    doc = Document(
        title="Similipal Conservation Dispatch: Snaring Incidents in Southern Corridor",
        source_type="GOVERNMENT_REPORT",
        raw_text="Field rangers intercepted illegal snaring equipment across Mayurbhanj district.",
        cleaned_text="Field rangers intercepted illegal snaring equipment across Mayurbhanj district.",
        summary="Interception of snaring equipment within the southern buffer zone."
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    # 3. Associate Document with Threat
    doc_threat = DocumentThreat(
        document_id=doc.id,
        threat_id=poaching.id,
        confidence_score=0.95
    )
    db_session.add(doc_threat)
    db_session.commit()

    assert len(doc.threat_mentions) == 1
    assert doc.threat_mentions[0].threat.category_name == "Poaching & Snaring"


def test_ml_outputs_and_alerts(db_session):
    species = db_session.query(Species).filter_by(scientific_name="Elephas maximus").first()
    location = db_session.query(Location).filter_by(name="Similipal Tiger Reserve").first()

    # 1. Risk Score
    risk = MLRiskScore(
        species_id=species.id,
        region_name="Odisha",
        composite_score=78.5,
        risk_level="HIGH",
        observation_frequency=12.0,
        threat_density=4.5,
        temporal_trend=-0.22,
        feature_snapshot={"hwc_mentions": 8, "fragmentation_index": 0.65}
    )
    db_session.add(risk)

    # 2. Anomaly
    anomaly = MLAnomaly(
        species_id=species.id,
        location_id=location.id,
        anomaly_type="INCIDENT_SURGE",
        anomaly_score=-0.412,
        is_anomaly=True,
        explanation="Sudden spike in snaring encounters detected over past 7 days."
    )
    db_session.add(anomaly)

    # 3. Alert
    alert = ConservationAlert(
        title="Elevated Risk Alert: Asian Elephant in Odisha",
        severity="HIGH",
        alert_type="RISK_THRESHOLD",
        message="Risk score crossed 75 threshold (Current: 78.5/100).",
        species_id=species.id,
        location_id=location.id
    )
    db_session.add(alert)
    db_session.commit()

    db_session.refresh(risk)
    db_session.refresh(anomaly)
    db_session.refresh(alert)

    assert risk.id is not None
    assert risk.composite_score == 78.5
    assert anomaly.anomaly_type == "INCIDENT_SURGE"
    assert alert.severity == "HIGH"
    assert alert.species.common_name == "Asian Elephant"
