"""
Seed Demonstration Dataset for Wildlife Conservation Intelligence Platform
===========================================================================
Creates a coherent, interconnected, realistic demonstration dataset:
- Standard Demo Users (2 Admins, 3 Researchers, 2 Forest Officers) with safe TestPassword123! credentials.
- 7 Demonstration Wildlife Submissions spanning all workflow states:
  * 2 PENDING_REVIEW (awaiting officer inspection)
  * 1 UNDER_REVIEW (claimed by an officer)
  * 1 MORE_INFO_NEEDED (officer requested revisions + clarification)
  * 2 VERIFIED (promoted to official Observations table, points & badges awarded)
  * 1 REJECTED (unsupported sighting with officer rejection justification)
- Explicit DEMO/TEST DATA attribution tag on all demonstration records.
- Complete idempotency: safe to rerun multiple times without duplicating points, users, or records.
"""
from __future__ import annotations

import datetime
import os
import sys

# Ensure project root is in Python path so 'backend.app.*' imports resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models.user import User, Role
from backend.app.models.species import Species
from backend.app.models.location import Location
from backend.app.models.observation import Observation, DataSource
from backend.app.models.submission import (
    ObservationSubmission,
    SubmissionImage,
    VerificationDecision,
    PointsLedger,
    BadgeDefinition,
    UserBadge,
    Notification,
    AuditEvent,
)
from backend.app.services.auth_service import AuthService
from backend.app.services.gamification_service import GamificationService, seed_badges, seed_roles
from backend.app.config import settings

DEMO_TAG = "[DEMO/TEST DATA]"
DEFAULT_DEMO_PASSWORD = "TestPassword123!"

# Canonical per-role demo passwords (must match run_platform.bat + test fixtures)
ROLE_PASSWORDS = {
    "ADMIN": "Admin@123",
    "RESEARCHER": "Researcher@123",
    "FOREST_OFFICER": "Officer@123",
    "CITIZEN": "Citizen@123",
    "NGO": "Ngo@123",
}


def seed_demo_users(db: Session) -> dict[str, User]:
    """
    Ensure all demo users exist with standard test password.
    Returns dictionary mapping email to User object.
    """
    seed_roles(db)
    roles = {r.name: r for r in db.query(Role).all()}

    demo_user_specs = [
        # Canonical 4 Primary Demo Roles (matching run_platform.bat and UI presets)
        {
            "email": "admin@wildlife.gov.in",
            "username": "admin",
            "full_name": "National Surveillance Director",
            "role": "ADMIN",
            "organization": "Ministry of Environment, Forest & Climate Change",
        },
        {
            "email": "officer@forest.gov.in",
            "username": "officer",
            "full_name": "Ranger Sharma (Field Inspector)",
            "role": "FOREST_OFFICER",
            "organization": "Tiger Reserve Command",
        },
        {
            "email": "researcher@wildlife.gov.in",
            "username": "researcher",
            "full_name": "Priya Nambiar (Field Biologist)",
            "role": "RESEARCHER",
            "organization": "Aaranyak Biodiversity Initiative",
        },
        {
            "email": "citizen@gmail.com",
            "username": "citizen",
            "full_name": "Aarav Sharma (Nature Observer)",
            "role": "CITIZEN",
            "organization": "Community Wildlife Observer",
        },
        # Additional supporting accounts with distinct non-colliding usernames
        {
            "email": "admin@wildlife.com",
            "username": "admin_sen",
            "full_name": "Dr. Rajeshwar Sen (Admin)",
            "role": "ADMIN",
            "organization": "Wildlife Institute of India",
        },
        {
            "email": "researcher@wildlife.com",
            "username": "researcher_roy",
            "full_name": "Dr. Ananya Roy (Lead Researcher)",
            "role": "RESEARCHER",
            "organization": "Centre for Wildlife Studies",
        },
        {
            "email": "researcher_test@wildlife.gov.in",
            "username": "researcher_salim",
            "full_name": "Dr. Salim Researcher",
            "role": "RESEARCHER",
            "organization": "Bombay Natural History Society",
        },
        {
            "email": "officer@wildlife.com",
            "username": "officer_rathore",
            "full_name": "Vikram Rathore (Divisional Forest Officer)",
            "role": "FOREST_OFFICER",
            "organization": "State Forest Department",
        },
        {
            "email": "public@wildlife.org",
            "username": "public_observer",
            "full_name": "Neha Patel (Public Contributor)",
            "role": "CITIZEN",
            "organization": "General Public / Citizen Science",
        },
        {
            "email": "ngo@wwfindia.org",
            "username": "ngo",
            "full_name": "Sunita Rao (Conservation Lead)",
            "role": "NGO",
            "organization": "WWF India Biodiversity Division",
        },
    ]

    users = {}
    now = datetime.datetime.now(datetime.timezone.utc)

    for spec in demo_user_specs:
        user = db.query(User).filter(User.email == spec["email"]).first()
        role = roles.get(spec["role"])
        if not role:
            raise RuntimeError(f"Role {spec['role']} not found in database.")

        desired_username = spec.get("username") or spec["email"].split("@")[0]
        if not user:
            pwd = ROLE_PASSWORDS.get(spec["role"], DEFAULT_DEMO_PASSWORD)
            user = User(
                username=desired_username,
                email=spec["email"],
                hashed_password=AuthService.hash_password(pwd),
                full_name=spec["full_name"],
                organization=spec["organization"],
                role_id=role.id,
                is_active=True,
                is_suspended=False,
                approval_status="APPROVED",
                last_active_at=now,
            )
            db.add(user)
            db.flush()
        else:
            pwd = ROLE_PASSWORDS.get(spec["role"], DEFAULT_DEMO_PASSWORD)
            user.full_name = spec["full_name"]
            if not getattr(user, "username", None):
                user.username = desired_username
            user.organization = spec["organization"]
            user.role_id = role.id
            user.hashed_password = AuthService.hash_password(pwd)
            user.is_active = True
            user.is_suspended = False
            user.approval_status = "APPROVED"
            user.last_active_at = now
            db.flush()

        users[spec["email"]] = user

    db.commit()
    return users


