import { useState } from 'react';
import { useTranscripts, useIngestUrl, useIngestText, useExtractSignals } from '../../api/hooks';

export default function TranscriptPanel({ eventId }) {
  const { data: transcripts, isLoading } = useTranscripts(eventId);
  const ingestUrl = useIngestUrl(eventId);
  const ingestText = useIngestText(eventId);
  const extractSignals = useExtractSignals(eventId);
  const [url, setUrl] = useState('');
  const [text, setText] = useState('');
  const [mode, setMode] = useState('url');
  const [expanded, setExpanded] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (mode === 'url') {
      ingestUrl.mutate(url, { onSuccess: () => setUrl('') });
    } else {
      ingestText.mutate({ raw_text: text }, { onSuccess: () => setText('') });
    }
  };

  return (
    <div style={{ border: '1px solid #333', borderRadius: '4px', padding: '1rem', marginBottom: '1rem' }}>
      <h3 style={{ marginTop: 0 }}>Transcripts</h3>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <button onClick={() => setMode('url')} style={{ fontWeight: mode === 'url' ? 'bold' : 'normal' }}>YouTube URL</button>
        <button onClick={() => setMode('text')} style={{ fontWeight: mode === 'text' ? 'bold' : 'normal' }}>Raw Text</button>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        {mode === 'url' ? (
          <input placeholder="https://youtube.com/watch?v=..." value={url} onChange={e => setUrl(e.target.value)} required style={{ flex: 1 }} />
        ) : (
          <textarea placeholder="Paste transcript text..." value={text} onChange={e => setText(e.target.value)} required style={{ flex: 1, minHeight: '60px' }} />
        )}
        <button type="submit" disabled={ingestUrl.isPending || ingestText.isPending}>
          {(ingestUrl.isPending || ingestText.isPending) ? 'Ingesting...' : 'Ingest'}
        </button>
      </form>

      {isLoading ? <p>Loading...</p> : transcripts?.length === 0 ? (
        <p style={{ color: '#888' }}>No transcripts yet.</p>
      ) : (
        <div>
          {transcripts?.map(t => (
            <div key={t.id} style={{ marginBottom: '0.5rem', padding: '0.5rem', background: '#1a1a1a', borderRadius: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{t.source_type} — {new Date(t.created_at).toLocaleString()}</span>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button onClick={() => extractSignals.mutate(t.id)} disabled={extractSignals.isPending} style={{ fontSize: '0.8rem' }}>
                    Extract Signals
                  </button>
                  <button onClick={() => setExpanded(expanded === t.id ? null : t.id)} style={{ fontSize: '0.8rem' }}>
                    {expanded === t.id ? 'Collapse' : 'Expand'}
                  </button>
                </div>
              </div>
              {expanded === t.id && (
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8rem', maxHeight: '300px', overflow: 'auto', marginTop: '0.5rem', color: '#ccc' }}>
                  {t.raw_text}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
