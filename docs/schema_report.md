# NWCIP Database Schema Report

## Reflected Database Schema

### Table `audit_events`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ | ✔ |  |
| actor_id | INTEGER |  | ✔ |  |
| action | VARCHAR(100) |  |  |  |
| entity_type | VARCHAR(50) |  | ✔ |  |
| entity_id | INTEGER |  | ✔ |  |
| event_metadata | TEXT |  | ✔ |  |
| created_at | TIMESTAMP |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| actor_id → users.id |


### Table `users`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| email | VARCHAR(255) |  |  |  |
| hashed_password | VARCHAR(255) |  |  |  |
| full_name | VARCHAR(150) |  |  |  |
| organization | VARCHAR(200) |  | ✔ |  |
| is_active | BOOLEAN |  | ✔ |  |
| role_id | INTEGER |  |  |  |
| created_at | DATETIME |  | ✔ |  |
| username | VARCHAR(50) |  | ✔ |  |
| approval_status | VARCHAR(20) |  | ✔ |  |
| approved_by_id | INTEGER |  | ✔ |  |
| approved_at | DATETIME |  | ✔ |  |
| role_assigned_by_id | INTEGER |  | ✔ |  |
| role_assigned_at | DATETIME |  | ✔ |  |
| is_suspended | BOOLEAN |  | ✔ |  |
| last_active_at | DATETIME |  | ✔ |  |
| is_email_verified | BOOLEAN |  | ✔ |  |
| email_verified_at | TIMESTAMP |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| role_id → roles.id |
| approved_by_id → users.id |
| role_assigned_by_id → users.id |


### Table `roles`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| name | VARCHAR(50) |  |  |  |
| description | VARCHAR(255) |  | ✔ |  |


### Table `conservation_alerts`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| title | VARCHAR(200) |  |  |  |
| severity | VARCHAR(20) |  | ✔ |  |
| alert_type | VARCHAR(50) |  |  |  |
| message | TEXT |  |  |  |
| species_id | INTEGER |  | ✔ |  |
| location_id | INTEGER |  | ✔ |  |
| is_resolved | BOOLEAN |  | ✔ |  |
| created_at | DATETIME |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| species_id → species.id |
| location_id → locations.id |


### Table `species`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| scientific_name | VARCHAR(150) |  |  |  |
| common_name | VARCHAR(150) |  |  |  |
| kingdom | VARCHAR(50) |  | ✔ |  |
| phylum | VARCHAR(50) |  | ✔ |  |
| class_name | VARCHAR(50) |  | ✔ |  |
| order_name | VARCHAR(50) |  | ✔ |  |
| family | VARCHAR(50) |  | ✔ |  |
| genus | VARCHAR(50) |  | ✔ |  |
| iucn_category | VARCHAR(10) |  |  |  |
| description | TEXT |  | ✔ |  |
| image_url | VARCHAR(500) |  | ✔ |  |
| created_at | DATETIME |  | ✔ |  |


### Table `locations`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| name | VARCHAR(200) |  |  |  |
| state | VARCHAR(100) |  |  |  |
| district | VARCHAR(100) |  | ✔ |  |
| protected_area_type | VARCHAR(100) |  | ✔ |  |
| latitude | FLOAT |  |  |  |
| longitude | FLOAT |  |  |  |
| area_sq_km | FLOAT |  | ✔ |  |
| geometry_geojson | TEXT |  | ✔ |  |
| created_at | DATETIME |  | ✔ |  |


### Table `data_sources`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| name | VARCHAR(100) |  |  |  |
| url | VARCHAR(255) |  | ✔ |  |
| description | VARCHAR(500) |  | ✔ |  |


### Table `document_species`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| document_id | INTEGER | ✔ |  |  |
| species_id | INTEGER | ✔ |  |  |
| mention_count | INTEGER |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| document_id → documents.id |
| species_id → species.id |


### Table `documents`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| title | VARCHAR(300) |  |  |  |
| source_type | VARCHAR(100) |  |  |  |
| author | VARCHAR(200) |  | ✔ |  |
| publication_date | DATETIME |  | ✔ |  |
| url | VARCHAR(500) |  | ✔ |  |
| raw_text | TEXT |  |  |  |
| cleaned_text | TEXT |  | ✔ |  |
| summary | TEXT |  | ✔ |  |
| topics | JSON |  | ✔ |  |
| embedding_json | JSON |  | ✔ |  |
| author_user_id | INTEGER |  | ✔ |  |
| created_at | DATETIME |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| author_user_id → users.id |


