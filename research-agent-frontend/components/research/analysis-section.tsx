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

  // Enhanced markdown parser for magazine-style formatting
  const parseMarkdown = (text: string) => {
    return text
      // Headers (### only) with enhanced styling
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      // Bold text with enhanced styling
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic text with enhanced styling
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Bullet points with diamond bullets
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      // Blockquotes with magazine styling
      .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
      // Source citations in brackets [1], [2], etc.
      .replace(/\[(\d+)\]/g, '<span class="source-citation">[$1]</span>')
      // Line breaks
      .replace(/\n/g, '<br />');
  };

  // Wrap consecutive list items in ul tags
  const wrapLists = (html: string) => {
    return html.replace(/(<li[^>]*>.*?<\/li>)(\s*<li[^>]*>.*?<\/li>)*/gs, (match) => {
      return `<ul class="space-y-1 my-4">${match}</ul>`;
    });
  };

  // Format content into paragraphs with markdown support
  const formatContent = (content: string) => {
    // More aggressive cleaning - remove all types of quotes and escaping
    let cleanContent = content.trim();

    // Debug log the raw content
    console.log('Raw content received:', {
      first100: content.substring(0, 100),
      hasDoubleQuotes: content.includes('"'),
      hasSingleQuotes: content.includes("'"),
      startsWithQuote: content[0] === '"' || content[0] === "'",
      endsWithQuote: content[content.length - 1] === '"' || content[content.length - 1] === "'"
    });

    // Remove surrounding quotes - multiple passes to handle nested quotes
    while ((cleanContent.startsWith('"') && cleanContent.endsWith('"')) ||
           (cleanContent.startsWith("'") && cleanContent.endsWith("'")) ||
           (cleanContent.startsWith('"') && cleanContent.endsWith('"')) ||
           (cleanContent.startsWith('"') && cleanContent.endsWith('"'))) {
      cleanContent = cleanContent.slice(1, -1).trim();
    }

    // Unescape any escaped quotes and other characters
    cleanContent = cleanContent
      .replace(/\\"/g, '"')
      .replace(/\\'/g, "'")
      .replace(/\\n/g, '\n')
      .replace(/\\t/g, '\t')
      .replace(/\\\\/g, '\\');

    // If content already has HTML paragraph tags, render as HTML
    if (cleanContent.includes('<p>')) {
      return (
        <div
          className="prose prose-sm dark:prose-invert max-w-none detailed-analysis-content"
          dangerouslySetInnerHTML={{ __html: cleanContent }}
        />
      );
    }

    // Check if content has markdown formatting - look for any markdown patterns
    const markdownPatterns = [
      /\*\*[^*]+\*\*/,  // Bold text
      /\*[^*]+\*/,      // Italic text
      /^#{1,6} /m,      // Headers
      /^- /m,           // Bullet lists
      /^> /m,           // Blockquotes
      /\[.*?\]\(.*?\)/, // Links
      /`[^`]+`/         // Inline code
    ];

    const hasMarkdown = markdownPatterns.some(pattern => pattern.test(cleanContent));

    console.log('Format content processing:', {
      originalLength: content.length,
      cleanedLength: cleanContent.length,
      first50Clean: cleanContent.substring(0, 50),
      hasMarkdown,
      hasBoldPattern: /\*\*[^*]+\*\*/.test(cleanContent),
      hasItalicPattern: /\*[^*]+\*/.test(cleanContent)
    });

    if (hasMarkdown || cleanContent.includes('**') || cleanContent.includes('*')) {
      // Parse markdown and convert to HTML
      const parsedContent = parseMarkdown(cleanContent);
      const contentWithLists = wrapLists(parsedContent);

      // Split into paragraphs and wrap each paragraph
      const paragraphs = contentWithLists.split('\n\n').filter(p => p.trim());
      const formattedHtml = paragraphs.map(paragraph => {
        // If paragraph already has HTML tags, use as is
        if (paragraph.includes('<h3>') || paragraph.includes('<ul>') ||
            paragraph.includes('<blockquote>')) {
          return paragraph;
        }
        // Otherwise wrap in paragraph tags with enhanced styling
        return `<p class="mb-6 text-lg leading-[1.8] text-muted-foreground font-serif">${paragraph}</p>`;
      }).join('\n');

      console.log('Generated HTML preview:', formattedHtml.substring(0, 200));

      return (
        <div
          className="detailed-analysis-content magazine-layout"
          dangerouslySetInnerHTML={{ __html: formattedHtml }}
        />
      );
    }

    // Fallback: split by double newlines and create paragraphs with enhanced typography
    const paragraphs = cleanContent.split('\n\n').filter(p => p.trim());
    return (
      <div className="detailed-analysis-content magazine-layout space-y-6">
        {paragraphs.map((paragraph, index) => (
          <p key={index} className="text-lg leading-[1.8] text-muted-foreground font-serif">
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