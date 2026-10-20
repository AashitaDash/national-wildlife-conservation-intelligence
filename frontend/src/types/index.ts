export type RoleName = 'RESEARCHER' | 'FOREST_OFFICER' | 'NGO' | 'CITIZEN' | 'ADMIN' | 'VIEWER';

export interface Role {
  id: number;
  name: RoleName;
  description?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  roles: Role[];
  created_at?: string;
  last_active_at?: string;
}

// ── Submission workflow types ─────────────────────────────────────────────────

export type SubmissionStatus =
  | 'DRAFT'
  | 'PENDING_REVIEW'
  | 'UNDER_REVIEW'
  | 'MORE_INFO_NEEDED'
  | 'VERIFIED'
  | 'REJECTED';

export interface SubmissionImage {
  id: number;
  submission_id: number;
  file_path: string;
  original_filename?: string;
  mime_type?: string;
  file_size_bytes?: number;
  uploaded_at?: string;
}

export interface VerificationDecision {
  id: number;
  submission_id: number;
  officer_id: number;
  officer_name?: string;
  action: string;
  note?: string;
  decided_at?: string;
}

export interface Submission {
  id: number;
  researcher_id: number;
  researcher_name?: string;
  species_id: number;
  species_common_name?: string;
  species_scientific_name?: string;
  species_iucn_category?: string;
  location_id?: number;
  location_name?: string;
  observed_at: string;
  latitude: number;
  longitude: number;
  accuracy_meters?: number;
  description: string;
  habitat_notes?: string;
  behavior_notes?: string;
  identification_notes?: string;
  citations?: string[];
  status: SubmissionStatus;
  promoted_observation_id?: number;
  images: SubmissionImage[];
  latest_decision?: VerificationDecision;
  created_at?: string;
  updated_at?: string;
}

export interface SubmissionCreate {
  species_id: number;
  location_id?: number;
  observed_at: string;
  latitude: number;
  longitude: number;
  accuracy_meters?: number;
  description: string;
  habitat_notes?: string;
  behavior_notes?: string;
  identification_notes?: string;
  citations?: string[];
  status?: 'DRAFT' | 'PENDING_REVIEW';
}

// ── Gamification types ────────────────────────────────────────────────────────

export interface Badge {
  code: string;
  name: string;
  description?: string;
  icon_emoji?: string;
  awarded_at: string;
}

export interface ResearcherProfile {
  total_points: number;
  level: string;
  level_min_points: number;
  next_level_points?: number;
  progress_to_next_pct?: number;
  verified_count: number;
  distinct_species: number;
  badges: Badge[];
  submission_counts: Record<string, number>;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  display_name: string;
  verified_count: number;
  total_points: number;
  distinct_species: number;
  badge_count: number;
  level: string;
}

export interface Notification {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  submission_id?: number;
  points_amount?: number;
  badge_code?: string;
  created_at?: string;
}

// ── Admin types ───────────────────────────────────────────────────────────────

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  organization?: string;
  is_active: boolean;
  is_suspended: boolean;
  role_name: string;
  created_at?: string;
  last_active_at?: string;
  submission_count: number;
  verified_count: number;
}

export interface AdminPlatformStats {
  total_users: number;
  total_researchers: number;
  total_officers: number;
  total_admins: number;
  active_users_24h: number;
  total_submissions: number;
  pending_submissions: number;
  verified_submissions: number;
  rejected_submissions: number;
  total_species: number;
  total_observations: number;
  submissions_by_status: Record<string, number>;
  registrations_last_30d: Array<{ date: string; count: number }>;
}

export interface OfficerQueueStats {
  pending_review: number;
  under_review: number;
  more_info_needed: number;
  verified: number;
  rejected: number;
  total: number;
}

// ── State-wise spatial intelligence types ─────────────────────────────────────

export interface StateMetricSummary {
  state_name: string;
  distinct_species_count: number;
  total_observation_records: number;
  verified_records: number;
  unverified_records: number;
  taxonomic_breakdown: Record<string, number>;
  top_recorded_species: Array<{
    species_id: number;
    common_name: string;
    scientific_name: string;
    taxonomic_class?: string;
    iucn_category?: string;
    records_count: number;
  }>;
  active_threat_count: number;
  recorded_threats: string[];
  highest_risk_level: string;
  risk_score_summary?: {
    composite_score: number;
    risk_level: string;
    feature_snapshot?: Record<string, any>;
  };
  latest_observations: any[];
  data_provenance_sources: string[];
}

export interface StateBiodiversityMapResponse {
  total_states_represented: number;
  dataset_disclaimer: string;
  metric_type: string;
  states: Record<string, StateMetricSummary>;
}

export interface StateDetailObservation {
  id: number;
  species_id: number;
  species_common_name?: string;
  species_scientific_name?: string;
  taxonomic_class?: string;
  iucn_category?: string;
  latitude: number;
  longitude: number;
  is_fuzzy: boolean;
  observed_at: string;
  verification_status: string;
  source_name?: string;
  accuracy_meters?: number;
  notes?: string;
}

export interface StateDetailResponse {
  state_name: string;
  summary: StateMetricSummary;
  observations: StateDetailObservation[];
  total_observations_available: number;
}



export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Species {
  id: number;
  scientific_name: string;
  common_name: string;
  taxonomic_class?: string;
  /** IUCN Red List category as sent by the backend (e.g. 'EN'). */
  iucn_category?: string;
  /** Legacy alias — some UI code reads this; mapped from iucn_category. */
  conservation_status?: string;
  is_demo?: boolean;
  population_trend?: string;
  description?: string;
  image_url?: string;
  image_source?: string;
  image_license?: string;
  image_attribution?: string;
  created_at?: string;
  total_observations?: number;
}


