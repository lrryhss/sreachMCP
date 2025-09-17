'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Download,
  ExternalLink,
  Copy,
  Share2,
  FileText,
  BarChart3,
  BookOpen,
  Quote,
  Calendar,
  User,
} from 'lucide-react';
import type { ResearchReport, KeyFinding, Source } from '@/lib/types';

interface ResearchResultsProps {
  report: ResearchReport;
  onExport?: (format: string) => void;
}

export function ResearchResults({ report, onExport }: ResearchResultsProps) {
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const copyToClipboard = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="w-full space-y-6">
      {/* Header with metadata */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl">{report.query || 'Research Report'}</CardTitle>
              <CardDescription className="mt-2">
                {report.metadata?.processing_time_seconds
                  ? `Research completed in ${report.metadata.processing_time_seconds} seconds`
                  : 'Research completed'}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => onExport?.('pdf')}>
                <Download className="h-4 w-4 mr-2" />
                Export PDF
              </Button>
              <Button variant="outline" size="sm">
                <Share2 className="h-4 w-4 mr-2" />
                Share
              </Button>
            </div>
          </div>
          <div className="flex gap-4 mt-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <FileText className="h-4 w-4" />
              {report.metadata?.total_sources || report.sources_used || 0} sources analyzed
            </div>
            <div className="flex items-center gap-1">
              <BarChart3 className="h-4 w-4" />
              {report.metadata?.sources_used || report.sources?.length || 0} sources used
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Main content tabs */}
      <Tabs defaultValue="summary" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="findings">Key Findings</TabsTrigger>
          <TabsTrigger value="analysis">Detailed Analysis</TabsTrigger>
          <TabsTrigger value="sources">Sources</TabsTrigger>
        </TabsList>

        {/* Executive Summary */}
        <TabsContent value="summary">
          <Card>
            <CardHeader>
              <CardTitle>Executive Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <p className="text-base leading-relaxed">{report.executive_summary}</p>
              </div>
              {report.related_topics && report.related_topics.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-medium mb-2">Related Topics</h4>
                  <div className="flex flex-wrap gap-2">
                    {report.related_topics.map((topic, index) => (
                      <Badge key={index} variant="secondary">
                        {topic}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Key Findings */}
        <TabsContent value="findings">
          <div className="space-y-4">
            {report.key_findings && Array.isArray(report.key_findings) ? (
              report.key_findings.map((finding, index) => (
                <FindingCard key={index} finding={finding} sources={report.sources || []} />
              ))
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground">No key findings available.</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Detailed Analysis */}
        <TabsContent value="analysis">
          <Card>
            <CardContent className="pt-6">
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-6">
                  {report.detailed_analysis?.sections ? (
                    report.detailed_analysis.sections.map((section, index) => (
                      <div key={index}>
                        <h3 className="text-lg font-semibold mb-3">{section.title}</h3>
                        <div
                          className="prose prose-sm max-w-none text-muted-foreground"
                          dangerouslySetInnerHTML={{ __html: section.content }}
                        />
                        <div className="mt-2 text-xs text-muted-foreground">
                          Sources: {section.sources?.map(id => `[${id}]`).join(', ') || 'N/A'}
                        </div>
                        {index < report.detailed_analysis.sections.length - 1 && (
                          <Separator className="mt-6" />
                        )}
                      </div>
                    ))
                  ) : report.themes ? (
                    // Fallback to themes if detailed_analysis is not available
                    report.themes.map((theme: any, index: number) => (
                      <div key={index}>
                        <h3 className="text-lg font-semibold mb-3">{theme.theme}</h3>
                        <p className="text-muted-foreground">{theme.description}</p>
                        <div className="mt-2 text-xs text-muted-foreground">
                          Sources: {theme.sources?.map((id: number) => `[${id}]`).join(', ') || 'N/A'}
                        </div>
                        {index < report.themes.length - 1 && (
                          <Separator className="mt-6" />
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-muted-foreground">No detailed analysis available.</p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sources */}
        <TabsContent value="sources">
          <div className="grid gap-4">
            {report.sources && Array.isArray(report.sources) && report.sources.length > 0 ? (
              report.sources.map((source) => (
                <SourceCard
                  key={source.id}
                  source={source}
                  onCopy={(text) => copyToClipboard(text, source.id)}
                  isCopied={copiedId === source.id}
                />
              ))
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-muted-foreground">No sources available.</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Further Research Suggestions */}
      {report.further_research && report.further_research.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Suggested Further Research</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {report.further_research.map((suggestion, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-muted-foreground">•</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function FindingCard({ finding, sources }: { finding: KeyFinding; sources: Source[] }) {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <CardTitle className="text-base">{finding.finding}</CardTitle>
          <Badge className={getConfidenceColor(finding.confidence)}>
            {(finding.confidence * 100).toFixed(0)}% confidence
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground">
          Supported by {finding.supporting_sources?.length || 0} sources:
          {finding.supporting_sources?.slice(0, 3).map(id => {
            const source = sources.find(s => s.id === id);
            return source ? (
              <span key={id} className="ml-2">
                [{id}] {source.title}
              </span>
            ) : null;
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function SourceCard({
  source,
  onCopy,
  isCopied,
}: {
  source: Source;
  onCopy: (text: string) => void;
  isCopied: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <CardTitle className="text-base flex items-center gap-2">
              [{source.id}] {source.title}
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-primary"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            </CardTitle>
            <div className="flex gap-4 mt-2 text-sm text-muted-foreground">
              {source.author && (
                <div className="flex items-center gap-1">
                  <User className="h-3 w-3" />
                  {source.author}
                </div>
              )}
              {source.published_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {source.published_date}
                </div>
              )}
              <Badge variant="secondary">
                {(source.relevance_score * 100).toFixed(0)}% relevant
              </Badge>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onCopy(source.url)}
          >
            {isCopied ? 'Copied!' : <Copy className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{source.summary}</p>
        {source.quotes && source.quotes.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="text-sm font-medium">Key Quotes:</div>
            {source.quotes.map((quote, index) => (
              <div key={index} className="pl-4 border-l-2 border-muted">
                <Quote className="h-3 w-3 inline mr-2 text-muted-foreground" />
                <span className="text-sm italic">&ldquo;{quote.text}&rdquo;</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}