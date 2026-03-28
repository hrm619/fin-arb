import { useState } from 'react';
import { useTrackingSummary, useBreakdown } from '../api/hooks';
import { api } from '../api/client';

export default function TrackingDashboard() {
  const { data: summary, isLoading } = useTrackingSummary();
  const [dimension, setDimension] = useState('sport');
  const { data: breakdown } = useBreakdown(dimension);

  const handleExport = async () => {
    const csv = await api.exportCsv();
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'tracking_export.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) return <p>Loading...</p>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Tracking Dashboard</h1>
        <button onClick={handleExport}>Export CSV</button>
      </div>

      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
          {[
            { label: 'Total Graded', value: summary.total_graded },
            { label: 'Wins', value: summary.wins, color: '#22c55e' },
            { label: 'Losses', value: summary.losses, color: '#ef4444' },
            { label: 'Pushes', value: summary.pushes, color: '#eab308' },
            { label: 'Hit Rate', value: `${(summary.hit_rate * 100).toFixed(1)}%` },
            { label: 'ROI', value: `${(summary.roi * 100).toFixed(1)}%`, color: summary.roi >= 0 ? '#22c55e' : '#ef4444' },
          ].map(s => (
            <div key={s.label} style={{ padding: '1rem', border: '1px solid #333', borderRadius: '4px', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: '#aaa' }}>{s.label}</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: s.color || '#fff' }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginBottom: '1rem' }}>
        <h2>Edge Breakdown</h2>
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          {['sport', 'market_type', 'confidence_tier'].map(d => (
            <button key={d} onClick={() => setDimension(d)}
              style={{ fontWeight: dimension === d ? 'bold' : 'normal', background: dimension === d ? '#1e3a5f' : 'transparent', border: '1px solid #555', borderRadius: '3px', color: '#fff', cursor: 'pointer', padding: '0.25rem 0.5rem' }}
            >{d.replace('_', ' ')}</button>
          ))}
        </div>

        {breakdown?.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Group</th>
                <th>Count</th>
                <th>Hit Rate</th>
                <th>Avg Edge</th>
              </tr>
            </thead>
            <tbody>
              {breakdown.map(b => (
                <tr key={b.group}>
                  <td>{b.group}</td>
                  <td style={{ textAlign: 'center' }}>{b.count}</td>
                  <td style={{ textAlign: 'center', color: b.hit_rate >= 0.5 ? '#22c55e' : '#ef4444' }}>
                    {(b.hit_rate * 100).toFixed(1)}%
                  </td>
                  <td style={{ textAlign: 'center' }}>{(b.avg_edge * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: '#888' }}>No graded events yet.</p>
        )}
      </div>
    </div>
  );
}
