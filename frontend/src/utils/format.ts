import { NLPEntity, Observation } from '../types';

/** Human-readable label for an NLP entity (real API returns objects; older shape was a string). */
export const entityLabel = (e: NLPEntity): string => {
  if (typeof e === 'string') return e;
  return e.matched_name || e.name || e.value || e.scientific_name || '';
};

/** Observation date: real field is `observed_at`; `observation_date` is the legacy name. */
export const observationDate = (o: Observation): string | undefined => {
  const raw = o.observed_at || o.observation_date;
  return raw ? raw.slice(0, 10) : undefined;
};

/** Observation count is stored in `metadata.count` by the backend; undefined when not recorded. */
export const observationCount = (o: Observation): number | undefined => {
  if (typeof o.count === 'number') return o.count;
  const c = o.metadata?.count;
  return typeof c === 'number' ? c : undefined;
};

export const observationNote = (o: Observation): string | undefined => o.notes || o.provenance;

/** Extract a readable message from an axios-style error. */
export const errorMessage = (err: any, fallback: string): string => {
  const status = err?.response?.status;
  const detail = err?.response?.data?.detail;
  if (status) return `${fallback} (server responded ${status}${typeof detail === 'string' ? `: ${detail}` : ''}).`;
  return `${fallback} (no response from server — is the backend running?).`;
};
