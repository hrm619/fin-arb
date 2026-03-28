import { useParams, Link } from 'react-router-dom';
import { useEventResearch } from '../api/hooks';
import EstimatePanel from '../components/research/EstimatePanel';
import LinesPanel from '../components/research/LinesPanel';
import TranscriptPanel from '../components/research/TranscriptPanel';
import SignalsPanel from '../components/research/SignalsPanel';

export default function EventResearch() {
  const { id } = useParams();
  const { data: research, isLoading } = useEventResearch(id);

  if (isLoading) return <p>Loading...</p>;
  if (!research) return <p>Event not found.</p>;

  const { event } = research;

  return (
    <div>
      <Link to="/" style={{ color: '#3b82f6' }}>&larr; Back to Slates</Link>

      <div style={{ margin: '1rem 0', padding: '1rem', border: '1px solid #333', borderRadius: '4px' }}>
        <h1 style={{ marginTop: 0 }}>{event.home_team} vs {event.away_team}</h1>
        <div style={{ display: 'flex', gap: '2rem', color: '#aaa' }}>
          <span>{event.sport.toUpperCase()} — {event.league}</span>
          <span>{event.market_type}</span>
          <span>{new Date(event.event_date).toLocaleString()}</span>
          <span>Status: {event.status}</span>
          {event.confidence_tier && <span>Confidence: {event.confidence_tier}</span>}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div>
          <EstimatePanel eventId={event.id} />
          <LinesPanel eventId={event.id} />
        </div>
        <div>
          <TranscriptPanel eventId={event.id} />
          <SignalsPanel eventId={event.id} />
        </div>
      </div>
    </div>
  );
}
