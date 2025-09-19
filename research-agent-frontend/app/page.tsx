'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';
import { ResearchForm } from '@/components/research/research-form';
import { ResearchProgress } from '@/components/research/research-progress';
import { ResearchResults } from '@/components/research/research-results';
import { useResearch, useResearchHistory } from '@/hooks/use-research';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export default function HomePage() {
  const router = useRouter();
  const { data: session, status: sessionStatus } = useSession();
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const { startResearch, status, report, cancelResearch, liveProgress } = useResearch(currentTaskId || undefined);
  const { addToHistory } = useResearchHistory();

  // Redirect to signin if not authenticated (backup, middleware should handle this)
  useEffect(() => {
    if (sessionStatus === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [sessionStatus, router]);

  // Show loading while checking auth
  if (sessionStatus === 'loading') {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const handleSubmit = async (values: any) => {
    try {
      const result = await startResearch.mutateAsync({
        query: values.query,
        options: {
          depth: values.depth,
          max_sources: values.max_sources,
          include_pdfs: values.include_pdfs,
          include_academic: values.include_academic,
          custom_instructions: values.custom_instructions,
        },
      });

      setCurrentTaskId(result.task_id);
      addToHistory(result.task_id, values.query);
      toast.success('Research started successfully!');
    } catch (error: any) {
      toast.error(error.message || 'Failed to start research');
    }
  };

  const handleCancel = async () => {
    if (currentTaskId) {
      try {
        await cancelResearch.mutateAsync(currentTaskId);
        toast.success('Research cancelled');
        setCurrentTaskId(null);
      } catch (error: any) {
        toast.error('Failed to cancel research');
      }
    }
  };

  const handleExport = (format: string) => {
    toast.info(`Export to ${format} coming soon!`);
  };

  // Determine what to show
  const showForm = !currentTaskId || status.data?.status === 'completed' || status.data?.status === 'failed';
  const showProgress = currentTaskId && status.data && status.data.status !== 'completed' && status.data.status !== 'failed';
  const showResults = currentTaskId && report.data && status.data?.status === 'completed';

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">AI Research Assistant</h1>
        <p className="text-muted-foreground">
          Get comprehensive research reports on any topic in minutes
        </p>
      </div>

      {showForm && (
        <div className="max-w-2xl mx-auto">
          <ResearchForm onSubmit={handleSubmit} isLoading={startResearch.isPending} />
        </div>
      )}

      {showProgress && status.data && (
        <div className="max-w-2xl mx-auto">
          <ResearchProgress
            status={status.data}
            liveProgress={liveProgress}
            onCancel={handleCancel}
          />
        </div>
      )}

      {showResults && report.data && (
        <ResearchResults report={report.data} onExport={handleExport} />
      )}

      {/* Recent Research (when idle) */}
      {!currentTaskId && (
        <Card className="max-w-2xl mx-auto">
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">Getting Started</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Enter a detailed research query for better results</li>
              <li>• Choose the depth based on how thorough you want the research</li>
              <li>• Quick research takes 1-2 minutes, comprehensive can take 5-10 minutes</li>
              <li>• You can cancel the research at any time if needed</li>
              <li>• Results include sources, key findings, and detailed analysis</li>
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
