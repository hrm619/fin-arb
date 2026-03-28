import { useShortlist } from '../../api/hooks';

export default function ShortlistPanel({ slateId }) {
  const { data: shortlist, isLoading } = useShortlist(slateId);

  if (isLoading || !shortlist) return null;
  if (shortlist.length === 0) return <p style={{ color: '#888' }}>No shortlisted events yet.</p>;

  return (
    <div style={{ border: '1px solid #333', borderRadius: '4px', padding: '1rem', marginBottom: '1rem' }}>
      <h3 style={{ marginTop: 0 }}>Shortlist</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left' }}>Matchup</th>
            <th>Edge</th>
            <th>Score</th>
            <th>Kelly $</th>
          </tr>
        </thead>
        <tbody>
          {shortlist.map(r => (
            <tr key={r.event_id}>
              <td>{r.home_team} vs {r.away_team}</td>
              <td style={{ textAlign: 'center' }}>{(r.raw_edge * 100).toFixed(1)}%</td>
              <td style={{ textAlign: 'center' }}>{(r.weighted_score * 100).toFixed(1)}</td>
              <td style={{ textAlign: 'center' }}>${r.kelly_stake.toFixed(0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