### Table `document_threats`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| document_id | INTEGER | ✔ |  |  |
| threat_id | INTEGER | ✔ |  |  |
| confidence_score | FLOAT |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| document_id → documents.id |
| threat_id → threats.id |


### Table `threats`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| category_name | VARCHAR(150) |  |  |  |
| iucn_threat_code | VARCHAR(50) |  | ✔ |  |
| severity_weight | FLOAT |  | ✔ |  |
| description | TEXT |  | ✔ |  |


### Table `email_verification_tokens`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ | ✔ |  |
| email | VARCHAR(255) |  |  |  |
| otp_hash | VARCHAR(255) |  |  |  |
| token_hash | VARCHAR(255) |  |  |  |
| pending_data | TEXT |  |  |  |
| attempts | INTEGER |  | ✔ |  |
| resend_count | INTEGER |  | ✔ |  |
| expires_at | TIMESTAMP |  |  |  |
| last_sent_at | TIMESTAMP |  |  |  |
| consumed_at | TIMESTAMP |  | ✔ |  |
| created_at | TIMESTAMP |  | ✔ |  |


### Table `ml_anomalies`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| species_id | INTEGER |  |  |  |
| location_id | INTEGER |  | ✔ |  |
| anomaly_type | VARCHAR(50) |  |  |  |
| anomaly_score | FLOAT |  |  |  |
| is_anomaly | BOOLEAN |  | ✔ |  |
| explanation | TEXT |  | ✔ |  |
| detected_at | DATETIME |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| species_id → species.id |
| location_id → locations.id |


### Table `ml_risk_scores`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| species_id | INTEGER |  |  |  |
| region_name | VARCHAR(150) |  |  |  |
| composite_score | FLOAT |  |  |  |
| risk_level | VARCHAR(20) |  |  |  |
| observation_frequency | FLOAT |  | ✔ |  |
| threat_density | FLOAT |  | ✔ |  |
| temporal_trend | FLOAT |  | ✔ |  |
| feature_snapshot | JSON |  | ✔ |  |
| calculated_at | DATETIME |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| species_id → species.id |


### Table `nlp_analysis_results`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| document_id | INTEGER |  |  |  |
| extracted_entities | JSON |  | ✔ |  |
| topics | JSON |  | ✔ |  |
| raw_meta | JSON |  | ✔ |  |
| created_at | DATETIME |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| document_id → documents.id |


### Table `observations`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| species_id | INTEGER |  |  |  |
| location_id | INTEGER |  | ✔ |  |
| submitted_by_user_id | INTEGER |  | ✔ |  |
| source_id | INTEGER |  |  |  |
| observed_at | DATETIME |  |  |  |
| latitude | FLOAT |  |  |  |
| longitude | FLOAT |  |  |  |
| accuracy_meters | FLOAT |  | ✔ |  |
| verification_status | VARCHAR(50) |  | ✔ |  |
| notes | TEXT |  | ✔ |  |
| raw_metadata | JSON |  | ✔ |  |
| created_at | DATETIME |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| submitted_by_user_id → users.id |
| species_id → species.id |
| source_id → data_sources.id |
| location_id → locations.id |


### Table `user_alerts`
| Column | Type | PK | Nullable | Default |
|--------|------|----|----------|---------|
| id | INTEGER | ✔ |  |  |
| alert_id | INTEGER |  |  |  |
| user_id | INTEGER |  |  |  |
| is_read | BOOLEAN |  | ✔ |  |
| read_at | DATETIME |  | ✔ |  |

**Foreign Keys**
| Column → Target Table.Column |
|------------------------------|
| alert_id → conservation_alerts.id |
| user_id → users.id |


## Model‑Defined Schema (SQLAlchemy)

### Table `conservation_alerts` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| title | VARCHAR(200) |  |  |
| severity | VARCHAR(20) |  | ✔ |
| alert_type | VARCHAR(50) |  |  |
| message | TEXT |  |  |
| species_id | INTEGER |  | ✔ |
| location_id | INTEGER |  | ✔ |
| is_resolved | BOOLEAN |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `user_alerts` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| alert_id | INTEGER |  |  |
| user_id | INTEGER |  |  |
| is_read | BOOLEAN |  | ✔ |
| read_at | DATETIME |  | ✔ |


### Table `documents` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| title | VARCHAR(300) |  |  |
| source_type | VARCHAR(100) |  |  |
| author | VARCHAR(200) |  | ✔ |
| publication_date | DATETIME |  | ✔ |
| url | VARCHAR(500) |  | ✔ |
| raw_text | TEXT |  |  |
| cleaned_text | TEXT |  | ✔ |
| summary | TEXT |  | ✔ |
| topics | JSON |  | ✔ |
| embedding_json | JSON |  | ✔ |
| author_user_id | INTEGER |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `document_species` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| document_id | INTEGER | ✔ |  |
| species_id | INTEGER | ✔ |  |
| mention_count | INTEGER |  | ✔ |


