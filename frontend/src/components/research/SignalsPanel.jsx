import { useSignals, useFlagSignal } from '../../api/hooks';

const typeColors = {
  injury: '#ef4444', scheme: '#3b82f6', motivation: '#eab308',
  sentiment: '#a855f7', line_commentary: '#22c55e',
};

export default function SignalsPanel({ eventId }) {
  const { data: signals, isLoading } = useSignals(eventId);
  const flagSignal = useFlagSignal(eventId);

  if (isLoading) return <p>Loading signals...</p>;
  if (!signals?.length) return null;

  return (
    <div style={{ border: '1px solid #333', borderRadius: '4px', padding: '1rem', marginBottom: '1rem' }}>
      <h3 style={{ marginTop: 0 }}>Signals ({signals.length})</h3>
      {signals.map(s => (
        <div key={s.id} style={{
          padding: '0.5rem', marginBottom: '0.5rem', background: '#1a1a1a',
          borderRadius: '4px', borderLeft: `3px solid ${typeColors[s.signal_type] || '#888'}`,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ color: typeColors[s.signal_type] || '#888', fontWeight: 'bold', marginRight: '0.5rem' }}>
                {s.signal_type}
              </span>
              <span style={{ color: '#aaa', fontSize: '0.8rem' }}>
                relevance: {(s.relevance_score * 100).toFixed(0)}%
              </span>
            </div>
            <div style={{ display: 'flex', gap: '0.25rem' }}>
              <button
                onClick={() => flagSignal.mutate({ id: s.id, flag: 'used_in_pricing' })}
                style={{ fontSize: '0.7rem', background: s.user_flag === 'used_in_pricing' ? '#22c55e' : 'transparent', border: '1px solid #555', borderRadius: '3px', color: '#fff', cursor: 'pointer' }}
              >Use</button>
              <button
                onClick={() => flagSignal.mutate({ id: s.id, flag: 'dismissed' })}
                style={{ fontSize: '0.7rem', background: s.user_flag === 'dismissed' ? '#ef4444' : 'transparent', border: '1px solid #555', borderRadius: '3px', color: '#fff', cursor: 'pointer' }}
              >Dismiss</button>
            </div>
          </div>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.9rem' }}>{s.content}</p>
        </div>
      ))}
    </div>
  );
}
