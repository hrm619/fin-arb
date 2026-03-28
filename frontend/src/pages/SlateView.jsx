import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useSlates, useCreateSlate, useDeleteSlate, useEvents, useFetchLines } from '@/api/hooks';
import { useSlateStore } from '@/store/slateStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableHeader, TableHead, TableBody, TableRow, TableCell } from '@/components/ui/table';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import GameBrowser from '@/components/slate/GameBrowser';
import SelectedGamesPanel from '@/components/slate/SelectedGamesPanel';
import { Plus, Trash2, ArrowRight, RefreshCw, Calendar } from 'lucide-react';

function formatDate(d) {
  return new Date(d + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatDateTime(d) {
  return new Date(d).toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: 'numeric', minute: '2-digit',
  });
}

function CreateSlateDialog({ onCreate }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [weekStart, setWeekStart] = useState('');
  const [weekEnd, setWeekEnd] = useState('');
  const [saving, setSaving] = useState(false);

  const handleCreate = async () => {
    if (!name || !weekStart || !weekEnd) return;
    setSaving(true);
    try {
      await onCreate({ name, week_start: weekStart, week_end: weekEnd });
      setOpen(false);
      setName('');
      setWeekStart('');
      setWeekEnd('');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="border-dashed h-auto py-4 px-6">
          <Plus className="h-4 w-4 mr-2" /> New Slate
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Slate</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label>Slate Name</Label>
            <Input placeholder="e.g. MLB Opening Week" value={name} onChange={e => setName(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Start Date</Label>
              <Input type="date" value={weekStart} onChange={e => setWeekStart(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>End Date</Label>
              <Input type="date" value={weekEnd} onChange={e => setWeekEnd(e.target.value)} />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={handleCreate} disabled={!name || !weekStart || !weekEnd || saving}>
            {saving ? 'Creating...' : 'Create Slate'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function SlateCard({ slate, isSelected, onSelect, onDelete }) {
  return (
    <Card
      className={`cursor-pointer transition-all hover:border-primary/50 ${isSelected ? 'ring-2 ring-primary border-primary' : ''}`}
      onClick={onSelect}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-semibold text-sm">{slate.name}</h3>
            <div className="flex items-center gap-1.5 mt-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              {formatDate(slate.week_start)} — {formatDate(slate.week_end)}
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-muted-foreground hover:text-destructive shrink-0"
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function FetchLinesButton({ eventId }) {
  const fetchLines = useFetchLines(eventId);
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={() => fetchLines.mutate()}
      disabled={fetchLines.isPending}
    >
      <RefreshCw className={`h-3.5 w-3.5 mr-1 ${fetchLines.isPending ? 'animate-spin' : ''}`} />
      {fetchLines.isPending ? 'Fetching...' : 'Lines'}
    </Button>
  );
}

function EventsTable({ slateId }) {
  const { data: events, isLoading } = useEvents(slateId);

  if (isLoading) return <p className="text-muted-foreground text-sm">Loading events...</p>;
  if (!events?.length) return <p className="text-muted-foreground text-sm py-4">No events saved yet. Browse leagues above and add games to this slate.</p>;

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/30">
            <TableHead>Matchup</TableHead>
            <TableHead>League</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Market</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map(ev => (
            <TableRow key={ev.id}>
              <TableCell className="font-medium">
                {ev.away_team} <span className="text-muted-foreground">@</span> {ev.home_team}
              </TableCell>
              <TableCell>
                <Badge variant="outline">{ev.league}</Badge>
              </TableCell>
              <TableCell className="text-muted-foreground text-sm">
                {formatDateTime(ev.event_date)}
              </TableCell>
              <TableCell className="capitalize text-sm">{ev.market_type}</TableCell>
              <TableCell>
                <Badge variant={ev.status === 'open' ? 'secondary' : 'default'} className="text-xs">
                  {ev.status}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-2">
                  <FetchLinesButton eventId={ev.id} />
                  <Button variant="ghost" size="sm" asChild>
                    <Link to={`/events/${ev.id}`}>
                      Research <ArrowRight className="h-3.5 w-3.5 ml-1" />
                    </Link>
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export default function SlateView() {
  const { data: slates, isLoading } = useSlates();
  const { currentSlateId, setCurrentSlateId } = useSlateStore();
  const deleteSlate = useDeleteSlate();
  const createSlate = useCreateSlate();

  const selectedSlate = slates?.find(s => s.id === currentSlateId);

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Slates</h1>
        <p className="text-muted-foreground text-sm mt-1">Create a slate, browse leagues, and select games to track.</p>
      </div>

      <div className="flex flex-wrap gap-3 items-start">
        {isLoading ? (
          <p className="text-muted-foreground text-sm">Loading...</p>
        ) : (
          slates?.map(s => (
            <SlateCard
              key={s.id}
              slate={s}
              isSelected={s.id === currentSlateId}
              onSelect={() => setCurrentSlateId(s.id)}
              onDelete={() => {
                deleteSlate.mutate(s.id);
                if (currentSlateId === s.id) setCurrentSlateId(null);
              }}
            />
          ))
        )}
        <CreateSlateDialog onCreate={(data) => createSlate.mutateAsync(data)} />
      </div>

      {selectedSlate && (
        <>
          <Separator />

          <div>
            <h2 className="text-lg font-semibold mb-3">Browse Games</h2>
            <GameBrowser weekStart={selectedSlate.week_start} weekEnd={selectedSlate.week_end} />
          </div>

          <SelectedGamesPanel slateId={selectedSlate.id} />

          <Separator />

          <div>
            <h2 className="text-lg font-semibold mb-3">Slate Events</h2>
            <EventsTable slateId={selectedSlate.id} />
          </div>
        </>
      )}

      {!selectedSlate && slates?.length > 0 && (
        <p className="text-muted-foreground text-sm">Select a slate above to get started.</p>
      )}
    </div>
  );
}