export interface Location {
  id: number;
  name: string;
  location_type?: string;
  state?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
  is_protected_area?: boolean;
}

export interface Threat {
  id: number;
  code: string;
  name: string;
  description?: string;
  severity_weight?: number;
}

export interface Topic {
  id: number;
  code: string;
  name: string;
  description?: string;
}

export interface Observation {
  id: number;
  species_id: number;
  species_name?: string;
  species_image_url?: string;
  location_id?: number;
  location_name?: string;
  latitude: number;
  longitude: number;
  /** Real API field. */
  observed_at?: string;
  /** Legacy field name (not sent by the backend). */
  observation_date?: string;
  count?: number;
  metadata?: Record<string, any>;
  provenance?: string;
  observer_identifier?: string;
  is_demo?: boolean;
  verification_status: 'UNVERIFIED' | 'VERIFIED' | 'REJECTED' | string;
  notes?: string;
  observer_type?: string;
}

export interface DocumentResult {
  id: number;
  title: string;
  document_type: string;
  summary?: string;
  similarity_score?: number;
  publication_date?: string;
  provenance?: string;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  page: number;
  page_size: number;
  total_pages: number;
  documents: DocumentResult[];
  matched_species: Species[];
  matched_locations: Location[];
  matched_threats: Threat[];
  matched_topics: Topic[];
  related_observations: Observation[];
  nlp_summary?: string;
  risk_score?: number;
  risk_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  anomaly_info?: AnomalyResult;
}

/** Real NLP entities are objects such as {name, type} / {matched_name, scientific_name, type} / {value, type}. */
export type NLPEntity =
  | string
  | { name?: string; matched_name?: string; scientific_name?: string; value?: string; type?: string };

export interface NLPAnalysisResult {
  title?: string;
  cleaned_text: string;
  sentence_count: number;
  entities: {
    species: NLPEntity[];
    locations: NLPEntity[];
    protected_areas: NLPEntity[];
    organizations: NLPEntity[];
    dates: NLPEntity[];
  };
  threats: Array<{
    threat_code: string;
    threat_name: string;
    confidence: number;
    severity_weight: number;
    matched_keywords: string[];
  }>;
  topics: Array<{
    topic_code: string;
    topic_name: string;
    score: number;
  }>;
  summary: string;
  embedding?: number[];
  embedding_dimension?: number;
  model_metadata?: Record<string, any>;
}

export interface RiskScoreResult {
  species_id?: number;
  species_name?: string;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  /** Only sent by the per-species detail endpoint. */
  confidence?: number;
  class_probabilities?: Record<string, number>;
  features_used?: Record<string, number>;
  factor_breakdown?: Record<string, number>;
  disclaimer?: string;
  /** Sent by the list endpoint. */
  explanation?: Record<string, number>;
  model_name?: string;
  is_demo?: boolean;
}

export interface AnomalyResult {
  /** Not sent for stored anomaly records (the list endpoint only returns detected anomalies). */
  is_anomaly?: boolean;
  anomaly_score?: number; // Legacy or explicit score
  isolation_score?: number; // Updated field
  anomaly_type?: string;
  explanation: string;
  
  // Conservation Anomaly Intelligence fields
  species?: { id: number; common_name: string; scientific_name: string };
  location?: { id: number; name: string };
  period?: { days: number; label: string };
  observation_count?: number;
  related_threats?: Array<{ category_name: string; mention_count: number }>;
  related_documents?: Array<{ id: number; title: string }>;
  supporting_record_count?: number;
  investigation_guidance?: string;
  evidence_strength?: string;

  metrics?: Record<string, any>;
  disclaimer?: string;
  id?: number;
  species_id?: number;
  detected_at?: string;
  is_demo?: boolean;
}

export interface SpeciesRiskProfile {
  species_id: number;
  scientific_name: string;
  common_name: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  risk_score: number;
  primary_threat?: string;
}

export interface ConservationIntelligenceOverview {
  total_species_monitored: number;
  total_observations_recorded: number;
  total_documents_indexed?: number;
  active_threats_tracked?: number;
  species_risk_profiles: SpeciesRiskProfile[];
  active_anomalies: AnomalyResult[];
  summary_directive?: string;
  disclaimer?: string;
}

export interface Alert {
  id: number;
  title: string;
  alert_type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | 'LOW' | 'MEDIUM' | 'HIGH' | string;
  message: string;
  is_read: boolean;
  is_demo?: boolean;
  created_at: string;
}

export interface ChatSourceItem {
  id: string;
  source_type: 'DATABASE' | 'DOCUMENT' | 'EXTERNAL' | string;
  title: string;
  snippet: string;
  reference?: string;
  relevance_score: number;
  metadata?: Record<string, any>;
}

export interface ChatRetrievalMetadata {
  intent: string;
  db_species_retrieved?: number;
  db_observations_retrieved?: number;
  documents_retrieved?: number;
  external_records_retrieved?: number;
  llm_provider: string;
  llm_model: string;
  retrieval_time_ms: number;
  generation_time_ms: number;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: ChatSourceItem[];
  retrieval_metadata?: ChatRetrievalMetadata;
  created_at?: string;
}

export interface ChatRequest {
  question: string;
  conversation_id?: string;
  conversation_history?: ChatMessage[];
}

export interface ChatResponse {
  answer: string;
  sources: ChatSourceItem[];
  retrieval_metadata: ChatRetrievalMetadata;
  conversation_id?: string;
  model_used?: string;
}

