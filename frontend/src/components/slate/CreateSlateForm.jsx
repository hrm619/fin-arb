import { useState } from 'react';
import { useCreateSlate } from '../../api/hooks';

export default function CreateSlateForm() {
  const [name, setName] = useState('');
  const [weekStart, setWeekStart] = useState('');
  const [weekEnd, setWeekEnd] = useState('');
  const createSlate = useCreateSlate();

  const handleSubmit = (e) => {
    e.preventDefault();
    createSlate.mutate({ name, week_start: weekStart, week_end: weekEnd }, {
      onSuccess: () => { setName(''); setWeekStart(''); setWeekEnd(''); },
    });
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
      <input placeholder="Slate name" value={name} onChange={e => setName(e.target.value)} required />
      <input type="date" value={weekStart} onChange={e => setWeekStart(e.target.value)} required />
      <input type="date" value={weekEnd} onChange={e => setWeekEnd(e.target.value)} required />
      <button type="submit" disabled={createSlate.isPending}>
        {createSlate.isPending ? 'Creating...' : 'Create Slate'}
      </button>
    </form>
  );
}
