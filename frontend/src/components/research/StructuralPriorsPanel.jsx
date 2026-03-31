import { useStructuralPriors } from '../../api/hooks';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

const gradeColors = {
  HIGH: 'bg-green-600',
  MEDIUM: 'bg-yellow-600',
  LOW: 'bg-red-600',
};

export default function StructuralPriorsPanel({ eventId }) {
  const { data, isLoading, error } = useStructuralPriors(eventId);

  if (isLoading) return <Card><CardContent className="p-4 text-muted-foreground">Loading structural priors...</CardContent></Card>;
  if (error) return null;
  if (!data || data.edges.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-sm">Structural Priors</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">No validated factors apply to this matchup.</CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center justify-between">
          Structural Priors
          <span className="text-xs font-normal text-muted-foreground">
            {data.edges.length} factor{data.edges.length !== 1 ? 's' : ''}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {data.edges.map((edge) => (
          <div key={edge.edge_id} className="flex items-center justify-between text-sm border-b border-border pb-1">
            <div className="flex-1">
              <span className="font-medium">{edge.hypothesis_name}</span>
              <span className="text-muted-foreground ml-2">{edge.bucket_label}</span>
              <span className="text-muted-foreground ml-2">({edge.applies_to_team})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={edge.edge_magnitude > 0 ? 'text-green-500' : 'text-red-500'}>
                {edge.edge_magnitude > 0 ? '+' : ''}{(edge.edge_magnitude * 100).toFixed(1)}%
              </span>
              {edge.quality_grade && (
                <Badge className={`text-xs ${gradeColors[edge.quality_grade] || 'bg-gray-600'}`}>
                  {edge.quality_grade}
                </Badge>
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
