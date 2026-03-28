import { useState } from 'react';
import { useSlates, useEdgeRanking, useSlateArb } from '../api/hooks';

export default function EdgeDashboard() {
  const { data: slates } = useSlates();
  const [slateId, setSlateId] = useState(null);
  const { data: ranked, isLoading } = useEdgeRanking(slateId);
  const { data: arbs } = useSlateArb(slateId);
  const [sortKey, setSortKey] = useState('weighted_score');

  const sorted = ranked ? [...ranked].sort((a, b) => {
    if (sortKey === 'event_date') return 0;
    return (b[sortKey] || 0) - (a[sortKey] || 0);
  }) : [];

  return (
    <div>
      <h1>Edge Dashboard</h1>

      <div style={{ marginBottom: '1rem' }}>
        <select value={slateId || ''} onChange={e => setSlateId(e.target.value ? Number(e.target.value) : null)}>
          <option value="">Select a slate</option>
          {slates?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </div>

      {isLoading && <p>Loading...</p>}

      {slateId && sorted.length > 0 && (
        <>
          <div style={{ marginBottom: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span>Sort by:</span>
            {['weighted_score', 'raw_edge', 'kelly_stake', 'confidence_weight'].map(k => (
              <button key={k} onClick={() => setSortKey(k)}
                style={{ fontWeight: sortKey === k ? 'bold' : 'normal', background: sortKey === k ? '#1e3a5f' : 'transparent', border: '1px solid #555', borderRadius: '3px', color: '#fff', cursor: 'pointer', padding: '0.25rem 0.5rem' }}
              >{k.replace('_', ' ')}</button>
            ))}
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '2rem' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Matchup</th>
                <th>Sport</th>
                <th>Your %</th>
                <th>Market %</th>
                <th>Source</th>
                <th>Edge</th>
                <th>Confidence</th>
                <th>Score</th>
                <th>Kelly %</th>
                <th>Kelly $</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(r => (
                <tr key={r.event_id}>
                  <td>{r.home_team} vs {r.away_team}</td>
                  <td style={{ textAlign: 'center' }}>{r.sport}</td>
                  <td style={{ textAlign: 'center' }}>{r.user_prob_pct.toFixed(1)}</td>
                  <td style={{ textAlign: 'center' }}>{r.best_market_prob_pct.toFixed(1)}</td>
                  <td style={{ textAlign: 'center' }}>{r.best_market_source}</td>
                  <td style={{ textAlign: 'center', color: r.raw_edge > 0.05 ? '#22c55e' : '#eab308' }}>
                    {(r.raw_edge * 100).toFixed(1)}%
                  </td>
                  <td style={{ textAlign: 'center' }}>{r.confidence_tier || '-'}</td>
                  <td style={{ textAlign: 'center' }}>{(r.weighted_score * 100).toFixed(1)}</td>
                  <td style={{ textAlign: 'center' }}>{(r.kelly_fraction * 100).toFixed(2)}%</td>
                  <td style={{ textAlign: 'center' }}>${r.kelly_stake.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {slateId && sorted.length === 0 && !isLoading && (
        <p style={{ color: '#888' }}>No events with meaningful edge. Submit estimates and fetch lines first.</p>
      )}

      {slateId && arbs?.length > 0 && (
        <div style={{ border: '1px solid #333', borderRadius: '4px', padding: '1rem' }}>
          <h2>Arbitrage Opportunities</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Source A</th>
                <th>Prob A</th>
                <th style={{ textAlign: 'left' }}>Source B</th>
                <th>Prob B</th>
                <th>Combined</th>
                <th>Arb Edge</th>
              </tr>
            </thead>
            <tbody>
              {arbs.map((a, i) => (
                <tr key={i}>
                  <td>{a.source_a}</td>
                  <td style={{ textAlign: 'center' }}>{a.implied_prob_a.toFixed(1)}%</td>
                  <td>{a.source_b}</td>
                  <td style={{ textAlign: 'center' }}>{a.implied_prob_b.toFixed(1)}%</td>
                  <td style={{ textAlign: 'center' }}>{a.combined_prob.toFixed(1)}%</td>
                  <td style={{ textAlign: 'center', color: '#22c55e' }}>{a.arb_edge_pct.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
