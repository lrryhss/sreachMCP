'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  FileText,
  BarChart3,
  Clock,
  TrendingUp,
  Sparkles,
  BookOpen,
  Quote
} from 'lucide-react';
import { MediaGallery } from './media-preview';
import type { ResearchReport } from '@/lib/types';
import styles from './research-results.module.css';

interface HeroSummaryProps {
  report: ResearchReport;
}

export function HeroSummary({ report }: HeroSummaryProps) {
  const processingTime = report.metadata?.processing_time_seconds || 0;
  const totalSources = report.metadata?.total_sources || report.sources_used || 0;
  const sourcesUsed = report.metadata?.sources_used || report.sources?.length || 0;
  const keyFindingsCount = report.key_findings?.length || 0;

  const stats = [
    {
      label: 'Processing Time',
      value: `${processingTime}s`,
      icon: Clock,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-50 dark:bg-blue-950/30'
    },
    {
      label: 'Sources Analyzed',
      value: totalSources,
      icon: FileText,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-50 dark:bg-green-950/30'
    },
    {
      label: 'Sources Used',
      value: sourcesUsed,
      icon: BarChart3,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-50 dark:bg-purple-950/30'
    },
    {
      label: 'Key Findings',
      value: keyFindingsCount,
      icon: TrendingUp,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-50 dark:bg-orange-950/30'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-8 md:p-12">
        <div className="absolute top-0 right-0 -mt-4 -mr-4 h-72 w-72 rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute bottom-0 left-0 -mb-4 -ml-4 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />

        <div className="relative space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>
            <Badge variant="secondary" className="text-xs">
              AI-Powered Analysis
            </Badge>
          </div>

          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
            {report.query || 'Research Report'}
          </h1>

          <p className="text-muted-foreground text-lg max-w-3xl">
            Comprehensive analysis completed with {totalSources} sources analyzed
          </p>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            {stats.map((stat) => (
              <Card key={stat.label} className="border-0 shadow-sm">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                      <stat.icon className={`h-4 w-4 ${stat.color}`} />
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{stat.value}</p>
                      <p className="text-xs text-muted-foreground">{stat.label}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Executive Summary Card */}
      <Card className="overflow-hidden">
        <div className="bg-gradient-to-r from-primary/5 to-transparent p-6 border-b">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-semibold">Executive Summary</h2>
          </div>
        </div>
        <CardContent className="p-6">
          <article className="prose prose-lg dark:prose-invert max-w-none">
            {(() => {
              const summary = report.executive_summary || '';
              const unescapeHTML = (str: string): string => {
                const textArea = document.createElement('textarea');
                textArea.innerHTML = str;
                return textArea.value;
              };

              const hasHTMLTagStrings = summary.includes('<p>') || summary.includes('</p>');
              const hasEscapedHTML = summary.includes('&lt;p&gt;') || summary.includes('&lt;/p&gt;');
              const isHTML = hasHTMLTagStrings || hasEscapedHTML;
              const processedSummary = isHTML ? summary : summary;

              if (isHTML) {
                return (
                  <div
                    className={styles.executiveSummaryHtml}
                    dangerouslySetInnerHTML={{ __html: processedSummary }}
                  />
                );
              } else {
                const paragraphs = summary.includes('\n\n')
                  ? summary.split('\n\n').filter(p => p.trim())
                  : [summary];

                return paragraphs.map((paragraph, index) => {
                  if (index === 0) {
                    return (
                      <p key={`para-${index}`} className="text-xl leading-relaxed font-serif first-letter:text-5xl first-letter:font-bold first-letter:float-left first-letter:mr-3 first-letter:mt-1 first-letter:text-primary">
                        {paragraph}
                      </p>
                    );
                  }
                  return (
                    <p key={`para-${index}`} className="text-base leading-[1.7] text-muted-foreground">
                      {paragraph}
                    </p>
                  );
                });
              }
            })()}
          </article>

          {/* Featured Media */}
          {report.featured_media && report.featured_media.length > 0 && (
            <div className="mt-8 border-t pt-6">
              <h4 className="text-sm font-medium mb-4 flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Visual Insights
              </h4>
              <MediaGallery media={report.featured_media} />
            </div>
          )}

          {/* Pull Quote */}
          {report.pull_quote && (
            <blockquote className="mt-8 border-l-4 border-primary pl-6 py-4 bg-primary/5 rounded-r-lg">
              <div className="flex gap-2">
                <Quote className="h-5 w-5 text-primary mt-1 flex-shrink-0" />
                <p className="italic text-lg font-medium">
                  "{report.pull_quote}"
                </p>
              </div>
            </blockquote>
          )}

          {/* Related Topics */}
          {report.related_topics && report.related_topics.length > 0 && (
            <div className="mt-8 border-t pt-6">
              <h4 className="text-sm font-medium mb-3">Related Topics</h4>
              <div className="flex flex-wrap gap-2">
                {report.related_topics.map((topic, index) => (
                  <Badge key={index} variant="secondary" className="px-3 py-1 hover:bg-primary/10 transition-colors cursor-pointer">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}