import { useState } from 'react';
import { useSuggestedEstimate, useGenerateSuggestedEstimate, useSubmitEstimate } from '../../api/hooks';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

const tierColors = {
  high: 'bg-green-600',
  medium: 'bg-yellow-600',
  low: 'bg-red-600',
};

export default function SuggestedEstimatePanel({ eventId, isLocked }) {
  const { data: suggestion, isLoading, error } = useSuggestedEstimate(eventId);
  const generate = useGenerateSuggestedEstimate(eventId);
  const submit = useSubmitEstimate(eventId);
  const [overrideProb, setOverrideProb] = useState('');
  const [overrideNote, setOverrideNote] = useState('');
  const [showOverride, setShowOverride] = useState(false);

  if (isLocked) return null;

  if (!suggestion && !isLoading) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-sm">Suggested Estimate</CardTitle></CardHeader>
        <CardContent>
          <Button
            size="sm"
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
          >
            {generate.isPending ? 'Generating...' : 'Generate Estimate'}
          </Button>
          {generate.isError && (
            <p className="text-sm text-red-500 mt-2">{generate.error.message}</p>
          )}
        </CardContent>
      </Card>
    );
  }

  if (isLoading) return <Card><CardContent className="p-4 text-muted-foreground">Loading...</CardContent></Card>;
  if (error || !suggestion) return null;

  const handleAccept = () => {
    submit.mutate({
      probability_pct: suggestion.suggested_prob_pct,
      note: 'Accepted suggested estimate',
      suggested_estimate_id: suggestion.id,
    });
  };

  const handleOverride = () => {
    const prob = parseFloat(overrideProb);
    if (isNaN(prob) || prob < 1 || prob > 99) return;
    submit.mutate({
      probability_pct: prob,
      note: overrideNote || 'Manual override',
      suggested_estimate_id: suggestion.id,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center justify-between">
          Suggested Estimate
          <Badge className={tierColors[suggestion.confidence_tier] || 'bg-gray-600'}>
            {suggestion.confidence_tier}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {/* Anchor */}
        <div className="flex justify-between">
          <span className="text-muted-foreground">Anchor ({suggestion.anchor_source})</span>
          <span>{suggestion.anchor_prob_pct.toFixed(1)}%</span>
        </div>

        {/* Structural adjustments */}
        {suggestion.structural_adjustments?.length > 0 && (
          <div>
            <span className="text-muted-foreground">Structural adjustments:</span>
            {suggestion.structural_adjustments.map((adj) => (
              <div key={adj.edge_id} className="flex justify-between pl-4">
                <span>{adj.metric} ({adj.applies_to_team})</span>
                <span className={adj.adjustment > 0 ? 'text-green-500' : 'text-red-500'}>
                  {adj.adjustment > 0 ? '+' : ''}{adj.adjustment.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Signal adjustments */}
        {suggestion.signal_aggregation && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Signal adjustment ({suggestion.signal_aggregation.signal_count} signals)</span>
            <span className={suggestion.total_signal_adjustment > 0 ? 'text-green-500' : 'text-red-500'}>
              {suggestion.total_signal_adjustment > 0 ? '+' : ''}{suggestion.total_signal_adjustment.toFixed(2)}
            </span>
          </div>
        )}

        {/* Suggested probability */}
        <div className="flex justify-between border-t border-border pt-2 font-bold">
          <span>Suggested probability</span>
          <span>{suggestion.suggested_prob_pct.toFixed(1)}%</span>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button size="sm" onClick={handleAccept} disabled={submit.isPending}>
            Accept
          </Button>
          <Button size="sm" variant="outline" onClick={() => setShowOverride(!showOverride)}>
            Override
          </Button>
        </div>

        {showOverride && (
          <div className="space-y-2 pt-2 border-t border-border">
            <input
              type="number"
              min="1"
              max="99"
              step="0.1"
              placeholder="Your probability %"
              value={overrideProb}
              onChange={(e) => setOverrideProb(e.target.value)}
              className="w-full px-2 py-1 bg-background border border-border rounded text-sm"
            />
            <textarea
              placeholder="Override reason (required)"
              value={overrideNote}
              onChange={(e) => setOverrideNote(e.target.value)}
              className="w-full px-2 py-1 bg-background border border-border rounded text-sm"
              rows={2}
            />
            <Button
              size="sm"
              onClick={handleOverride}
              disabled={submit.isPending || !overrideProb || !overrideNote}
            >
              Submit Override
            </Button>
          </div>
        )}

        {submit.isError && (
          <p className="text-sm text-red-500">{submit.error.message}</p>
        )}
      </CardContent>
    </Card>
  );
}
