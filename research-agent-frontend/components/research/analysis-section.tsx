'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Quote as QuoteIcon,
  BarChart3,
  FileText,
  ChevronDown,
  ChevronUp,
  Copy,
  ExternalLink,
  Hash,
  TrendingUp,
  Percent,
  DollarSign,
  Calendar,
  Users
} from 'lucide-react';
import type { AnalysisSection as AnalysisSectionType, Source } from '@/lib/types';
import { SourceQuoteCard } from './source-quote-card';
import { cn } from '@/lib/utils';

interface AnalysisSectionProps {
  section: AnalysisSectionType;
  sources: Source[];
  sectionNumber: number;
  isActive?: boolean;
}

export function AnalysisSection({ section, sources, sectionNumber, isActive }: AnalysisSectionProps) {
  const [expandedSubsections, setExpandedSubsections] = useState<number[]>([]);
  const [copiedQuote, setCopiedQuote] = useState<string | null>(null);

  const toggleSubsection = (index: number) => {
    setExpandedSubsections(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const copyQuote = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedQuote(text);
    setTimeout(() => setCopiedQuote(null), 2000);
  };

  // Get icon for statistics based on key
  const getStatIcon = (key: string) => {
    const lowerKey = key.toLowerCase();
    if (lowerKey.includes('percent') || lowerKey.includes('%')) return Percent;
    if (lowerKey.includes('growth') || lowerKey.includes('increase')) return TrendingUp;
    if (lowerKey.includes('dollar') || lowerKey.includes('revenue') || lowerKey.includes('cost')) return DollarSign;
    if (lowerKey.includes('year') || lowerKey.includes('date') || lowerKey.includes('time')) return Calendar;
    if (lowerKey.includes('user') || lowerKey.includes('people') || lowerKey.includes('customer')) return Users;
    return BarChart3;
  };

  // Format content into paragraphs if needed
  const formatContent = (content: string) => {
    // If content already has HTML paragraph tags, render as HTML
    if (content.includes('<p>')) {
      return (
        <div
          className="prose prose-sm dark:prose-invert max-w-none"
          dangerouslySetInnerHTML={{ __html: content }}
        />
      );
    }

    // Otherwise, split by double newlines and create paragraphs
    const paragraphs = content.split('\n\n').filter(p => p.trim());
    return (
      <div className="space-y-4">
        {paragraphs.map((paragraph, index) => (
          <p key={index} className="text-base leading-relaxed text-muted-foreground">
            {paragraph}
          </p>
        ))}
      </div>
    );
  };

  return (
    <Card className={cn(
      "transition-all duration-300",
      isActive && "ring-2 ring-primary ring-offset-2"
    )}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <Badge variant="outline" className="mb-2">
              <Hash className="h-3 w-3 mr-1" />
              Section {sectionNumber}
            </Badge>
            <CardTitle className="text-2xl font-bold">
              {section.title}
            </CardTitle>
          </div>
          <div className="flex gap-2">
            {section.quotes && section.quotes.length > 0 && (
              <Badge variant="secondary">
                <QuoteIcon className="h-3 w-3 mr-1" />
                {section.quotes.length} quotes
              </Badge>
            )}
            {section.statistics && Object.keys(section.statistics).length > 0 && (
              <Badge variant="secondary">
                <BarChart3 className="h-3 w-3 mr-1" />
                {Object.keys(section.statistics).length} stats
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Main Content */}
        <div className="text-base">
          {formatContent(section.content)}
        </div>

        {/* Statistics Display */}
        {section.statistics && Object.keys(section.statistics).length > 0 && (
          <div className="my-6">
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Key Data Points
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(section.statistics).map(([key, value]) => {
                const Icon = getStatIcon(key);
                return (
                  <Card key={key} className="bg-muted/30">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          <Icon className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1">
                          <div className="text-xs text-muted-foreground capitalize">
                            {key.replace(/_/g, ' ')}
                          </div>
                          <div className="text-xl font-bold">
                            {typeof value === 'number' ? value.toLocaleString() : value}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Quotes Section */}
        {section.quotes && section.quotes.length > 0 && (
          <div className="space-y-4">
            <h4 className="text-sm font-semibold flex items-center gap-2">
              <QuoteIcon className="h-4 w-4" />
              Key Quotes from Sources
            </h4>
            <div className="space-y-3">
              {section.quotes.map((quote, index) => (
                <SourceQuoteCard
                  key={index}
                  quote={quote}
                  source={sources.find(s => s.id === quote.source_id)}
                  onCopy={() => copyQuote(quote.text)}
                  isCopied={copiedQuote === quote.text}
                />
              ))}
            </div>
          </div>
        )}

        {/* Subsections */}
        {section.subsections && section.subsections.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Deep Dive Topics</h4>
            {section.subsections.map((subsection, index) => (
              <Card key={index} className="bg-muted/20">
                <CardHeader className="pb-3">
                  <Button
                    variant="ghost"
                    className="w-full justify-between text-left p-0 h-auto hover:bg-transparent"
                    onClick={() => toggleSubsection(index)}
                  >
                    <h5 className="font-medium">{subsection.subtitle}</h5>
                    {expandedSubsections.includes(index) ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </Button>
                </CardHeader>
                {expandedSubsections.includes(index) && (
                  <CardContent className="pt-0">
                    {formatContent(subsection.content)}
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}

        {/* Source References */}
        <div className="border-t pt-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Sources: {section.sources.map(id => `[${id}]`).join(', ')}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // Scroll to sources section
                const element = document.querySelector('[data-tab-value="sources"]');
                element?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <FileText className="h-3 w-3 mr-2" />
              View Sources
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}