'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, AlertTriangle, Sparkles, BarChart3, Target, Brain } from 'lucide-react';
import type { KeyFinding } from '@/lib/types';

interface FindingsOverviewProps {
  findings: KeyFinding[];
}

export function FindingsOverview({ findings }: FindingsOverviewProps) {
  // Calculate statistics
  const totalFindings = findings.length;
  const avgConfidence = findings.reduce((acc, f) => acc + f.confidence, 0) / totalFindings;
  const avgImpact = findings.reduce((acc, f) => acc + (f.impact_score || 0), 0) / totalFindings;

  // Count by category
  const categoryCount = findings.reduce((acc, f) => {
    const category = f.category || 'uncategorized';
    acc[category] = (acc[category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const highConfidenceCount = findings.filter(f => f.confidence >= 0.85).length;
  const highImpactCount = findings.filter(f => (f.impact_score || 0) >= 0.8).length;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'primary':
        return TrendingUp;
      case 'secondary':
        return BarChart3;
      case 'emerging':
        return Sparkles;
      case 'consideration':
        return AlertTriangle;
      default:
        return Brain;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'primary':
        return 'bg-emerald-100 text-emerald-800';
      case 'secondary':
        return 'bg-blue-100 text-blue-800';
      case 'emerging':
        return 'bg-purple-100 text-purple-800';
      case 'consideration':
        return 'bg-amber-100 text-amber-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="mb-6 bg-gradient-to-r from-blue-50 to-purple-50 border-2">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Target className="h-5 w-5 text-blue-600" />
            Key Findings Overview
          </h3>
          <Badge variant="secondary" className="text-sm">
            {totalFindings} Total Findings
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Average Confidence */}
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-muted-foreground">Average Confidence</span>
              <span className="text-2xl font-bold">{(avgConfidence * 100).toFixed(0)}%</span>
            </div>
            <Progress value={avgConfidence * 100} className="h-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {highConfidenceCount} findings with high confidence (≥85%)
            </p>
          </div>

          {/* Average Impact */}
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-muted-foreground">Average Impact</span>
              <span className="text-2xl font-bold">{(avgImpact * 100).toFixed(0)}%</span>
            </div>
            <Progress value={avgImpact * 100} className="h-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {highImpactCount} findings with high impact (≥80%)
            </p>
          </div>

          {/* Category Distribution */}
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="mb-2">
              <span className="text-sm font-medium text-muted-foreground">Category Distribution</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {Object.entries(categoryCount).map(([category, count]) => {
                const Icon = getCategoryIcon(category);
                return (
                  <Badge
                    key={category}
                    className={`${getCategoryColor(category)} flex items-center gap-1`}
                  >
                    <Icon className="h-3 w-3" />
                    <span>{count}</span>
                  </Badge>
                );
              })}
            </div>
          </div>
        </div>

        {/* Quick Stats Bar */}
        <div className="flex flex-wrap gap-2">
          {categoryCount.primary > 0 && (
            <div className="flex items-center gap-2 bg-emerald-50 px-3 py-1 rounded-full">
              <TrendingUp className="h-4 w-4 text-emerald-600" />
              <span className="text-sm font-medium text-emerald-700">
                {categoryCount.primary} Primary Findings
              </span>
            </div>
          )}
          {categoryCount.emerging > 0 && (
            <div className="flex items-center gap-2 bg-purple-50 px-3 py-1 rounded-full">
              <Sparkles className="h-4 w-4 text-purple-600" />
              <span className="text-sm font-medium text-purple-700">
                {categoryCount.emerging} Emerging Insights
              </span>
            </div>
          )}
          {categoryCount.consideration > 0 && (
            <div className="flex items-center gap-2 bg-amber-50 px-3 py-1 rounded-full">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <span className="text-sm font-medium text-amber-700">
                {categoryCount.consideration} Important Considerations
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}