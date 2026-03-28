import { useState } from 'react';
import { useEstimate, useSubmitEstimate } from '../../api/hooks';

export default function EstimatePanel({ eventId }) {
  const { data: estimate, isLoading } = useEstimate(eventId);
  const submitEstimate = useSubmitEstimate(eventId);
  const [prob, setProb] = useState('');
  const [note, setNote] = useState('');

  if (isLoading) return <p>Loading estimate...</p>;

  if (estimate) {
    return (
      <div style={{ border: '1px solid #333', borderRadius: '4px', padding: '1rem', marginBottom: '1rem' }}>
        <h3 style={{ marginTop: 0 }}>Your Estimate (Locked)</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
          <div><strong>Probability:</strong> {estimate.probability_pct}%</div>
          <div><strong>American:</strong> {estimate.american_odds > 0 ? '+' : ''}{estimate.american_odds}</div>
          <div><strong>Decimal:</strong> {estimate.decimal_odds?.toFixed(2)}</div>
        </div>
        {estimate.note && <div style={{ marginTop: '0.5rem', color: '#aaa' }}>{estimate.note}</div>}
      </div>
    );
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    submitEstimate.mutate({ probability_pct: parseFloat(prob), note: note || null });
  };

  return (
    <form onSubmit={handleSubmit} style={{ border: '1px solid #333', borderRadius: '4px', padding: '1rem', marginBottom: '1rem' }}>
      <h3 style={{ marginTop: 0 }}>Submit Estimate</h3>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input type="number" step="0.1" min="0.1" max="99.9" placeholder="Probability %" value={prob} onChange={e => setProb(e.target.value)} required style={{ width: '120px' }} />
        <span>%</span>
        <input placeholder="Note (optional)" value={note} onChange={e => setNote(e.target.value)} style={{ flex: 1 }} />
        <button type="submit" disabled={submitEstimate.isPending}>Lock Estimate</button>
      </div>
      {submitEstimate.isError && <p style={{ color: 'red' }}>{submitEstimate.error.message}</p>}
    </form>
  );
}
