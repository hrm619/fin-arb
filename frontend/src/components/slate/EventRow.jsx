import { Link } from 'react-router-dom';

const tierColors = { high: '#22c55e', medium: '#eab308', low: '#ef4444' };

export default function EventRow({ event, onDelete }) {
  return (
    <tr>
      <td><Link to={`/events/${event.id}`}>{event.home_team} vs {event.away_team}</Link></td>
      <td>{event.sport}</td>
      <td>{event.market_type}</td>
      <td>{new Date(event.event_date).toLocaleDateString()}</td>
      <td>
        {event.confidence_tier && (
          <span style={{ color: tierColors[event.confidence_tier], fontWeight: 'bold' }}>
            {event.confidence_tier}
          </span>
        )}
      </td>
      <td>{event.status}</td>
      <td><button onClick={() => onDelete(event.id)} style={{ color: 'red', cursor: 'pointer', background: 'none', border: 'none' }}>x</button></td>
    </tr>
  );
}
