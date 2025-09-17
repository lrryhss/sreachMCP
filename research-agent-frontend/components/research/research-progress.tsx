'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  AlertCircle,
  FileSearch,
  Globe,
  Brain,
  FileText,
} from 'lucide-react';
import type { ResearchStatus } from '@/lib/types';

interface ResearchProgressProps {
  status: ResearchStatus;
  liveProgress?: any;
  onCancel?: () => void;
}

const stepIcons: Record<string, any> = {
  query_analysis: Brain,
  search_execution: Globe,
  content_fetching: FileSearch,
  content_synthesis: Brain,
  report_generation: FileText,
};

const stepLabels: Record<string, string> = {
  query_analysis: 'Analyzing Query',
  search_execution: 'Searching Sources',
  content_fetching: 'Fetching Content',
  content_synthesis: 'Synthesizing Information',
  report_generation: 'Generating Report',
};

export function ResearchProgress({ status, liveProgress, onCancel }: ResearchProgressProps) {
  const [estimatedTime, setEstimatedTime] = useState<string>('');

  useEffect(() => {
    if (status.estimated_completion) {
      const updateTime = () => {
        const remaining = new Date(status.estimated_completion!).getTime() - Date.now();
        if (remaining > 0) {
          const minutes = Math.floor(remaining / 60000);
          const seconds = Math.floor((remaining % 60000) / 1000);
          setEstimatedTime(`${minutes}m ${seconds}s`);
        } else {
          setEstimatedTime('Almost done...');
        }
      };
      updateTime();
      const interval = setInterval(updateTime, 1000);
      return () => clearInterval(interval);
    }
  }, [status.estimated_completion]);

  const allSteps = [
    'query_analysis',
    'search_execution',
    'content_fetching',
    'content_synthesis',
    'report_generation',
  ];

  const getStepStatus = (step: string) => {
    if (status.progress.steps_completed.includes(step)) return 'completed';
    if (status.progress.current_step === step) return 'current';
    return 'pending';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Research Progress</CardTitle>
            <CardDescription>
              {status.query}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              variant={
                status.status === 'completed' ? 'default' :
                status.status === 'failed' ? 'destructive' :
                'secondary'
              }
            >
              {status.status}
            </Badge>
            {estimatedTime && status.status !== 'completed' && status.status !== 'failed' && (
              <Badge variant="outline">
                {estimatedTime} remaining
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Overall Progress</span>
            <span>{status.progress.percentage}%</span>
          </div>
          <Progress value={status.progress.percentage} className="h-2" />
        </div>

        {/* Step indicators */}
        <div className="space-y-3">
          {allSteps.map((step, index) => {
            const stepStatus = getStepStatus(step);
            const Icon = stepIcons[step] || Circle;

            return (
              <div
                key={step}
                className={`flex items-center gap-3 ${
                  stepStatus === 'pending' ? 'opacity-50' : ''
                }`}
              >
                {stepStatus === 'completed' ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : stepStatus === 'current' ? (
                  <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
                ) : (
                  <Circle className="h-5 w-5 text-gray-300" />
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    <span className="font-medium">{stepLabels[step] || step}</span>
                  </div>
                  {stepStatus === 'current' && liveProgress?.message && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {liveProgress.message}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Source statistics */}
        {(status.progress.sources_found !== undefined || status.progress.sources_processed !== undefined) && (
          <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
            {status.progress.sources_found !== undefined && (
              <div>
                <div className="text-2xl font-bold">{status.progress.sources_found}</div>
                <div className="text-sm text-muted-foreground">Sources Found</div>
              </div>
            )}
            {status.progress.sources_processed !== undefined && (
              <div>
                <div className="text-2xl font-bold">{status.progress.sources_processed}</div>
                <div className="text-sm text-muted-foreground">Sources Processed</div>
              </div>
            )}
          </div>
        )}

        {/* Live updates */}
        {liveProgress && liveProgress.type === 'source_found' && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Found: {liveProgress.data.title}
              <br />
              <span className="text-sm text-muted-foreground">
                Relevance: {(liveProgress.data.relevance * 100).toFixed(0)}%
              </span>
            </AlertDescription>
          </Alert>
        )}

        {/* Error state */}
        {status.error && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{status.error}</AlertDescription>
          </Alert>
        )}

        {/* Action buttons */}
        {status.status !== 'completed' && status.status !== 'failed' && onCancel && (
          <Button variant="destructive" onClick={onCancel} className="w-full">
            Cancel Research
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export function ResearchProgressSkeleton() {
  return (
    <Card className="w-full">
      <CardHeader>
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-64 mt-2" />
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-2 w-full" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-5 w-5 rounded-full" />
              <Skeleton className="h-4 w-32" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}