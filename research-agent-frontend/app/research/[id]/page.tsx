'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
import { ArrowLeft, AlertCircle } from 'lucide-react';
import { UserMenu } from '@/components/user-menu';
import { ResearchProgress } from '@/components/research/research-progress';
import { ResearchResults } from '@/components/research/research-results';
import { useResearch } from '@/hooks/use-research';
import { toast } from 'sonner';

export default function ResearchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.id as string;
  const { status, report, cancelResearch, liveProgress } = useResearch(taskId);

  useEffect(() => {
    if (!taskId) {
      router.push('/');
    }
  }, [taskId, router]);

  const handleCancel = async () => {
    try {
      await cancelResearch.mutateAsync(taskId);
      toast.success('Research cancelled');
      router.push('/');
    } catch (error: any) {
      toast.error('Failed to cancel research');
    }
  };

  const handleExport = (format: string) => {
    toast.info(`Export to ${format} coming soon!`);
  };

  if (status.isLoading || report.isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-8">
        <Button
          variant="ghost"
          onClick={() => router.push('/history')}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to History
        </Button>
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }

  if (status.error || report.error) {
    return (
      <div className="max-w-6xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => router.push('/history')}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to History
        </Button>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-destructive mb-4" />
            <h3 className="text-lg font-semibold mb-2">Error Loading Research</h3>
            <p className="text-muted-foreground text-center mb-4">
              {(status.error as any)?.message || (report.error as any)?.message || 'Failed to load research details'}
            </p>
            <Button onClick={() => router.push('/')}>
              Start New Research
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isComplete = status.data?.status === 'completed';
  const isFailed = status.data?.status === 'failed';
  const isInProgress = status.data && !isComplete && !isFailed;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={() => router.push('/history')}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to History
        </Button>

        <div className="flex items-center gap-2">
          {!isComplete && !isFailed && (
            <Button onClick={() => router.push('/')}>
              Start New Research
            </Button>
          )}
          <UserMenu />
        </div>
      </div>

      {isInProgress && status.data && (
        <ResearchProgress
          status={status.data}
          liveProgress={liveProgress}
          onCancel={handleCancel}
        />
      )}

      {isComplete && report.data && (
        <ResearchResults report={report.data} onExport={handleExport} />
      )}

      {isFailed && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-destructive mb-4" />
            <h3 className="text-lg font-semibold mb-2">Research Failed</h3>
            <p className="text-muted-foreground text-center mb-4">
              {status.data?.error || 'The research could not be completed'}
            </p>
            <Button onClick={() => router.push('/')}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}