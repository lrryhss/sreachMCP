export type ResearchDepth = 'quick' | 'standard' | 'comprehensive';
export type ResearchStatus = 'pending' | 'searching' | 'fetching' | 'synthesizing' | 'completed' | 'failed';
export type OutputFormat = 'html' | 'json' | 'markdown';

export interface ResearchOptions {
  depth?: ResearchDepth;
  max_sources?: number;
  languages?: string[];
  time_range?: 'day' | 'week' | 'month' | 'year' | 'all';
  include_pdfs?: boolean;
  include_academic?: boolean;
  follow_links?: boolean;
  custom_instructions?: string;
}

export interface ResearchRequest {
  query: string;
  options?: ResearchOptions;
  output_format?: OutputFormat;
  webhook_url?: string;
}

export interface ResearchTask {
  task_id: string;
  status: string;
  estimated_duration_seconds?: number;
  created_at: string;
  links: {
    status: string;
    report: string;
    stream: string;
  };
}

export interface ResearchProgress {
  percentage: number;
  current_step: string;
  steps_completed: string[];
  steps_remaining?: string[];
  sources_found?: number;
  sources_processed?: number;
}

export interface ResearchStatus {
  task_id: string;
  status: ResearchStatus;
  progress: ResearchProgress;
  query: string;
  created_at: string;
  updated_at: string;
  estimated_completion?: string;
  error?: string | null;
}

export interface KeyFinding {
  headline?: string;
  finding: string;
  category?: 'primary' | 'secondary' | 'emerging' | 'consideration';
  impact_score?: number;
  confidence: number;
  supporting_sources: number[];
  statistics?: Record<string, string | number>;
  keywords?: string[];
}

export interface MediaItem {
  url: string;
  type: 'image' | 'video' | 'youtube' | 'tiktok';
  thumbnail?: string;
  title?: string;
  description?: string;
}

export interface Source {
  id: number;
  title: string;
  url: string;
  author?: string;
  published_date?: string;
  relevance_score: number;
  summary: string;
  quotes?: Array<{
    text: string;
    context: string;
  }>;
  media?: MediaItem[];
}

export interface AnalysisQuote {
  text: string;
  source_id: number;
  author?: string;
}

export interface AnalysisSection {
  title: string;
  content: string;
  quotes?: AnalysisQuote[];
  statistics?: Record<string, string | number>;
  sources: number[];
  subsections?: Array<{
    subtitle: string;
    content: string;
  }>;
}

export interface ResearchReport {
  task_id: string;
  query: string;
  status: string;
  metadata: {
    total_sources: number;
    sources_used: number;
    processing_time_seconds: number;
    report_generated_at: string;
    total_media_found?: number;
  };
  executive_summary: string;
  key_findings: KeyFinding[];
  detailed_analysis: {
    sections: AnalysisSection[];
  };
  sources: Source[];
  related_topics?: string[];
  further_research?: string[];
  featured_media?: MediaItem[];
  pull_quote?: string;
  themes?: Array<{
    theme: string;
    description: string;
    sources: number[];
  }>;
}

export interface SSEMessage {
  type: 'progress' | 'source_found' | 'content_extracted' | 'synthesis_update' | 'complete' | 'error';
  data: any;
}