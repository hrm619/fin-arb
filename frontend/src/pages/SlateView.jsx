import { useState } from 'react';
import { useSlates, useEvents, useDeleteSlate, useDeleteEvent } from '../api/hooks';
import CreateSlateForm from '../components/slate/CreateSlateForm';
import AddEventForm from '../components/slate/AddEventForm';
import EventRow from '../components/slate/EventRow';
import ShortlistPanel from '../components/slate/ShortlistPanel';

export default function SlateView() {
  const { data: slates, isLoading } = useSlates();
  const [selectedSlateId, setSelectedSlateId] = useState(null);
  const { data: events } = useEvents(selectedSlateId);
  const deleteSlate = useDeleteSlate();
  const deleteEvent = useDeleteEvent(selectedSlateId);

  if (isLoading) return <p>Loading slates...</p>;

  return (
    <div>
      <h1>Slates</h1>
      <CreateSlateForm />

      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
        {slates?.map(s => (
          <div
            key={s.id}
            onClick={() => setSelectedSlateId(s.id)}
            style={{
              padding: '0.5rem 1rem', cursor: 'pointer', borderRadius: '4px',
              border: selectedSlateId === s.id ? '2px solid #3b82f6' : '1px solid #555',
              background: selectedSlateId === s.id ? '#1e3a5f' : 'transparent',
            }}
          >
            <strong>{s.name}</strong>
            <div style={{ fontSize: '0.8rem', color: '#aaa' }}>{s.week_start} - {s.week_end}</div>
            <button
              onClick={(e) => { e.stopPropagation(); deleteSlate.mutate(s.id); }}
              style={{ fontSize: '0.7rem', color: 'red', background: 'none', border: 'none', cursor: 'pointer', marginTop: '0.25rem' }}
            >delete</button>
          </div>
        ))}
      </div>

      {selectedSlateId && (
        <>
          <ShortlistPanel slateId={selectedSlateId} />
          <AddEventForm slateId={selectedSlateId} />
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Matchup</th>
                <th>Sport</th>
                <th>Market</th>
                <th>Date</th>
                <th>Confidence</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {events?.map(e => (
                <EventRow key={e.id} event={e} onDelete={(id) => deleteEvent.mutate(id)} />
              ))}
            </tbody>
          </table>
          {events?.length === 0 && <p style={{ color: '#888' }}>No events yet. Add one above.</p>}
        </>
      )}

      {!selectedSlateId && slates?.length > 0 && <p style={{ color: '#888' }}>Select a slate above.</p>}
    </div>
  );
}
