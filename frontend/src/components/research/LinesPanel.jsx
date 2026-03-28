import { useLines, useFetchLines } from '../../api/hooks';

export default function LinesPanel({ eventId }) {
  const { data: lines, isLoading } = useLines(eventId);
  const fetchLines = useFetchLines(eventId);

  return (
    <div style={{ border: '1px solid #333', borderRadius: '4px', padding: '1rem', marginBottom: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ marginTop: 0 }}>Market Lines</h3>
        <button onClick={() => fetchLines.mutate()} disabled={fetchLines.isPending}>
          {fetchLines.isPending ? 'Fetching...' : 'Fetch Lines'}
        </button>
      </div>
      {isLoading ? <p>Loading...</p> : lines?.length === 0 ? (
        <p style={{ color: '#888' }}>No lines yet. Click Fetch Lines.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr><th style={{ textAlign: 'left' }}>Source</th><th>Implied %</th><th>American</th><th>Decimal</th><th>Fetched</th></tr>
          </thead>
          <tbody>
            {lines?.map(l => (
              <tr key={l.id}>
                <td>{l.source}</td>
                <td style={{ textAlign: 'center' }}>{l.implied_prob_pct.toFixed(1)}%</td>
                <td style={{ textAlign: 'center' }}>{l.american_odds ? (l.american_odds > 0 ? '+' : '') + l.american_odds : '-'}</td>
                <td style={{ textAlign: 'center' }}>{l.decimal_odds?.toFixed(2) || '-'}</td>
                <td style={{ textAlign: 'center', fontSize: '0.8rem', color: '#aaa' }}>{new Date(l.fetched_at).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
