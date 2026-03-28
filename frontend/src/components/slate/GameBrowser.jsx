import { useState } from 'react';
import { useSports, useSportEvents } from '@/api/hooks';
import { useSlateStore } from '@/store/slateStore';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Table, TableHeader, TableHead, TableBody, TableRow, TableCell } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';

function formatTime(iso) {
  return new Date(iso).toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: 'numeric', minute: '2-digit',
  });
}

export default function GameBrowser({ weekStart, weekEnd }) {
  const [sportKey, setSportKey] = useState('');
  const { data: sports, isLoading: sportsLoading } = useSports();
  const { data: events, isLoading: eventsLoading } = useSportEvents(sportKey, weekStart, weekEnd);
  const { selectedGames, toggleGame, isGameSelected } = useSlateStore();

  const selectedCount = Object.keys(selectedGames).length;
  const currentSport = sports?.find(s => s.key === sportKey);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Select value={sportKey} onValueChange={setSportKey}>
          <SelectTrigger className="w-[280px]">
            <SelectValue placeholder="Select a league..." />
          </SelectTrigger>
          <SelectContent>
            {sportsLoading ? (
              <SelectItem value="_loading" disabled>Loading sports...</SelectItem>
            ) : (
              sports?.map(s => (
                <SelectItem key={s.key} value={s.key}>{s.title}</SelectItem>
              ))
            )}
          </SelectContent>
        </Select>

        {selectedCount > 0 && (
          <Badge variant="secondary" className="text-sm">
            {selectedCount} game{selectedCount !== 1 ? 's' : ''} selected
          </Badge>
        )}
      </div>

      {sportKey && (
        <div className="rounded-lg border border-border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30">
                <TableHead className="w-[50px]"></TableHead>
                <TableHead>Matchup</TableHead>
                <TableHead>Date & Time</TableHead>
                <TableHead className="text-right">League</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {eventsLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton className="h-5 w-5 rounded-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-16 ml-auto" /></TableCell>
                  </TableRow>
                ))
              ) : events?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                    No upcoming games found for this date range
                  </TableCell>
                </TableRow>
              ) : (
                events?.map(ev => {
                  const selected = isGameSelected(ev.id);
                  return (
                    <TableRow
                      key={ev.id}
                      className={`cursor-pointer ${selected ? 'bg-primary/10' : ''}`}
                      onClick={() => toggleGame({
                        id: ev.id,
                        sport_key: ev.sport_key,
                        sport_title: currentSport?.title || ev.sport_key,
                        home_team: ev.home_team,
                        away_team: ev.away_team,
                        commence_time: ev.commence_time,
                      })}
                    >
                      <TableCell>
                        <Checkbox checked={selected} />
                      </TableCell>
                      <TableCell className="font-medium">
                        {ev.away_team} <span className="text-muted-foreground">@</span> {ev.home_team}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatTime(ev.commence_time)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant="outline">{currentSport?.title || ev.sport_key}</Badge>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
