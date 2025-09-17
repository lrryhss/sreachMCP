'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Search,
  Calendar,
  Clock,
  FileText,
  Trash2,
  ChevronRight,
  Archive
} from 'lucide-react';
import { useResearchHistory } from '@/hooks/use-research';
import { formatDistanceToNow } from 'date-fns';

export default function HistoryPage() {
  const router = useRouter();
  const { history, removeFromHistory, clearHistory } = useResearchHistory();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleViewResearch = (taskId: string) => {
    router.push(`/research/${taskId}`);
  };

  const handleDeleteItem = (taskId: string) => {
    removeFromHistory(taskId);
    if (selectedId === taskId) {
      setSelectedId(null);
    }
  };

  const sortedHistory = [...history].sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  if (history.length === 0) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center space-y-2 mb-8">
          <h1 className="text-4xl font-bold tracking-tight">Research History</h1>
          <p className="text-muted-foreground">
            Your previous research queries and reports
          </p>
        </div>

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Archive className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Research History</h3>
            <p className="text-muted-foreground text-center mb-4">
              Start your first research to see it here
            </p>
            <Button onClick={() => router.push('/')}>
              <Search className="h-4 w-4 mr-2" />
              Start Research
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">Research History</h1>
          <p className="text-muted-foreground">
            {history.length} research {history.length === 1 ? 'query' : 'queries'} saved
          </p>
        </div>

        {history.length > 0 && (
          <Button
            variant="outline"
            onClick={() => {
              if (confirm('Are you sure you want to clear all history?')) {
                clearHistory();
              }
            }}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear All
          </Button>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {sortedHistory.map((item) => (
          <Card
            key={item.taskId}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => handleViewResearch(item.taskId)}
          >
            <CardHeader>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <CardTitle className="text-base line-clamp-2">
                    {item.query}
                  </CardTitle>
                  <CardDescription className="mt-2">
                    <div className="flex items-center gap-2 text-xs">
                      <Calendar className="h-3 w-3" />
                      {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
                    </div>
                  </CardDescription>
                </div>
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center">
                <Badge variant={item.status === 'completed' ? 'default' : 'secondary'}>
                  {item.status || 'pending'}
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteItem(item.taskId);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}