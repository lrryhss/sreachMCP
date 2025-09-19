import { useState, useCallback, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/api';
import type { ResearchRequest, ResearchTask, ResearchStatus, ResearchReport } from '@/lib/types';

export function useResearch(taskId?: string) {
  const queryClient = useQueryClient();
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const [liveProgress, setLiveProgress] = useState<any>(null);

  // Start research mutation
  const startResearch = useMutation({
    mutationFn: (request: ResearchRequest) => api.startResearch(request),
    onSuccess: (data) => {
      // Invalidate any cached queries
      queryClient.invalidateQueries({ queryKey: ['research-status', data.task_id] });
    },
  });

  // Get research status query
  const status = useQuery({
    queryKey: ['research-status', taskId],
    queryFn: () => taskId ? api.getResearchStatus(taskId) : Promise.reject('No task ID'),
    enabled: !!taskId,
    refetchInterval: (data) => {
      // Stop polling if completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        // Invalidate cache to ensure fresh data
        queryClient.invalidateQueries({ queryKey: ['research-status', taskId] });
        queryClient.invalidateQueries({ queryKey: ['research-report', taskId] });
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });

  // Get research report query
  const report = useQuery({
    queryKey: ['research-report', taskId],
    queryFn: async () => {
      if (!taskId) return Promise.reject('No task ID');
      const data = await api.getResearchReport(taskId);

      // Transform the data structure to match frontend expectations
      if (data && data.synthesis) {
        return {
          ...data,
          executive_summary: data.synthesis.executive_summary,
          key_findings: data.synthesis.key_findings,
          detailed_analysis: data.synthesis.detailed_analysis,
          themes: data.synthesis.themes,
          contradictions: data.synthesis.contradictions,
          recommendations: data.synthesis.recommendations,
          further_research: data.synthesis.further_research,
          pull_quote: data.synthesis.pull_quote,
          sources: data.sources || [],
          featured_media: data.featured_media || [],
          metadata: data.metadata || {},
        };
      }
      return data;
    },
    enabled: !!taskId && status.data?.status === 'completed',
  });

  // Cancel research mutation
  const cancelResearch = useMutation({
    mutationFn: (taskId: string) => api.cancelResearch(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research-status', taskId] });
    },
  });

  // Setup SSE connection
  useEffect(() => {
    if (!taskId || !status.data) return;

    // Only create SSE if research is in progress
    if (status.data.status === 'completed' || status.data.status === 'failed') {
      if (eventSource) {
        eventSource.close();
        setEventSource(null);
      }
      return;
    }

    if (!eventSource) {
      const source = api.createEventSource(taskId);

      source.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        setLiveProgress(data);
      });

      source.addEventListener('source_found', (event) => {
        const data = JSON.parse(event.data);
        console.log('Source found:', data);
      });

      source.addEventListener('complete', (event) => {
        const data = JSON.parse(event.data);
        queryClient.invalidateQueries({ queryKey: ['research-status', taskId] });
        queryClient.invalidateQueries({ queryKey: ['research-report', taskId] });
        source.close();
        setEventSource(null);
      });

      source.addEventListener('error', (event: any) => {
        console.error('SSE error:', event);
        if (event.readyState === EventSource.CLOSED) {
          setEventSource(null);
        }
      });

      setEventSource(source);
    }

    return () => {
      if (eventSource) {
        eventSource.close();
        setEventSource(null);
      }
    };
  }, [taskId, status.data?.status]);

  return {
    startResearch,
    status,
    report,
    cancelResearch,
    liveProgress,
  };
}

export function useResearchHistory() {
  // This would fetch from local storage or a backend endpoint
  const [history, setHistory] = useState<Array<{
    taskId: string;
    query: string;
    timestamp: string;
    status?: string;
  }>>([]);

  useEffect(() => {
    const stored = localStorage.getItem('research-history');
    if (stored) {
      setHistory(JSON.parse(stored));
    }
  }, []);

  const addToHistory = useCallback((taskId: string, query: string, status: string = 'pending') => {
    const newItem = {
      taskId,
      query,
      timestamp: new Date().toISOString(),
      status
    };
    const updated = [newItem, ...history.filter(item => item.taskId !== taskId)].slice(0, 20); // Keep last 20, avoid duplicates
    setHistory(updated);
    localStorage.setItem('research-history', JSON.stringify(updated));
  }, [history]);

  const removeFromHistory = useCallback((taskId: string) => {
    const updated = history.filter(item => item.taskId !== taskId);
    setHistory(updated);
    localStorage.setItem('research-history', JSON.stringify(updated));
  }, [history]);

  const clearHistory = useCallback(() => {
    setHistory([]);
    localStorage.removeItem('research-history');
  }, []);

  return { history, addToHistory, removeFromHistory, clearHistory };
}