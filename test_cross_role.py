import requests
from backend.app.database import SessionLocal
from backend.app.models.submission import ObservationSubmission, VerificationDecision, PointsLedger
from backend.app.models.observation import Observation

BASE = 'http://127.0.0.1:8000/api/v1'

# 1. Login researcher & officer
r_token = requests.post(f'{BASE}/auth/login', json={'email': 'researcher@wildlife.gov.in', 'password': 'Researcher@123'}).json()['access_token']
o_token = requests.post(f'{BASE}/auth/login', json={'email': 'officer@forest.gov.in', 'password': 'Officer@123'}).json()['access_token']
r_hdr = {'Authorization': f'Bearer {r_token}'}
o_hdr = {'Authorization': f'Bearer {o_token}'}

# Get researcher initial stats
prof_init = requests.get(f'{BASE}/gamification/profile/me', headers=r_hdr).json()
initial_pts = prof_init['total_points']
initial_verified = prof_init['verified_count']
print(f'Initial Stats -> Points: {initial_pts}, Verified: {initial_verified}')

# Create isolated sighting
create_payload = {
    'species_id': 1,
    'observed_at': '2026-10-20T14:15:00Z',
    'latitude': 21.65,
    'longitude': 86.34,
    'accuracy_meters': 10.0,
    'description': 'Temporary test sighting for cross-role audit verification.',
    'status': 'DRAFT',
    'citations': []
}
sub_res = requests.post(f'{BASE}/submissions', json=create_payload, headers=r_hdr)
assert sub_res.status_code == 201, f'Creation failed: {sub_res.text}'
sub_id = sub_res.json()['id']
print(f'Created Sighting ID: {sub_id}')

# Transition to PENDING_REVIEW
trans_res = requests.post(f'{BASE}/submissions/{sub_id}/submit', headers=r_hdr)
assert trans_res.status_code == 200, f'Submit failed: {trans_res.text}'
print(f"Submitted for review -> Status: {trans_res.json().get('status')}")

# Officer claims
claim_res = requests.post(f'{BASE}/officer/queue/{sub_id}/claim', headers=o_hdr)
assert claim_res.status_code == 200, f'Claim failed: {claim_res.text}'
print(f"Officer claimed -> Status: {claim_res.json().get('status')}")

# Officer verifies
verify_res = requests.post(f'{BASE}/officer/queue/{sub_id}/verify', json={'note': 'Photographic evidence verified.'}, headers=o_hdr)
assert verify_res.status_code == 200, f'Verification failed: {verify_res.text}'
promoted_obs_id = verify_res.json().get('promoted_observation_id')
print(f'Officer verified -> Promoted Observation ID: {promoted_obs_id}')

# Check researcher updated stats
prof_updated = requests.get(f'{BASE}/gamification/profile/me', headers=r_hdr).json()
new_pts = prof_updated['total_points']
new_verified = prof_updated['verified_count']
print(f'Updated Stats -> Points: {new_pts} (+{new_pts - initial_pts}), Verified: {new_verified}')
assert new_verified == initial_verified + 1, 'Verified count did not increment!'

# Cleanup isolated test record from database
with SessionLocal() as db:
    if promoted_obs_id:
        db.query(Observation).filter(Observation.id == promoted_obs_id).delete()
    db.query(VerificationDecision).filter(VerificationDecision.submission_id == sub_id).delete()
    db.query(PointsLedger).filter(PointsLedger.submission_id == sub_id).delete()
    db.query(ObservationSubmission).filter(ObservationSubmission.id == sub_id).delete()
    db.commit()
print('Cleaned up isolated test records safely from database.')
