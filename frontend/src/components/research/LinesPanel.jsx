import { useLines, useFetchLines, useEstimate } from '../../api/hooks';
import { RefreshCw } from 'lucide-react';

function summarizeLines(lines) {
  if (!lines?.length) return null;

  const byOutcome = {};
  for (const l of lines) {
    const name = l.outcome_name || 'Unknown';
    if (!byOutcome[name]) byOutcome[name] = [];
    byOutcome[name].push(l);
  }

  const outcomes = Object.entries(byOutcome).map(([name, entries]) => {
    const probs = entries.map(e => e.implied_prob_pct);
    const avgProb = probs.reduce((a, b) => a + b, 0) / probs.length;
    const best = entries.reduce((a, b) =>
      a.implied_prob_pct < b.implied_prob_pct ? a : b
    );
    const worst = entries.reduce((a, b) =>
      a.implied_prob_pct > b.implied_prob_pct ? a : b
    );
    return { name, entries, avgProb, best, worst, count: entries.length };
  });

  outcomes.sort((a, b) => b.avgProb - a.avgProb);
  return { outcomes, totalBooks: new Set(lines.map(l => l.source)).size };
}

function OddsDisplay({ odds }) {
  if (!odds) return '-';
  const sign = odds > 0 ? '+' : '';
  return `${sign}${odds}`;
}

function MatchupSummary({ lines, estimate }) {
  const summary = summarizeLines(lines);
  if (!summary) return null;

  const { outcomes, totalBooks } = summary;
  const favorite = outcomes[0];
  const underdog = outcomes[1];
  const userProb = estimate?.probability_pct;

  return (
    <div style={{
      background: 'linear-gradient(135deg, #111318 0%, #0d1117 100%)',
      border: '1px solid #2a2d35',
      borderRadius: '12px',
      padding: '1.25rem',
      marginBottom: '1rem',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#6b7280' }}>
          Market Consensus
        </span>
        <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>
          {totalBooks} book{totalBooks !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Two-sided matchup */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '0.75rem', alignItems: 'center' }}>
        {/* Favorite */}
        <OutcomeSide outcome={favorite} isFavorite={true} userProb={userProb} isHome={true} />

        {/* VS divider */}
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem',
        }}>
          <span style={{ fontSize: '0.65rem', color: '#4b5563', fontWeight: 600, letterSpacing: '0.1em' }}>VS</span>
        </div>

        {/* Underdog */}
        {underdog ? (
          <OutcomeSide outcome={underdog} isFavorite={false} userProb={null} isHome={false} />
        ) : (
          <div />
        )}
      </div>

      {/* Edge callout */}
      {userProb != null && favorite && (
        <EdgeCallout userProb={userProb} marketProb={favorite.avgProb} outcomeName={favorite.name} bestOdds={favorite.best.american_odds} />
      )}
    </div>
  );
}

