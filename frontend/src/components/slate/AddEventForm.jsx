import { useState } from 'react';
import { useCreateEvent } from '../../api/hooks';

export default function AddEventForm({ slateId }) {
  const createEvent = useCreateEvent(slateId);
  const [form, setForm] = useState({
    home_team: '', away_team: '', sport: 'nfl', league: 'NFL',
    event_date: '', market_type: 'moneyline',
  });

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    createEvent.mutate(form, {
      onSuccess: () => setForm(f => ({ ...f, home_team: '', away_team: '', event_date: '' })),
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
      <input placeholder="Home team" value={form.home_team} onChange={set('home_team')} required />
      <input placeholder="Away team" value={form.away_team} onChange={set('away_team')} required />
      <select value={form.sport} onChange={set('sport')}>
        {['nfl', 'nba', 'mlb', 'nhl', 'ncaaf', 'ncaab'].map(s => <option key={s}>{s}</option>)}
      </select>
      <input placeholder="League" value={form.league} onChange={set('league')} required />
      <input type="datetime-local" value={form.event_date} onChange={set('event_date')} required />
      <select value={form.market_type} onChange={set('market_type')}>
        {['moneyline', 'spread', 'over_under', 'binary'].map(m => <option key={m}>{m}</option>)}
      </select>
      <button type="submit" disabled={createEvent.isPending}>Add Event</button>
    </form>
  );
}