### Table `document_threats` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| document_id | INTEGER | ✔ |  |
| threat_id | INTEGER | ✔ |  |
| confidence_score | FLOAT |  | ✔ |


### Table `nlp_analysis_results` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| document_id | INTEGER |  |  |
| extracted_entities | JSON |  | ✔ |
| topics | JSON |  | ✔ |
| raw_meta | JSON |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `global_intelligence_records` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| source_id | INTEGER |  |  |
| source_record_id | VARCHAR(250) |  | ✔ |
| canonical_url | VARCHAR(500) |  | ✔ |
| title | VARCHAR(400) |  |  |
| summary | TEXT |  | ✔ |
| content_text | TEXT |  |  |
| content_hash | VARCHAR(64) |  | ✔ |
| layer | VARCHAR(50) |  |  |
| geography | VARCHAR(100) |  | ✔ |
| species_name | VARCHAR(200) |  | ✔ |
| threat_category | VARCHAR(200) |  | ✔ |
| topics | JSON |  | ✔ |
| publication_date | DATETIME |  | ✔ |
| event_date | DATETIME |  | ✔ |
| ingested_at | DATETIME |  | ✔ |
| is_indexed | BOOLEAN |  | ✔ |
| document_id | INTEGER |  | ✔ |
| corroboration_count | INTEGER |  | ✔ |
| provenance_meta | JSON |  | ✔ |


### Table `global_source_registry` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| source_key | VARCHAR(100) |  |  |
| source_name | VARCHAR(200) |  |  |
| source_type | VARCHAR(100) |  |  |
| geography | VARCHAR(100) |  | ✔ |
| topics | JSON |  | ✔ |
| access_method | VARCHAR(50) |  | ✔ |
| endpoint_url | VARCHAR(500) |  | ✔ |
| refresh_frequency_hours | INTEGER |  | ✔ |
| license_type | VARCHAR(100) |  | ✔ |
| is_active | BOOLEAN |  | ✔ |
| reliability_score | FLOAT |  | ✔ |
| requires_credentials | BOOLEAN |  | ✔ |
| has_credentials_configured | BOOLEAN |  | ✔ |
| last_refresh_attempt | DATETIME |  | ✔ |
| last_successful_refresh | DATETIME |  | ✔ |
| last_status | VARCHAR(50) |  | ✔ |
| last_http_status | INTEGER |  | ✔ |
| last_error_message | TEXT |  | ✔ |
| total_records_ingested | INTEGER |  | ✔ |
| records_newly_stored | INTEGER |  | ✔ |
| failed_requests_count | INTEGER |  | ✔ |
| latest_publication_date | DATETIME |  | ✔ |
| next_refresh_scheduled | DATETIME |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `locations` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| name | VARCHAR(200) |  |  |
| state | VARCHAR(100) |  |  |
| district | VARCHAR(100) |  | ✔ |
| protected_area_type | VARCHAR(100) |  | ✔ |
| latitude | FLOAT |  |  |
| longitude | FLOAT |  |  |
| area_sq_km | FLOAT |  | ✔ |
| geometry_geojson | TEXT |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `ml_anomalies` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| species_id | INTEGER |  |  |
| location_id | INTEGER |  | ✔ |
| anomaly_type | VARCHAR(50) |  |  |
| anomaly_score | FLOAT |  |  |
| is_anomaly | BOOLEAN |  | ✔ |
| explanation | TEXT |  | ✔ |
| detected_at | DATETIME |  | ✔ |
| status | VARCHAR(50) |  | ✔ |
| acknowledged | BOOLEAN |  | ✔ |
| acknowledged_by_id | INTEGER |  | ✔ |
| acknowledged_at | DATETIME |  | ✔ |
| investigation_notes | TEXT |  | ✔ |


### Table `ml_risk_scores` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| species_id | INTEGER |  |  |
| region_name | VARCHAR(150) |  |  |
| composite_score | FLOAT |  |  |
| risk_level | VARCHAR(20) |  |  |
| observation_frequency | FLOAT |  | ✔ |
| threat_density | FLOAT |  | ✔ |
| temporal_trend | FLOAT |  | ✔ |
| feature_snapshot | JSON |  | ✔ |
| calculated_at | DATETIME |  | ✔ |


