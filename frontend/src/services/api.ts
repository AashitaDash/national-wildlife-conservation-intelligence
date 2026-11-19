import axios from 'axios';
import {
  AuthResponse,
  User,
  Species,
  SearchResponse,
  NLPAnalysisResult,
  RiskScoreResult,
  AnomalyResult,
  ConservationIntelligenceOverview,
  Observation,
  Alert,
} from '../types';

const rawBase = (import.meta as any).env?.VITE_API_BASE_URL;
const API_BASE = (() => {
  if (rawBase && rawBase.trim().length > 0) {
    let base = rawBase.trim();
    if (base.startsWith('/')) {
      return base.replace(/\/+$/, '');
    }
    base = base.replace(/^https?:\/\//, '');
    if (!base.includes('.') && !base.includes('localhost') && !base.includes('127.0.0.1') && base.length > 0) {
      base = `${base}.onrender.com`;
    }
    const protocol = base.includes('localhost') || base.includes('127.0.0.1') ? 'http' : 'https';
    base = `${protocol}://${base}`;
    base = base.replace(/\/+$/, '');
    if (!base.endsWith('/api/v1')) {
      base = `${base}/api/v1`;
    }
    return base;
  }
  // If in development mode or running on localhost/127.0.0.1, use relative /api/v1 proxy or local backend
  if ((import.meta as any).env?.DEV || (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))) {
    return '/api/v1';
  }
  return 'https://nwcip-backend.onrender.com/api/v1';
})();

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 45000, // 45 seconds timeout for cold starts and heavy analytical loads
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject JWT token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth Services
export const authService = {
  checkUsername: async (username: string): Promise<{
    username: string;
    available: boolean;
    valid: boolean;
    message: string;
    suggestions: string[];
  }> => {
    const response = await api.get('/auth/check-username', {
      params: { username }
    });
    return response.data;
  },

  login: async (username: string, password: string): Promise<AuthResponse> => {
    // Backend uses OAuth2PasswordRequestForm (supports email or username)
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const response = await api.post<any>('/auth/token', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return {
      access_token: response.data.access_token,
      token_type: response.data.token_type,
      user: {
        id: response.data.user_id,
        username: response.data.username || username,
        email: response.data.email || username,
        full_name: response.data.full_name,
        approval_status: response.data.approval_status || 'APPROVED',
        is_active: true,
        roles: [{ id: 1, name: response.data.role }]
      }
    };
  },

  register: async (userData: {
    username: string;
    email: string;
    password: string;
    full_name: string;
  }): Promise<AuthResponse> => {
    // Backend expects UserCreate schema and returns UserResponse
    const response = await api.post<any>('/auth/register', {
      username: userData.username,
      email: userData.email,
      password: userData.password,
      full_name: userData.full_name,
    });
    // Return empty auth response to let the UI know it succeeded, then it can redirect to login
    return {
      access_token: '',
      token_type: '',
      user: response.data
    };
  },

  // V32 Multi-Step Verification & Role Selection
  initiateRegistration: async (userData: {
    username: string;
    email: string;
    password: string;
    full_name: string;
  }): Promise<{
    email: string;
    message: string;
    cooldown_seconds: number;
    expires_in_minutes: number;
    verification_token?: string;
    otp_code?: string;
  }> => {
    const response = await api.post('/auth/register/initiate', {
      username: userData.username,
      email: userData.email,
      password: userData.password,
      full_name: userData.full_name,
    });
    return response.data;
  },

  verifyEmail: async (data: {
    email: string;
    otp_code?: string;
    verification_token?: string;
  }): Promise<{
    email: string;
    verified: boolean;
    verified_token: string;
    message: string;
    available_roles: Array<{
      id: string;
      title: string;
      target_role: string;
      description: string;
    }>;
  }> => {
    const response = await api.post('/auth/register/verify-email', data);
    return response.data;
  },

  resendVerification: async (email: string): Promise<{
    email: string;
    message: string;
    cooldown_seconds: number;
    otp_code?: string;
    verification_token?: string;
  }> => {
    const response = await api.post('/auth/register/resend', { email });
    return response.data;
  },

  completeRegistration: async (data: {
    email: string;
    verified_token: string;
    selected_account_type: string;
  }): Promise<AuthResponse> => {
    const response = await api.post<any>('/auth/register/complete', data);
    return {
      access_token: response.data.access_token,
      token_type: response.data.token_type,
      user: {
        id: response.data.user_id,
        username: response.data.username || data.email,
        email: data.email,
        full_name: response.data.full_name,
        approval_status: response.data.approval_status || 'APPROVED',
        is_active: true,
        roles: [{ id: 1, name: response.data.role }],
      },
    };
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<any>('/auth/me');
    const r = response.data.role;
    const roleObj = typeof r === 'object' && r !== null
      ? r
      : (typeof r === 'string' ? { id: response.data.role_id || 1, name: r } : null);
    return {
      id: response.data.id,
      username: response.data.username || response.data.email,
      email: response.data.email,
      full_name: response.data.full_name,
      approval_status: response.data.approval_status || 'APPROVED',
      is_active: response.data.is_active,
      roles: roleObj ? [roleObj] : []
    };
  },
};

// Search & Semantic Search Services
export const searchService = {
  search: async (
    query: string,
    filters?: { document_type?: string; source_id?: number },
    page: number = 1,
    page_size: number = 10
  ): Promise<SearchResponse> => {
    const response = await api.post<any>('/search', {
      query,
      limit: page_size,
    });

    const backendData = response.data;

    const documents = backendData.results
      .filter((r: any) => r.entity_type === 'DOCUMENT')
      .map((r: any) => ({
        id: r.id,
        title: r.title,
        document_type: r.metadata.source_type || 'Unknown',
        summary: r.snippet,
        similarity_score: r.relevance_score
      }));

    const species = backendData.results
      .filter((r: any) => r.entity_type === 'SPECIES')
      .map((r: any) => ({
        id: r.id,
        common_name: r.title,
        scientific_name: r.metadata.scientific_name || r.title,
        conservation_status: r.metadata.iucn_category,
        description: r.snippet
      }));

    const observations = backendData.results
      .filter((r: any) => r.entity_type === 'OBSERVATION')
      .map((r: any) => ({
        id: r.id,
        species_id: r.metadata.species_id || 0,
        species_name: r.title,
        latitude: r.metadata.latitude || 0,
        longitude: r.metadata.longitude || 0,
        observed_at: r.metadata.observed_at || '',
        verification_status: 'VERIFIED'
      }));

    return {
      query: backendData.query || query,
      total_results: backendData.total_results || 0,
      page,
      page_size,
      total_pages: Math.ceil((backendData.total_results || 0) / page_size) || 1,
      documents,
      matched_species: species,
      matched_locations: [],
      matched_threats: [],
      matched_topics: [],
      related_observations: observations,
      nlp_summary: "Results generated via FAISS dense vector search and BM25 lexical matching."
    };
  },
};

// NLP Intelligence Services
export const nlpService = {
  analyzeText: async (text: string, title?: string, signal?: AbortSignal): Promise<NLPAnalysisResult> => {
    const response = await api.post<any>('/documents', {
      raw_text: text,
      title: title || 'NLP Analysis',
      source_type: 'REPORT',
      author: 'Frontend User',
      publication_date: new Date().toISOString().split('T')[0],
      url: ''
    }, { signal, timeout: 30000 });

    const data = response.data;
    const nlp = data.nlp_results || {};
    const entities = nlp.extracted_entities || {};

    const threats = (data.threat_mentions || []).map((t: any) => ({
      threat_code: t.category_name,
      threat_name: t.category_name,
      confidence: t.confidence_score != null ? t.confidence_score : 0.6,
      severity_weight: 0.8,
      matched_keywords: [],
      evidence_status: t.evidence_status || 'REPORTED_SOURCE',
      supporting_passage: t.supporting_passage,
      section_type: t.section_type || 'BODY',
      score_type: t.score_type || 'CALIBRATED_PROBABILITY',
      explanation: t.explanation
    }));

    // Map calibrated topic breakdown instead of flat 1.0!
    const topicBreakdown = data.topic_breakdown || (data.nlp_results && data.nlp_results.topic_breakdown) || [];
    const topics = topicBreakdown.length > 0
      ? topicBreakdown.map((tb: any) => ({
          topic_code: tb.topic,
          topic_name: tb.topic,
          score: tb.confidence != null ? tb.confidence : 0.5,
          score_type: tb.score_type || 'CALIBRATED_PROBABILITY',
          raw_score: tb.raw_score,
          explanation: tb.explanation
        }))
      : (data.topics || []).map((t: string) => ({
          topic_code: t,
          topic_name: t,
          score: 1.0 / Math.max(1, (data.topics || []).length),
          score_type: 'ESTIMATED_SHARE'
        }));

    return {
      title: data.title,
      document_type: data.document_type || (data.nlp_results && data.nlp_results.document_type) || 'GENERAL_CONSERVATION_DOC',
      cleaned_text: data.cleaned_text || text,
      sentence_count: text.split(/[.!?]+/).length || 1,
      entities: {
        species: entities.species || [],
        locations: entities.locations || [],
        protected_areas: entities.protected_areas || [],
        organizations: entities.organizations || [],
        dates: entities.dates || entities.temporal_expressions || [],
        people: entities.people_and_authors || []
      },
      threats,
      topics,
      summary: data.summary || '',
      embedding: [],
      embedding_dimension: 0,
      model_metadata: nlp
    };
  },

  analyzePdf: async (file: File, title?: string, signal?: AbortSignal): Promise<NLPAnalysisResult> => {
    const formData = new FormData();
    formData.append('file', file);

    const params = title ? `?title=${encodeURIComponent(title)}` : '';
    const response = await api.post<any>(`/documents/upload-pdf${params}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      signal,
      timeout: 45000,
    });

    const data = response.data;
    const nlp = data.nlp_results || {};
    const entities = nlp.extracted_entities || {};

    const threats = (data.threat_mentions || []).map((t: any) => ({
      threat_code: t.category_name,
      threat_name: t.category_name,
      confidence: t.confidence_score != null ? t.confidence_score : 0.6,
      severity_weight: 0.8,
      matched_keywords: [],
      evidence_status: t.evidence_status || 'REPORTED_SOURCE',
      supporting_passage: t.supporting_passage,
      section_type: t.section_type || 'BODY',
      score_type: t.score_type || 'CALIBRATED_PROBABILITY',
      explanation: t.explanation
    }));

    const topicBreakdown = data.topic_breakdown || (data.nlp_results && data.nlp_results.topic_breakdown) || [];
    const topics = topicBreakdown.length > 0
      ? topicBreakdown.map((tb: any) => ({
          topic_code: tb.topic,
          topic_name: tb.topic,
          score: tb.confidence != null ? tb.confidence : 0.5,
          score_type: tb.score_type || 'CALIBRATED_PROBABILITY',
          raw_score: tb.raw_score,
          explanation: tb.explanation
        }))
      : (data.topics || []).map((t: string) => ({
          topic_code: t,
          topic_name: t,
          score: 1.0 / Math.max(1, (data.topics || []).length),
          score_type: 'ESTIMATED_SHARE'
        }));

    return {
      title: data.title,
      document_type: data.document_type || (data.nlp_results && data.nlp_results.document_type) || 'GENERAL_CONSERVATION_DOC',
      cleaned_text: data.cleaned_text || '',
      sentence_count: (data.cleaned_text || '').split(/[.!?]+/).length || 1,
      entities: {
        species: entities.species || [],
        locations: entities.locations || [],
        protected_areas: entities.protected_areas || [],
        organizations: entities.organizations || [],
        dates: entities.dates || entities.temporal_expressions || [],
        people: entities.people_and_authors || []
      },
      threats,
      topics,
      summary: data.summary || '',
      embedding: [],
      embedding_dimension: 0,
      model_metadata: nlp
    };
  },
};


// Machine Learning Intelligence Services
export const mlService = {
  getRiskScores: async (risk_level?: string, page: number = 1): Promise<{ items: RiskScoreResult[] }> => {
    const response = await api.get('/dashboards/species-risk-ranking');
    let items = response.data.map((r: any) => ({
      species_id: r.species_id,
      species_name: r.common_name,
      risk_score: r.composite_score,
      risk_level: r.risk_level
    }));

    if (risk_level) {
      items = items.filter((i: any) => i.risk_level === risk_level);
    }

    return { items };
  },

  getSpeciesRisk: async (speciesId: number): Promise<RiskScoreResult> => {
    const response = await api.post<any>('/ml/assess-risk', { species_id: speciesId });
    const data = response.data;
    return {
      species_id: data.species_id,
      species_name: data.species_common_name,
      risk_score: data.composite_score,
      risk_level: data.risk_level,
      class_probabilities: data.class_probabilities,
      features_used: data.feature_vector,
    };
  },

  getAnomalies: async (page: number = 1): Promise<{ items: AnomalyResult[] }> => {
    const response = await api.get('/ml/anomalies', { params: { skip: (page - 1) * 50, limit: 50 } });
    return { items: response.data };
  },

  acknowledgeAnomaly: async (id: number, notes?: string, status?: string): Promise<any> => {
    const payload = notes || status ? { notes, status: status || 'ACKNOWLEDGED' } : {};
    const response = await api.post(`/ml/anomalies/${id}/acknowledge`, payload);
    return response.data;
  },

  getIntelligenceOverview: async (): Promise<ConservationIntelligenceOverview> => {
    const [statsRes, riskRes, anomalyRes] = await Promise.all([
      api.get('/dashboards/stats'),
      api.get('/dashboards/species-risk-ranking'),
      api.get('/ml/anomalies')
    ]);

    return {
      total_species_monitored: statsRes.data.total_species || 0,
      total_observations_recorded: statsRes.data.total_observations || 0,
      total_documents_indexed: statsRes.data.total_documents || 0,
      active_threats_tracked: statsRes.data.total_threat_mentions || 0,
      species_risk_profiles: (riskRes.data || []).map((r: any) => ({
        species_id: r.species_id,
        scientific_name: r.scientific_name,
        common_name: r.common_name,
        risk_level: r.risk_level,
        risk_score: r.composite_score,
        primary_threat: 'Unknown'
      })).slice(0, 5),
      active_anomalies: anomalyRes.data || [],
      summary_directive: 'Monitor high risk species closely based on current model outputs.',
      disclaimer: 'Data generated via backend ML inference.'
    };
  },
};

// Species Services
export const speciesService = {
  getSpeciesList: async (page: number = 1, page_size: number = 24): Promise<{ items: Species[], total?: number, page?: number, total_pages?: number }> => {
    const skip = (page - 1) * page_size;
    const response = await api.get('/species', { params: { skip, limit: page_size } });
    if (Array.isArray(response.data)) {
        return { items: response.data, total: response.data.length, page: 1, total_pages: 1 };
    }
    const data = response.data;
    return {
        items: data.items || [],
        total: data.total || (data.items || []).length,
        page: data.page || 1,
        total_pages: data.total ? Math.ceil(data.total / page_size) : 1
    };
  },

  getSpeciesById: async (id: number): Promise<Species> => {
    const response = await api.get<Species>(`/species/${id}`);
    return response.data;
  },
};

// Observation Services
export const observationService = {
  getObservations: async (params?: { species_id?: number }): Promise<{ items: Observation[] }> => {
    const response = await api.get('/observations', { params });
    // Handle either direct array or { data: [] } structure
    const items = Array.isArray(response.data) ? response.data : response.data.data || [];
    return { items };
  },

  getMapObservations: async (params?: { species_id?: number, taxonomic_group?: string, state_name?: string, min_lat?: number, max_lat?: number, min_lon?: number, max_lon?: number }): Promise<{ items: Observation[], total_loaded: number, total_matching: number }> => {
    const response = await api.get('/observations/map', { params });
    const items = Array.isArray(response.data) ? response.data : response.data.data || [];
    const headerTotal = response.headers?.['x-total-count'];
    const totalMatching = headerTotal ? parseInt(headerTotal, 10) : items.length;
    return { items, total_loaded: items.length, total_matching: isNaN(totalMatching) ? items.length : totalMatching };
  },

  createObservation: async (obsData: Partial<Observation>): Promise<Observation> => {
    const response = await api.post<Observation>('/observations', obsData);
    return response.data;
  },
};

// Alert Services
export const alertService = {
  getAlerts: async (): Promise<{ items: Alert[] }> => {
    const response = await api.get('/dashboards/alerts');
    const readAlertIds = (() => {
      try {
        return new Set(JSON.parse(localStorage.getItem('nwcip_read_alert_ids') || '[]'));
      } catch {
        return new Set<number>();
      }
    })();
    const items = (Array.isArray(response.data) ? response.data : []).map((a: any) => ({
      id: a.id,
      title: a.title,
      alert_type: a.alert_type || a.severity || 'ECOLOGICAL_ANOMALY',
      severity: a.severity,
      message: a.description || a.message || '',
      is_read: a.is_resolved || readAlertIds.has(a.id),
      created_at: a.created_at
    }));
    return { items };
  },

  markAsRead: async (alertId: number): Promise<Alert> => {
    try {
      const readAlertIds: number[] = JSON.parse(localStorage.getItem('nwcip_read_alert_ids') || '[]');
      if (!readAlertIds.includes(alertId)) {
        readAlertIds.push(alertId);
        localStorage.setItem('nwcip_read_alert_ids', JSON.stringify(readAlertIds));
      }
    } catch {
      // ignore localstorage errors
    }
    const response = await api.post(`/dashboards/alerts/${alertId}/read`);
    return response.data;
  },
};


// ─────────────────────────────────────────────────────────────────────────────
// NLP Intelligence Services — Conservation Brief + Ask the Corpus
// ─────────────────────────────────────────────────────────────────────────────

export interface EvidenceItem {
  sentence: string;
  document_id: number;
  document_title: string;
  relevance: number;
}

export interface SourceDocumentSummary {
  id: number;
  title: string;
  source_type: string;
  author?: string;
  summary?: string;
  relevance_score?: number;
  snippet?: string;
}

export interface SynthesisResult {
  summary: string;
  species: Array<{ common_name: string; scientific_name: string; iucn_category: string; total_mentions: number }>;
  threats: Array<{ category_name: string; document_count: number }>;
  topics: Array<{ topic: string; document_count: number }>;
  documents_analyzed: number;
  evidence: EvidenceItem[];
  evidence_strength: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';
  conflicting_evidence: boolean;
  source_documents: SourceDocumentSummary[];
  missing_document_ids: number[];
  evidence_strength_rationale: string;
}

export interface QAResult {
  question: string;
  answer: string;
  evidence: EvidenceItem[];
  evidence_strength: 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';
  conflicting_evidence: boolean;
  source_documents: SourceDocumentSummary[];
  retrieved_species: string[];
  retrieved_threats: string[];
  evidence_strength_rationale: string;
}

export const nlpIntelligenceService = {
  /** Generate a Conservation Intelligence Brief from selected document IDs. */
  synthesize: async (documentIds: number[]): Promise<SynthesisResult> => {
    const response = await api.post<SynthesisResult>('/documents/synthesize', {
      document_ids: documentIds,
    });
    return response.data;
  },

  /** Ask a question across the indexed conservation corpus. */
  ask: async (question: string, topK: number = 5): Promise<QAResult> => {
    const response = await api.post<QAResult>('/documents/ask', {
      question,
      top_k: topK,
    });
    return response.data;
  },

  /** Fetch all indexed documents for document selection UI. */
  listDocuments: async (): Promise<SourceDocumentSummary[]> => {
    const response = await api.get<any[]>('/documents?limit=200');
    return (response.data || []).map((d: any) => ({
      id: d.id,
      title: d.title,
      source_type: d.source_type,
      author: d.author,
      summary: d.summary,
    }));
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// RAG Chatbot Assistant Service
// ─────────────────────────────────────────────────────────────────────────────
import {
  ChatRequest,
  ChatResponse,
  Submission,
  SubmissionCreate,
  ResearcherProfile,
  LeaderboardEntry,
  Badge,
  Notification,
  AdminUser,
  AdminPlatformStats,
  OfficerQueueStats,
  VerificationDecision,
} from '../types';

export const chatService = {
  ask: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat/ask', request);
    return response.data;
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Researcher Submission Service
// ─────────────────────────────────────────────────────────────────────────────
export const submissionService = {
  getMySubmissions: async (status?: string): Promise<Submission[]> => {
    const response = await api.get<Submission[]>('/submissions/mine', {
      params: status ? { status } : {},
    });
    return response.data;
  },

  getSubmission: async (id: number): Promise<Submission> => {
    const response = await api.get<Submission>(`/submissions/${id}`);
    return response.data;
  },

  createSubmission: async (data: SubmissionCreate): Promise<Submission> => {
    const response = await api.post<Submission>('/submissions', data);
    return response.data;
  },

  updateSubmission: async (id: number, data: Partial<SubmissionCreate>): Promise<Submission> => {
    const response = await api.put<Submission>(`/submissions/${id}`, data);
    return response.data;
  },

  submitForReview: async (id: number): Promise<Submission> => {
    const response = await api.post<Submission>(`/submissions/${id}/submit`);
    return response.data;
  },

  deleteDraft: async (id: number): Promise<void> => {
    await api.delete(`/submissions/${id}`);
  },

  uploadImage: async (submissionId: number, file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/submissions/${submissionId}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Forest Officer Verification Service
// ─────────────────────────────────────────────────────────────────────────────
export const officerService = {
  getQueue: async (params?: { status?: string; limit?: number; offset?: number }): Promise<Submission[]> => {
    const response = await api.get<Submission[]>('/officer/queue', { params });
    return response.data;
  },

  getQueueStats: async (): Promise<OfficerQueueStats> => {
    const response = await api.get<OfficerQueueStats>('/officer/queue/stats');
    return response.data;
  },

  claimSubmission: async (id: number): Promise<Submission> => {
    const response = await api.post<Submission>(`/officer/queue/${id}/claim`);
    return response.data;
  },

  verifySubmission: async (id: number, note?: string): Promise<VerificationDecision> => {
    const response = await api.post<VerificationDecision>(`/officer/queue/${id}/verify`, { note });
    return response.data;
  },

  rejectSubmission: async (id: number, reason: string): Promise<VerificationDecision> => {
    const response = await api.post<VerificationDecision>(`/officer/queue/${id}/reject`, { reason });
    return response.data;
  },

  requestMoreInfo: async (id: number, note: string): Promise<VerificationDecision> => {
    const response = await api.post<VerificationDecision>(`/officer/queue/${id}/request-info`, { note });
    return response.data;
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Gamification Service
// ─────────────────────────────────────────────────────────────────────────────
export const gamificationService = {
  getMyProfile: async (): Promise<ResearcherProfile> => {
    const response = await api.get<ResearcherProfile>('/gamification/profile/me');
    return response.data;
  },

  getLeaderboard: async (limit: number = 20): Promise<LeaderboardEntry[]> => {
    const response = await api.get<LeaderboardEntry[]>('/gamification/leaderboard', {
      params: { limit },
    });
    return response.data;
  },

  getBadges: async (): Promise<Badge[]> => {
    const response = await api.get<Badge[]>('/gamification/badges');
    return response.data;
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Admin Platform Service
// ─────────────────────────────────────────────────────────────────────────────
export const adminPlatformService = {
  getStats: async (): Promise<AdminPlatformStats> => {
    const response = await api.get<AdminPlatformStats>('/admin/platform/stats');
    return response.data;
  },

  getUsers: async (params?: { search?: string; role?: string; limit?: number }): Promise<AdminUser[]> => {
    const response = await api.get<AdminUser[]>('/admin/platform/users', { params });
    return response.data;
  },

  updateUserRole: async (userId: number, roleName: string): Promise<any> => {
    const response = await api.put(`/admin/platform/users/${userId}/role`, { role_name: roleName });
    return response.data;
  },

  toggleUserStatus: async (userId: number, isActive: boolean): Promise<any> => {
    const response = await api.put(`/admin/platform/users/${userId}/status`, { is_active: isActive });
    return response.data;
  },

  approveUser: async (userId: number, action: 'APPROVE' | 'REJECT', assignedRole?: string): Promise<any> => {
    const response = await api.put(`/admin/platform/users/${userId}/approve`, {
      action,
      assigned_role: assignedRole,
    });
    return response.data;
  },

  getAuditLog: async (limit: number = 50): Promise<any[]> => {
    const response = await api.get<any[]>('/admin/platform/audit-log', { params: { limit } });
    return response.data;
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Spatial State-Wise Biodiversity Service
// ─────────────────────────────────────────────────────────────────────────────
import { StateBiodiversityMapResponse, StateDetailResponse } from '../types';

export const spatialService = {
  getStateMetrics: async (params?: {
    species_id?: number;
    taxonomic_group?: string;
    verification_status?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<StateBiodiversityMapResponse> => {
    const response = await api.get<StateBiodiversityMapResponse>('/spatial/states', { params });
    return response.data;
  },

  getStateDetail: async (
    stateName: string,
    params?: {
      limit?: number;
      species_id?: number;
      taxonomic_group?: string;
      verification_status?: string;
    }
  ): Promise<StateDetailResponse> => {
    const response = await api.get<StateDetailResponse>(`/spatial/states/${encodeURIComponent(stateName)}`, {
      params,
    });
    return response.data;
  },
};

// ── Reports & Exports ────────────────────────────────────────────────────────

export interface ReportTypeMetadata {
  type_id: string;
  name: string;
  description: string;
  supported_formats: string[];
  available_filters: string[];
}

export interface ReportFilterOptions {
  species_id?: number;
  location_id?: number;
  taxonomic_class?: string;
  iucn_category?: string;
  threat_category?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
}

export interface ReportPreviewResponse {
  report_type: string;
  title: string;
  estimated_records: number;
  summary_metrics: Record<string, unknown>;
  sections: string[];
  scientific_limitations: string[];
  supported_formats: string[];
}

export const reportsService = {
  getTypes: async (): Promise<ReportTypeMetadata[]> => {
    const res = await api.get<ReportTypeMetadata[]>('/reports/types');
    return res.data;
  },

  getPreview: async (
    report_type: string,
    filters?: ReportFilterOptions
  ): Promise<ReportPreviewResponse> => {
    const res = await api.post<ReportPreviewResponse>('/reports/preview', {
      report_type,
      filters: filters ?? null,
    });
    return res.data;
  },

  generate: async (
    report_type: string,
    format: string,
    filters?: ReportFilterOptions
  ): Promise<{ blob: Blob; filename: string }> => {
    const res = await api.post(
      '/reports/generate',
      { report_type, format, filters: filters ?? null },
      { responseType: 'blob' }
    );
    const disposition: string = (res.headers['content-disposition'] as string) ?? '';
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match ? match[1] : `report.${format.toLowerCase()}`;
    return { blob: res.data as Blob, filename };
  },
};


