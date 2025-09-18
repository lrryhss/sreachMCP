'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ChevronDown, ChevronUp, TrendingUp, AlertTriangle, Sparkles, Info, BarChart3, ExternalLink } from 'lucide-react';
import type { KeyFinding, Source } from '@/lib/types';

interface EnhancedFindingCardProps {
  finding: KeyFinding;
  sources: Source[];
  index: number;
}

export function EnhancedFindingCard({ finding, sources, index }: EnhancedFindingCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Get category icon and color
  const getCategoryConfig = (category?: string) => {
    switch (category) {
      case 'primary':
        return {
          icon: TrendingUp,
          bgColor: 'bg-emerald-50',
          borderColor: 'border-emerald-200',
          iconColor: 'text-emerald-600',
          badgeClass: 'bg-emerald-100 text-emerald-800',
          label: 'Primary Finding'
        };
      case 'secondary':
        return {
          icon: BarChart3,
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          iconColor: 'text-blue-600',
          badgeClass: 'bg-blue-100 text-blue-800',
          label: 'Secondary'
        };
      case 'emerging':
        return {
          icon: Sparkles,
          bgColor: 'bg-purple-50',
          borderColor: 'border-purple-200',
          iconColor: 'text-purple-600',
          badgeClass: 'bg-purple-100 text-purple-800',
          label: 'Emerging Insight'
        };
      case 'consideration':
        return {
          icon: AlertTriangle,
          bgColor: 'bg-amber-50',
          borderColor: 'border-amber-200',
          iconColor: 'text-amber-600',
          badgeClass: 'bg-amber-100 text-amber-800',
          label: 'Important Consideration'
        };
      default:
        return {
          icon: Info,
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          iconColor: 'text-gray-600',
          badgeClass: 'bg-gray-100 text-gray-800',
          label: 'Finding'
        };
    }
  };

  const config = getCategoryConfig(finding.category);
  const Icon = config.icon;

  // Get confidence color for progress bar
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.85) return 'bg-green-500';
    if (confidence >= 0.7) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  // Format statistics for display
  const formatStatistic = (key: string, value: string | number) => {
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    return value;
  };

  return (
    <Card
      className={`transition-all duration-300 hover:shadow-lg ${config.bgColor} ${config.borderColor} border-2`}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1">
            <div className={`p-2 rounded-lg bg-white shadow-sm`}>
              <Icon className={`h-5 w-5 ${config.iconColor}`} />
            </div>
            <div className="flex-1">
              <Badge className={`${config.badgeClass} mb-2`}>
                {config.label}
              </Badge>
              <h3 className="font-semibold text-base leading-tight">
                {finding.headline || finding.finding.substring(0, 50)}
              </h3>
            </div>
          </div>
        </div>

        {/* Confidence and Impact Indicators */}
        <div className="mt-4 space-y-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-muted-foreground">Confidence</span>
                <span className="text-xs font-semibold">{(finding.confidence * 100).toFixed(0)}%</span>
              </div>
              <Progress
                value={finding.confidence * 100}
                className={`h-2 ${getConfidenceColor(finding.confidence)}`}
              />
            </div>
            {finding.impact_score && (
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-muted-foreground">Impact</span>
                  <span className="text-xs font-semibold">{(finding.impact_score * 100).toFixed(0)}%</span>
                </div>
                <Progress
                  value={finding.impact_score * 100}
                  className="h-2"
                />
              </div>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <p className="text-sm text-muted-foreground leading-relaxed">
          {finding.finding}
        </p>

        {/* Statistics Preview */}
        {finding.statistics && Object.keys(finding.statistics).length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(finding.statistics).slice(0, 3).map(([key, value]) => (
              <Badge key={key} variant="outline" className="text-xs">
                {key}: {formatStatistic(key, value)}
              </Badge>
            ))}
          </div>
        )}

        {/* Expand/Collapse Button */}
        <Button
          variant="ghost"
          size="sm"
          className="mt-3 w-full"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? (
            <>
              <ChevronUp className="h-4 w-4 mr-2" />
              Show Less
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4 mr-2" />
              Show More Details
            </>
          )}
        </Button>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="mt-4 space-y-4 animate-in slide-in-from-top-2">
            {/* All Statistics */}
            {finding.statistics && Object.keys(finding.statistics).length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Key Statistics
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(finding.statistics).map(([key, value]) => (
                    <div key={key} className="bg-white/50 rounded p-2">
                      <div className="text-xs text-muted-foreground">{key}</div>
                      <div className="font-semibold">{formatStatistic(key, value)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Supporting Sources */}
            {finding.supporting_sources && finding.supporting_sources.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Supporting Sources</h4>
                <div className="space-y-1">
                  {finding.supporting_sources.map(id => {
                    const source = sources.find(s => s.id === id);
                    return source ? (
                      <a
                        key={id}
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-xs text-muted-foreground hover:text-primary transition-colors p-2 rounded hover:bg-white/50"
                      >
                        <ExternalLink className="h-3 w-3" />
                        <span className="flex-1 truncate">[{id}] {source.title}</span>
                      </a>
                    ) : null;
                  })}
                </div>
              </div>
            )}

            {/* Keywords */}
            {finding.keywords && finding.keywords.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Related Topics</h4>
                <div className="flex flex-wrap gap-1">
                  {finding.keywords.map(keyword => (
                    <Badge key={keyword} variant="secondary" className="text-xs">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}