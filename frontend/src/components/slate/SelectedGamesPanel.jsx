import { useSlateStore } from '@/store/slateStore';
import { useCreateEventsBatch } from '@/api/hooks';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Table, TableHeader, TableHead, TableBody, TableRow, TableCell } from '@/components/ui/table';
import { X, Save } from 'lucide-react';

function formatTime(iso) {
  return new Date(iso).toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: 'numeric', minute: '2-digit',
  });
}

export default function SelectedGamesPanel({ slateId }) {
  const { selectedGames, toggleGame, setGameMarketType, clearSelectedGames } = useSlateStore();
  const games = Object.values(selectedGames);
  const batchCreate = useCreateEventsBatch(slateId);

  if (games.length === 0) return null;

  const handleSave = () => {
    const events = games.map(g => ({
      home_team: g.home_team,
      away_team: g.away_team,
      sport: g.sport_key,
      league: g.sport_title,
      external_event_id: g.id,
      event_date: g.commence_time,
      market_type: g.market_type || 'moneyline',
    }));
    batchCreate.mutateAsync(events).then(() => clearSelectedGames());
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
          Selected Games ({games.length})
        </h3>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={clearSelectedGames}>
            Clear All
          </Button>
          <Button size="sm" onClick={handleSave} disabled={batchCreate.isPending}>
            <Save className="h-4 w-4 mr-2" />
            {batchCreate.isPending ? 'Saving...' : 'Save to Slate'}
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead>Matchup</TableHead>
              <TableHead>League</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Market</TableHead>
              <TableHead className="w-[40px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {games.map(g => (
              <TableRow key={g.id}>
                <TableCell className="font-medium">
                  {g.away_team} <span className="text-muted-foreground">@</span> {g.home_team}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{g.sport_title}</Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatTime(g.commence_time)}
                </TableCell>
                <TableCell>
                  <Select
                    value={g.market_type || 'moneyline'}
                    onValueChange={(v) => setGameMarketType(g.id, v)}
                  >
                    <SelectTrigger className="w-[130px] h-8 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="moneyline">Moneyline</SelectItem>
                      <SelectItem value="spread">Spread</SelectItem>
                      <SelectItem value="over_under">Over/Under</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-foreground"
                    onClick={() => toggleGame(g)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