def get_or_create_data_source(db: Session) -> DataSource:
    source = db.query(DataSource).filter(DataSource.name == "Researcher Submission").first()
    if not source:
        source = DataSource(
            name="Researcher Submission",
            description="Verified researcher sighting submitted through the platform",
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def seed_demo_submissions(db: Session, users: dict[str, User]) -> list[ObservationSubmission]:
    """
    Seed 7 distinct demonstration submissions across various statuses.
    Ensures idempotency based on unique identifying tags in description.
    """
    source = get_or_create_data_source(db)
    seed_badges(db)

    # Resolve target species
    sp_elephant = db.query(Species).filter(Species.common_name == "Asian Elephant").first()
    sp_tiger = db.query(Species).filter(Species.common_name == "Bengal Tiger").first()
    sp_leopard = db.query(Species).filter(Species.common_name == "Indian Leopard").first()
    sp_gharial = db.query(Species).filter(Species.common_name == "Gharial").first()
    sp_bustard = db.query(Species).filter(Species.common_name == "Great Indian Bustard").first()
    sp_peafowl = db.query(Species).filter(Species.common_name == "Indian Peafowl").first()
    sp_snow = db.query(Species).filter(Species.common_name == "Snow Leopard").first()

    # Resolve locations
    loc_similipal = db.query(Location).filter(Location.name == "Similipal Tiger Reserve").first()
    loc_corbett = db.query(Location).filter(Location.name == "Jim Corbett National Park").first()
    loc_kaziranga = db.query(Location).filter(Location.name == "Kaziranga National Park").first()
    loc_sundarbans = db.query(Location).filter(Location.name == "Sundarbans National Park").first()
    loc_desert = db.query(Location).filter(Location.name == "Desert National Park").first()
    loc_satkosia = db.query(Location).filter(Location.name == "Satkosia Gorge Sanctuary").first()

    u_ananya = users["researcher@wildlife.com"]
    u_priya = users["researcher@wildlife.gov.in"]
    u_salim = users["researcher_test@wildlife.gov.in"]

    u_rathore = users["officer@wildlife.com"]
    u_sharma = users["officer@forest.gov.in"]

    now = datetime.datetime.now(datetime.timezone.utc)

    # Demonstration specs
    demo_specs = [
        # 1. PENDING_REVIEW (by Ananya)
        {
            "tag": "DEMO-SUB-01",
            "researcher": u_ananya,
            "species": sp_elephant,
            "location": loc_similipal,
            "observed_at": now - datetime.timedelta(days=2, hours=4),
            "lat": 21.6780,
            "lon": 86.3420,
            "status": "PENDING_REVIEW",
            "description": f"{DEMO_TAG} [DEMO-SUB-01] Adult female Asian Elephant with juvenile calf feeding near core buffer zone perimeter. Healthy body condition observed.",
            "habitat_notes": "Dense moist deciduous forest near seasonal stream bank.",
            "behavior_notes": "Active foraging and dust bathing. Maternal vigilance behavior noted.",
            "identification_notes": "Prominent ear depigmentation pattern photographed from 45m distance.",
            "citations": ["https://doi.org/10.1016/j.biocon.2025.109821"],
            "image_url": sp_elephant.image_url if sp_elephant else None,
        },
        # 2. PENDING_REVIEW (by Priya)
        {
            "tag": "DEMO-SUB-02",
            "researcher": u_priya,
            "species": sp_bustard,
            "location": loc_desert,
            "observed_at": now - datetime.timedelta(days=3, hours=1),
            "lat": 26.8520,
            "lon": 70.5280,
            "status": "PENDING_REVIEW",
            "description": f"{DEMO_TAG} [DEMO-SUB-02] Solitary male Great Indian Bustard performing courtship display on protected grassland enclosure.",
            "habitat_notes": "Arid open grassland with sparse scrub vegetation.",
            "behavior_notes": "Inflating gular pouch, resonant booming calls recorded at dawn.",
            "identification_notes": "Black crown and white neck markings distinct.",
            "citations": ["https://doi.org/10.1007/s10531-024-02844-3"],
            "image_url": sp_bustard.image_url if sp_bustard else None,
        },
        # 3. UNDER_REVIEW (by Priya, claimed by Rathore)
        {
            "tag": "DEMO-SUB-03",
            "researcher": u_priya,
            "species": sp_tiger,
            "location": loc_corbett,
            "observed_at": now - datetime.timedelta(days=4, hours=6),
            "lat": 29.5350,
            "lon": 78.7820,
            "status": "UNDER_REVIEW",
            "description": f"{DEMO_TAG} [DEMO-SUB-03] Prime adult male Bengal Tiger crossing secondary riverbed transect during evening patrol.",
            "habitat_notes": "Riparian riverine corridor adjacent to mixed sal woodlands.",
            "behavior_notes": "Scent marking territory on terminalia tree trunk.",
            "identification_notes": "Stripe pattern on left flank matches regional camera-trap database individual T-42.",
            "citations": ["https://doi.org/10.1111/cobi.14201"],
            "image_url": sp_tiger.image_url if sp_tiger else None,
            "claim_officer": u_rathore,
        },
        # 4. MORE_INFO_NEEDED (by Salim, reviewed by Sharma)
        {
            "tag": "DEMO-SUB-04",
            "researcher": u_salim,
            "species": sp_gharial,
            "location": loc_satkosia,
            "observed_at": now - datetime.timedelta(days=5, hours=3),
            "lat": 20.5890,
            "lon": 84.8410,
            "status": "MORE_INFO_NEEDED",
            "description": f"{DEMO_TAG} [DEMO-SUB-04] Subadult Gharial resting on exposed sandy bank in Mahanadi river gorge.",
            "habitat_notes": "Deep riverine pool with undisturbed sandbar.",
            "behavior_notes": "Thermoregulatory mouth-gaping behavior during midday heat.",
            "identification_notes": "Elongated snout with partial ghara bud formation.",
            "citations": [],
            "image_url": sp_gharial.image_url if sp_gharial else None,
            "decision_officer": u_sharma,
            "decision_note": "Please attach higher-resolution photographs of snout morphology and GPS waypoint timestamp log to verify non-overlap with captive release batch.",
        },
        # 5. VERIFIED (by Ananya, verified by Rathore) -> Promoted observation & points
        {
            "tag": "DEMO-SUB-05",
            "researcher": u_ananya,
            "species": sp_tiger,
            "location": loc_sundarbans,
            "observed_at": now - datetime.timedelta(days=8, hours=5),
            "lat": 21.9540,
            "lon": 88.9040,
            "status": "VERIFIED",
            "description": f"{DEMO_TAG} [DEMO-SUB-05] Tigress with two 6-month-old cubs observed navigating mudflat mangrove edge at low tide.",
            "habitat_notes": "Tidal mangrove swamp characterized by dense Sundari and Gewa cover.",
            "behavior_notes": "Slow movement across tidal creek, teaching young cubs to traverse mudflats.",
            "identification_notes": "Distinct double Y-stripe over right eye. PUG marks cast in plaster by accompanying team.",
            "citations": [
                "https://doi.org/10.1017/S003060532400012X",
                "WII/Sundarbans/Tech-Report-2026/04",
            ],
            "image_url": sp_tiger.image_url if sp_tiger else None,
            "decision_officer": u_rathore,
            "decision_note": "Photographic evidence, pugmark casts, and tidal GPS log confirmed authentic and verified against patrol logs.",
        },
        # 6. VERIFIED (by Priya, verified by Sharma) -> Promoted observation & points
        {
            "tag": "DEMO-SUB-06",
            "researcher": u_priya,
            "species": sp_leopard,
            "location": loc_kaziranga,
            "observed_at": now - datetime.timedelta(days=10, hours=2),
            "lat": 26.6710,
            "lon": 93.3560,
            "status": "VERIFIED",
            "description": f"{DEMO_TAG} [DEMO-SUB-06] Adult Indian Leopard resting on high bough of silk cotton tree overlooking floodplain corridor.",
            "habitat_notes": "Semi-evergreen riparian woodland bordering tall alluvial grassland.",
            "behavior_notes": "Resting after successful night hunt. Clean rosette patterns clearly documented.",
            "identification_notes": "Unique broken rosette cluster behind left ear pinna.",
            "citations": ["https://doi.org/10.1007/s10344-025-01891-2"],
            "image_url": sp_leopard.image_url if sp_leopard else None,
            "decision_officer": u_sharma,
            "decision_note": "Rosette cluster confirmed in registry. Location metadata consistent with high-canopy monitoring station.",
        },
        # 7. REJECTED (by Salim, rejected by Rathore)
        {
            "tag": "DEMO-SUB-07",
            "researcher": u_salim,
            "species": sp_snow,
            "location": loc_similipal,  # Plausibility check: Snow Leopard does not occur in Similipal (Odisha)!
            "observed_at": now - datetime.timedelta(days=12, hours=1),
            "lat": 21.6667,
            "lon": 86.3333,
            "status": "REJECTED",
            "description": f"{DEMO_TAG} [DEMO-SUB-07] Purported sighting of Snow Leopard in tropical Similipal hills.",
            "habitat_notes": "Dense tropical moist deciduous canopy.",
            "behavior_notes": "Brief fleabite glimpse in heavy undergrowth.",
            "identification_notes": "Spotted coat observed through foliage; uncertain species attribution.",
            "citations": [],
            "image_url": sp_snow.image_url if sp_snow else None,
            "decision_officer": u_rathore,
            "decision_note": "Rejection: Extreme biogeographical impossibility. Snow Leopard (Panthera uncia) is strictly high-altitude Himalayan (>3000m). Likely misidentification of Indian Leopard (Panthera pardus) or Fishing Cat.",
        },
    ]

    seeded_submissions = []

    for spec in demo_specs:
        if not spec["species"]:
            continue

        existing_sub = (
            db.query(ObservationSubmission)
            .filter(ObservationSubmission.description.ilike(f"%{spec['tag']}%"))
            .first()
        )

        if not existing_sub:
            sub = ObservationSubmission(
                researcher_id=spec["researcher"].id,
                species_id=spec["species"].id,
                location_id=spec["location"].id if spec.get("location") else None,
                observed_at=spec["observed_at"],
                latitude=spec["lat"],
                longitude=spec["lon"],
                accuracy_meters=15.0,
                description=spec["description"],
                habitat_notes=spec.get("habitat_notes"),
                behavior_notes=spec.get("behavior_notes"),
                identification_notes=spec.get("identification_notes"),
                citations=spec.get("citations", []),
                status=spec["status"],
            )
            db.add(sub)
            db.flush()

            # Attach evidence image placeholder if provided
            if spec.get("image_url"):
                img = SubmissionImage(
                    submission_id=sub.id,
                    file_path=spec["image_url"],
                    original_filename=f"{spec['tag']}_field_capture.jpg",
                    mime_type="image/jpeg",
                    file_size_bytes=1024 * 340,
                )
                db.add(img)
                db.flush()

            # Handle decisions & state-specific relations
            if spec["status"] == "UNDER_REVIEW" and spec.get("claim_officer"):
                dec = VerificationDecision(
                    submission_id=sub.id,
                    officer_id=spec["claim_officer"].id,
                    action="CLAIM",
                    note=f"Claimed for officer review by {spec['claim_officer'].full_name}",
                    decided_at=sub.observed_at + datetime.timedelta(hours=6),
                )
                db.add(dec)

            elif spec["status"] == "MORE_INFO_NEEDED" and spec.get("decision_officer"):
                dec = VerificationDecision(
                    submission_id=sub.id,
                    officer_id=spec["decision_officer"].id,
                    action="REQUEST_MORE_INFO",
                    note=spec.get("decision_note", "Additional evidence requested."),
                    decided_at=sub.observed_at + datetime.timedelta(hours=12),
                )
                db.add(dec)

            elif spec["status"] == "REJECTED" and spec.get("decision_officer"):
                dec = VerificationDecision(
                    submission_id=sub.id,
                    officer_id=spec["decision_officer"].id,
                    action="REJECT",
                    note=spec.get("decision_note", "Evidence rejected."),
                    decided_at=sub.observed_at + datetime.timedelta(hours=8),
                )
                db.add(dec)

            elif spec["status"] == "VERIFIED" and spec.get("decision_officer"):
                # 1. Promote to official observations table
                obs = Observation(
                    species_id=sub.species_id,
                    location_id=sub.location_id,
                    submitted_by_user_id=sub.researcher_id,
                    source_id=source.id,
                    observed_at=sub.observed_at,
                    latitude=sub.latitude,
                    longitude=sub.longitude,
                    accuracy_meters=sub.accuracy_meters,
                    verification_status="VERIFIED",
                    notes=f"{DEMO_TAG} Verified researcher submission: {sub.description}",
                    raw_metadata={
                        "demo_tag": spec["tag"],
                        "submission_id": sub.id,
                        "verified_by": spec["decision_officer"].id,
                        "citations": sub.citations or [],
                    },
                )
                db.add(obs)
                db.flush()
                sub.promoted_observation_id = obs.id

                # 2. Add verification decision
                dec = VerificationDecision(
                    submission_id=sub.id,
                    officer_id=spec["decision_officer"].id,
                    action="VERIFY",
                    note=spec.get("decision_note", "Verified and promoted."),
                    decided_at=sub.observed_at + datetime.timedelta(hours=14),
                )
                db.add(dec)

                # 3. Process gamification rewards
                GamificationService.process_verification_rewards(db, sub)

            db.commit()
            db.refresh(sub)
            seeded_submissions.append(sub)
        else:
            seeded_submissions.append(existing_sub)

    return seeded_submissions


def seed_demo_data():
    """Main entrypoint for idempotent demonstration dataset seeding."""
    db = SessionLocal()
    try:
        print("1. Seeding demo users across roles (ADMIN, RESEARCHER, FOREST_OFFICER)...")
        users = seed_demo_users(db)
        print(f"   Created / synchronized {len(users)} demo accounts with standard credentials.")

        print("2. Seeding 7 structured demonstration submissions across lifecycle states...")
        subs = seed_demo_submissions(db, users)
        print(f"   Synchronized {len(subs)} demonstration submissions with explicit demo tagging.")

        print("3. Verification and summary counts (DEMO submissions only):")
        for status in ["PENDING_REVIEW", "UNDER_REVIEW", "MORE_INFO_NEEDED", "VERIFIED", "REJECTED"]:
            count = (
                db.query(ObservationSubmission)
                .filter(
                    ObservationSubmission.status == status,
                    ObservationSubmission.description.ilike(f"%{DEMO_TAG}%"),
                )
                .count()
            )
            print(f"   - {status}: {count} demo submissions")

        leaderboard = GamificationService.get_researcher_profile(db, users["researcher@wildlife.com"].id)
        print(f"   - Lead Researcher points: {leaderboard['total_points']}, rank: {leaderboard['level']}, badges: {len(leaderboard['badges'])}")

        print("\nDemonstration seeding completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()