function OutcomeSide({ outcome, isFavorite, userProb }) {
  const probColor = isFavorite ? '#22c55e' : '#f97316';
  const bestOdds = outcome.best.american_odds;
  const spread = Math.abs(outcome.worst.implied_prob_pct - outcome.best.implied_prob_pct);

  return (
    <div style={{
      background: '#161b22',
      border: `1px solid ${isFavorite ? '#1a3a2a' : '#2a2520'}`,
      borderRadius: '10px',
      padding: '1rem',
    }}>
      {/* Team name */}
      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e5e7eb', marginBottom: '0.75rem' }}>
        {outcome.name}
      </div>

      {/* Consensus probability */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '1.6rem', fontWeight: 700, color: probColor }}>
          {outcome.avgProb.toFixed(1)}%
        </span>
        <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>avg</span>
      </div>

      {/* Best odds */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
        <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>Best odds</span>
        <span style={{
          fontSize: '0.8rem', fontWeight: 600,
          color: bestOdds > 0 ? '#22c55e' : '#e5e7eb',
          fontFamily: 'monospace',
        }}>
          <OddsDisplay odds={bestOdds} />
        </span>
      </div>

      {/* Best book */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
        <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>Best book</span>
        <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{outcome.best.source}</span>
      </div>

      {/* Range */}
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>Range</span>
        <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
          {outcome.best.implied_prob_pct.toFixed(1)}–{outcome.worst.implied_prob_pct.toFixed(1)}%
          {spread > 2 && (
            <span style={{ color: '#eab308', marginLeft: '0.3rem', fontSize: '0.65rem' }}>wide</span>
          )}
        </span>
      </div>
    </div>
  );
}

function EdgeCallout({ userProb, marketProb, outcomeName, bestOdds }) {
  const edge = userProb - marketProb;
  const hasEdge = edge > 2;
  const isNegative = edge < -2;

  const bgColor = hasEdge ? '#0a2a1a' : isNegative ? '#2a0a0a' : '#1a1a1a';
  const borderColor = hasEdge ? '#1a4a2a' : isNegative ? '#4a1a1a' : '#2a2a2a';
  const textColor = hasEdge ? '#22c55e' : isNegative ? '#ef4444' : '#9ca3af';
  const label = hasEdge ? 'EDGE DETECTED' : isNegative ? 'NEGATIVE EDGE' : 'MARGINAL';

  return (
    <div style={{
      marginTop: '1rem',
      padding: '0.75rem 1rem',
      background: bgColor,
      border: `1px solid ${borderColor}`,
      borderRadius: '8px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <span style={{
          fontSize: '0.6rem',
          fontWeight: 700,
          letterSpacing: '0.1em',
          color: textColor,
          padding: '0.15rem 0.5rem',
          border: `1px solid ${borderColor}`,
          borderRadius: '4px',
        }}>
          {label}
        </span>
        <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>
          You: <strong style={{ color: '#e5e7eb' }}>{userProb.toFixed(1)}%</strong>
          {' '}vs Market: <strong style={{ color: '#e5e7eb' }}>{marketProb.toFixed(1)}%</strong>
        </span>
      </div>
      <span style={{ fontSize: '1.1rem', fontWeight: 700, color: textColor, fontFamily: 'monospace' }}>
        {edge > 0 ? '+' : ''}{edge.toFixed(1)}%
      </span>
    </div>
  );
}

export default function LinesPanel({ eventId }) {
  const { data: lines, isLoading } = useLines(eventId);
  const { data: estimate } = useEstimate(eventId);
  const fetchLines = useFetchLines(eventId);

  return (
    <div style={{ border: '1px solid #333', borderRadius: '4px', padding: '1rem', marginBottom: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h3 style={{ marginTop: 0, marginBottom: 0 }}>Market Lines</h3>
        <button
          onClick={() => fetchLines.mutate()}
          disabled={fetchLines.isPending}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.4rem 0.8rem', fontSize: '0.8rem',
            background: '#1e3a5f', border: '1px solid #2a4a6f', borderRadius: '6px',
            color: '#e5e7eb', cursor: 'pointer',
          }}
        >
          <RefreshCw size={14} className={fetchLines.isPending ? 'animate-spin' : ''} />
          {fetchLines.isPending ? 'Fetching...' : 'Fetch Lines'}
        </button>
      </div>

      {isLoading ? <p>Loading...</p> : lines?.length === 0 ? (
        <p style={{ color: '#888' }}>No lines yet. Click Fetch Lines.</p>
      ) : (
        <>
          <MatchupSummary lines={lines} estimate={estimate} />

          <details style={{ marginTop: '0.5rem' }}>
            <summary style={{ cursor: 'pointer', fontSize: '0.8rem', color: '#6b7280', marginBottom: '0.5rem' }}>
              All lines ({lines.length})
            </summary>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #2a2d35' }}>
                  <th style={{ textAlign: 'left', padding: '0.4rem', color: '#6b7280', fontWeight: 500 }}>Source</th>
                  <th style={{ textAlign: 'left', padding: '0.4rem', color: '#6b7280', fontWeight: 500 }}>Outcome</th>
                  <th style={{ textAlign: 'center', padding: '0.4rem', color: '#6b7280', fontWeight: 500 }}>Implied %</th>
                  <th style={{ textAlign: 'center', padding: '0.4rem', color: '#6b7280', fontWeight: 500 }}>American</th>
                  <th style={{ textAlign: 'center', padding: '0.4rem', color: '#6b7280', fontWeight: 500 }}>Decimal</th>
                </tr>
              </thead>
              <tbody>
                {lines?.map(l => (
                  <tr key={l.id} style={{ borderBottom: '1px solid #1a1d25' }}>
                    <td style={{ padding: '0.4rem', color: '#9ca3af' }}>{l.source}</td>
                    <td style={{ padding: '0.4rem' }}>{l.outcome_name || '-'}</td>
                    <td style={{ textAlign: 'center', padding: '0.4rem' }}>{l.implied_prob_pct.toFixed(1)}%</td>
                    <td style={{
                      textAlign: 'center', padding: '0.4rem', fontFamily: 'monospace',
                      color: l.american_odds > 0 ? '#22c55e' : '#e5e7eb',
                    }}>
                      {l.american_odds ? <OddsDisplay odds={l.american_odds} /> : '-'}
                    </td>
                    <td style={{ textAlign: 'center', padding: '0.4rem', color: '#9ca3af' }}>{l.decimal_odds?.toFixed(2) || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </>
      )}
    </div>
  );
}
