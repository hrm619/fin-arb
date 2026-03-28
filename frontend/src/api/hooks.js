import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';

// Slates
export const useSlates = () => useQuery({ queryKey: ['slates'], queryFn: api.listSlates });
export const useSlate = (id) => useQuery({ queryKey: ['slate', id], queryFn: () => api.getSlate(id), enabled: !!id });
export const useCreateSlate = () => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: api.createSlate, onSuccess: () => qc.invalidateQueries({ queryKey: ['slates'] }) });
};
export const useDeleteSlate = () => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: api.deleteSlate, onSuccess: () => qc.invalidateQueries({ queryKey: ['slates'] }) });
};

// Events
export const useEvents = (slateId) => useQuery({ queryKey: ['events', slateId], queryFn: () => api.listEvents(slateId), enabled: !!slateId });
export const useCreateEvent = (slateId) => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (data) => api.createEvent(slateId, data), onSuccess: () => qc.invalidateQueries({ queryKey: ['events', slateId] }) });
};
export const useDeleteEvent = (slateId) => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: api.deleteEvent, onSuccess: () => qc.invalidateQueries({ queryKey: ['events', slateId] }) });
};
export const useEventResearch = (id) => useQuery({ queryKey: ['research', id], queryFn: () => api.getEventResearch(id), enabled: !!id });

// Estimates
export const useEstimate = (eventId) => useQuery({ queryKey: ['estimate', eventId], queryFn: () => api.getEstimate(eventId), enabled: !!eventId, retry: false });
export const useSubmitEstimate = (eventId) => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (data) => api.submitEstimate(eventId, data), onSuccess: () => qc.invalidateQueries({ queryKey: ['estimate', eventId] }) });
};

// Lines
export const useLines = (eventId) => useQuery({ queryKey: ['lines', eventId], queryFn: () => api.getLines(eventId), enabled: !!eventId });
export const useFetchLines = (eventId) => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: () => api.fetchLines(eventId), onSuccess: () => qc.invalidateQueries({ queryKey: ['lines', eventId] }) });
};
export const useArbForEvent = (eventId) => useQuery({ queryKey: ['arb', eventId], queryFn: () => api.getArbForEvent(eventId), enabled: !!eventId });

// Transcripts
export const useTranscripts = (eventId) => useQuery({ queryKey: ['transcripts', eventId], queryFn: () => api.listTranscripts(eventId), enabled: !!eventId });
export const useIngestUrl = (eventId) => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (url) => api.ingestUrl(eventId, url), onSuccess: () => qc.invalidateQueries({ queryKey: ['transcripts', eventId] }) });
};
export const useIngestText = (eventId) => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (data) => api.ingestText(eventId, data), onSuccess: () => qc.invalidateQueries({ queryKey: ['transcripts', eventId] }) });
};

// Signals
export const useSignals = (eventId) => useQuery({ queryKey: ['signals', eventId], queryFn: () => api.listSignals(eventId), enabled: !!eventId });
export const useExtractSignals = (eventId) => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: api.extractSignals, onSuccess: () => qc.invalidateQueries({ queryKey: ['signals', eventId] }) });
};
export const useFlagSignal = (eventId) => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, flag }) => api.flagSignal(id, flag), onSuccess: () => qc.invalidateQueries({ queryKey: ['signals', eventId] }) });
};

// Edge
export const useEdgeRanking = (slateId) => useQuery({ queryKey: ['edge', slateId], queryFn: () => api.getEdgeRanking(slateId), enabled: !!slateId });
export const useShortlist = (slateId) => useQuery({ queryKey: ['shortlist', slateId], queryFn: () => api.getShortlist(slateId), enabled: !!slateId });
export const useSlateArb = (slateId) => useQuery({ queryKey: ['slateArb', slateId], queryFn: () => api.getSlateArb(slateId), enabled: !!slateId });

// Tracking
export const useGradeEvent = () => {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ eventId, data }) => api.gradeEvent(eventId, data), onSuccess: () => qc.invalidateQueries({ queryKey: ['tracking'] }) });
};
export const useTrackingSummary = () => useQuery({ queryKey: ['tracking', 'summary'], queryFn: api.getTrackingSummary });
export const useBreakdown = (dimension) => useQuery({ queryKey: ['tracking', 'breakdown', dimension], queryFn: () => api.getBreakdown(dimension), enabled: !!dimension });
