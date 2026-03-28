const BASE_URL = '/api/v1';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (res.status === 204) return null;
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  // Sports browsing
  listSports: () => request('/sports'),
  listSportEvents: (sportKey, params = {}) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v != null))
    ).toString();
    return request(`/sports/${sportKey}/events${qs ? '?' + qs : ''}`);
  },

  // Slates
  listSlates: () => request('/slates'),
  createSlate: (data) => request('/slates', { method: 'POST', body: JSON.stringify(data) }),
  getSlate: (id) => request(`/slates/${id}`),
  updateSlate: (id, data) => request(`/slates/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteSlate: (id) => request(`/slates/${id}`, { method: 'DELETE' }),

  // Events
  listEvents: (slateId) => request(`/slates/${slateId}/events`),
  createEvent: (slateId, data) => request(`/slates/${slateId}/events`, { method: 'POST', body: JSON.stringify(data) }),
  createEventsBatch: (slateId, events) => request(`/slates/${slateId}/events/batch`, { method: 'POST', body: JSON.stringify({ events }) }),
  getEvent: (id) => request(`/events/${id}`),
  updateEvent: (id, data) => request(`/events/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteEvent: (id) => request(`/events/${id}`, { method: 'DELETE' }),
  getEventResearch: (id) => request(`/events/${id}/research`),

  // Estimates
  submitEstimate: (eventId, data) => request(`/events/${eventId}/estimate`, { method: 'POST', body: JSON.stringify(data) }),
  getEstimate: (eventId) => request(`/events/${eventId}/estimate`),

  // Lines
  fetchLines: (eventId) => request(`/events/${eventId}/lines/fetch`, { method: 'POST' }),
  getLines: (eventId) => request(`/events/${eventId}/lines`),
  getArbForEvent: (eventId) => request(`/events/${eventId}/lines/arb`),

  // Transcripts
  ingestUrl: (eventId, url) => request(`/events/${eventId}/transcripts/url`, { method: 'POST', body: JSON.stringify({ source_url: url }) }),
  ingestText: (eventId, data) => request(`/events/${eventId}/transcripts`, { method: 'POST', body: JSON.stringify(data) }),
  listTranscripts: (eventId) => request(`/events/${eventId}/transcripts`),
  deleteTranscript: (id) => request(`/transcripts/${id}`, { method: 'DELETE' }),

  // Signals
  extractSignals: (transcriptId) => request(`/transcripts/${transcriptId}/extract`, { method: 'POST' }),
  listSignals: (eventId) => request(`/events/${eventId}/signals`),
  flagSignal: (id, flag) => request(`/signals/${id}/flag`, { method: 'PATCH', body: JSON.stringify({ user_flag: flag }) }),

  // Edge
  getEdgeRanking: (slateId) => request(`/slates/${slateId}/edge`),
  getShortlist: (slateId) => request(`/slates/${slateId}/shortlist`),
  getSlateArb: (slateId) => request(`/slates/${slateId}/arb`),

  // Tracking
  gradeEvent: (eventId, data) => request(`/events/${eventId}/outcome`, { method: 'POST', body: JSON.stringify(data) }),
  getTrackingSummary: () => request('/tracking/summary'),
  getBreakdown: (dimension) => request(`/tracking/breakdown/${dimension}`),
  exportCsv: () => fetch(`${BASE_URL}/tracking/export`).then(r => r.text()),
};