### Table `data_sources` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| name | VARCHAR(100) |  |  |
| url | VARCHAR(255) |  | ✔ |
| description | VARCHAR(500) |  | ✔ |


### Table `observations` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| species_id | INTEGER |  |  |
| location_id | INTEGER |  | ✔ |
| submitted_by_user_id | INTEGER |  | ✔ |
| source_id | INTEGER |  |  |
| observed_at | DATETIME |  |  |
| latitude | FLOAT |  |  |
| longitude | FLOAT |  |  |
| accuracy_meters | FLOAT |  | ✔ |
| verification_status | VARCHAR(50) |  | ✔ |
| notes | TEXT |  | ✔ |
| raw_metadata | JSON |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `species` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| scientific_name | VARCHAR(150) |  |  |
| common_name | VARCHAR(150) |  |  |
| kingdom | VARCHAR(50) |  | ✔ |
| phylum | VARCHAR(50) |  | ✔ |
| class_name | VARCHAR(50) |  | ✔ |
| order_name | VARCHAR(50) |  | ✔ |
| family | VARCHAR(50) |  | ✔ |
| genus | VARCHAR(50) |  | ✔ |
| iucn_category | VARCHAR(10) |  |  |
| iucn_sis_id | INTEGER |  | ✔ |
| iucn_authority | VARCHAR(200) |  | ✔ |
| iucn_retrieved_at | DATETIME |  | ✔ |
| description | TEXT |  | ✔ |
| image_url | VARCHAR(500) |  | ✔ |
| image_source | VARCHAR(50) |  | ✔ |
| image_license | VARCHAR(100) |  | ✔ |
| image_attribution | VARCHAR(500) |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `audit_events` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| actor_id | INTEGER |  | ✔ |
| action | VARCHAR(100) |  |  |
| entity_type | VARCHAR(50) |  | ✔ |
| entity_id | INTEGER |  | ✔ |
| event_metadata | JSON |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `badge_definitions` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| code | VARCHAR(50) |  |  |
| name | VARCHAR(100) |  |  |
| description | TEXT |  | ✔ |
| icon_emoji | VARCHAR(10) |  | ✔ |
| rule_type | VARCHAR(50) |  |  |
| rule_threshold | INTEGER |  |  |


### Table `notifications` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| user_id | INTEGER |  |  |
| notification_type | VARCHAR(50) |  |  |
| title | VARCHAR(200) |  |  |
| message | TEXT |  |  |
| is_read | BOOLEAN |  | ✔ |
| submission_id | INTEGER |  | ✔ |
| points_amount | INTEGER |  | ✔ |
| badge_code | VARCHAR(50) |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `observation_submissions` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| researcher_id | INTEGER |  |  |
| species_id | INTEGER |  |  |
| location_id | INTEGER |  | ✔ |
| observed_at | DATETIME |  |  |
| latitude | FLOAT |  |  |
| longitude | FLOAT |  |  |
| accuracy_meters | FLOAT |  | ✔ |
| description | TEXT |  |  |
| habitat_notes | TEXT |  | ✔ |
| behavior_notes | TEXT |  | ✔ |
| identification_notes | TEXT |  | ✔ |
| citations | JSON |  | ✔ |
| status | VARCHAR(30) |  |  |
| promoted_observation_id | INTEGER |  | ✔ |
| created_at | DATETIME |  | ✔ |
| updated_at | DATETIME |  | ✔ |


### Table `points_ledger` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| user_id | INTEGER |  |  |
| submission_id | INTEGER |  | ✔ |
| amount | INTEGER |  |  |
| reason | VARCHAR(200) |  |  |
| idempotency_key | VARCHAR(200) |  |  |
| awarded_at | DATETIME |  | ✔ |


### Table `submission_images` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| submission_id | INTEGER |  |  |
| file_path | VARCHAR(500) |  |  |
| original_filename | VARCHAR(255) |  | ✔ |
| mime_type | VARCHAR(100) |  | ✔ |
| file_size_bytes | INTEGER |  | ✔ |
| uploaded_at | DATETIME |  | ✔ |


### Table `user_badges` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| user_id | INTEGER |  |  |
| badge_id | INTEGER |  |  |
| awarded_at | DATETIME |  | ✔ |
| triggered_by_submission_id | INTEGER |  | ✔ |


### Table `verification_decisions` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| submission_id | INTEGER |  |  |
| officer_id | INTEGER |  |  |
| action | VARCHAR(30) |  |  |
| note | TEXT |  | ✔ |
| decided_at | DATETIME |  | ✔ |


