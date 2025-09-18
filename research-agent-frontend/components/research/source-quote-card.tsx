'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Quote,
  Copy,
  Check,
  ExternalLink,
  User,
  Calendar,
  FileText
} from 'lucide-react';
import type { AnalysisQuote, Source } from '@/lib/types';
import { cn } from '@/lib/utils';

interface SourceQuoteCardProps {
  quote: AnalysisQuote;
  source?: Source;
  onCopy: () => void;
  isCopied: boolean;
  className?: string;
}

export function SourceQuoteCard({
  quote,
  source,
  onCopy,
  isCopied,
  className
}: SourceQuoteCardProps) {
  return (
    <Card className={cn(
      "relative overflow-hidden border-l-4 border-l-primary/50 bg-muted/20",
      className
    )}>
      <CardContent className="pt-4">
        {/* Quote Icon */}
        <Quote className="absolute top-2 right-2 h-8 w-8 text-muted-foreground/20" />

        {/* Quote Text */}
        <blockquote className="relative">
          <p className="text-base italic leading-relaxed mb-4">
            "{quote.text}"
          </p>
        </blockquote>

        {/* Attribution and Actions */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-border/50">
          <div className="space-y-1">
            {/* Author */}
            {quote.author && (
              <div className="flex items-center gap-2 text-sm">
                <User className="h-3 w-3 text-muted-foreground" />
                <span className="font-medium">{quote.author}</span>
              </div>
            )}

            {/* Source Info */}
            {source && (
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <Badge variant="outline" className="text-xs">
                  Source [{quote.source_id}]
                </Badge>
                <span className="truncate max-w-[300px]" title={source.title}>
                  {source.title}
                </span>
                {source.published_date && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {source.published_date}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={onCopy}
              className="h-8"
            >
              {isCopied ? (
                <>
                  <Check className="h-3 w-3 mr-1" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </>
              )}
            </Button>
            {source && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8"
                asChild
              >
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-3 w-3 mr-1" />
                  View
                </a>
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}