### Table `threats` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| category_name | VARCHAR(150) |  |  |
| iucn_threat_code | VARCHAR(50) |  | ✔ |
| severity_weight | FLOAT |  | ✔ |
| description | TEXT |  | ✔ |


### Table `email_verification_tokens` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| email | VARCHAR(255) |  |  |
| otp_hash | VARCHAR(255) |  |  |
| token_hash | VARCHAR(255) |  |  |
| pending_data | TEXT |  |  |
| attempts | INTEGER |  |  |
| resend_count | INTEGER |  |  |
| expires_at | DATETIME |  |  |
| last_sent_at | DATETIME |  |  |
| consumed_at | DATETIME |  | ✔ |
| created_at | DATETIME |  | ✔ |


### Table `roles` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| name | VARCHAR(50) |  |  |
| description | VARCHAR(255) |  | ✔ |


### Table `users` (from model)
| Column | Type | PK | Nullable |
|--------|------|----|----------|
| id | INTEGER | ✔ |  |
| username | VARCHAR(50) |  | ✔ |
| email | VARCHAR(255) |  |  |
| hashed_password | VARCHAR(255) |  |  |
| full_name | VARCHAR(150) |  |  |
| organization | VARCHAR(200) |  | ✔ |
| is_active | BOOLEAN |  | ✔ |
| is_suspended | BOOLEAN |  | ✔ |
| role_id | INTEGER |  |  |
| approval_status | VARCHAR(20) |  |  |
| approved_by_id | INTEGER |  | ✔ |
| approved_at | DATETIME |  | ✔ |
| role_assigned_by_id | INTEGER |  | ✔ |
| role_assigned_at | DATETIME |  | ✔ |
| is_email_verified | BOOLEAN |  |  |
| email_verified_at | DATETIME |  | ✔ |
| created_at | DATETIME |  | ✔ |
| last_active_at | DATETIME |  | ✔ |


## Differences Detected

- Table 'global_intelligence_records' defined in models but missing in DB.
- Table 'global_source_registry' defined in models but missing in DB.
- Column 'status' in table 'ml_anomalies' defined in model but missing in DB.
- Column 'acknowledged' in table 'ml_anomalies' defined in model but missing in DB.
- Column 'acknowledged_by_id' in table 'ml_anomalies' defined in model but missing in DB.
- Column 'acknowledged_at' in table 'ml_anomalies' defined in model but missing in DB.
- Column 'investigation_notes' in table 'ml_anomalies' defined in model but missing in DB.
- Column 'iucn_sis_id' in table 'species' defined in model but missing in DB.
- Column 'iucn_authority' in table 'species' defined in model but missing in DB.
- Column 'iucn_retrieved_at' in table 'species' defined in model but missing in DB.
- Column 'image_source' in table 'species' defined in model but missing in DB.
- Column 'image_license' in table 'species' defined in model but missing in DB.
- Column 'image_attribution' in table 'species' defined in model but missing in DB.
- Column 'id' in table 'audit_events' nullable mismatch: model=False, db=True
- Column 'event_metadata' in table 'audit_events' type mismatch: model=JSON, db=TEXT
- Column 'created_at' in table 'audit_events' type mismatch: model=DATETIME, db=TIMESTAMP
- Table 'badge_definitions' defined in models but missing in DB.
- Table 'notifications' defined in models but missing in DB.
- Table 'observation_submissions' defined in models but missing in DB.
- Table 'points_ledger' defined in models but missing in DB.
- Table 'submission_images' defined in models but missing in DB.
- Table 'user_badges' defined in models but missing in DB.
- Table 'verification_decisions' defined in models but missing in DB.
- Column 'id' in table 'email_verification_tokens' nullable mismatch: model=False, db=True
- Column 'attempts' in table 'email_verification_tokens' nullable mismatch: model=False, db=True
- Column 'resend_count' in table 'email_verification_tokens' nullable mismatch: model=False, db=True
- Column 'expires_at' in table 'email_verification_tokens' type mismatch: model=DATETIME, db=TIMESTAMP
- Column 'last_sent_at' in table 'email_verification_tokens' type mismatch: model=DATETIME, db=TIMESTAMP
- Column 'consumed_at' in table 'email_verification_tokens' type mismatch: model=DATETIME, db=TIMESTAMP
- Column 'created_at' in table 'email_verification_tokens' type mismatch: model=DATETIME, db=TIMESTAMP
- Column 'approval_status' in table 'users' nullable mismatch: model=False, db=True
- Column 'is_email_verified' in table 'users' nullable mismatch: model=False, db=True
- Column 'email_verified_at' in table 'users' type mismatch: model=DATETIME, db=TIMESTAMP

