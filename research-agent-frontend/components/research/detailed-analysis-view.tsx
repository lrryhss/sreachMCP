'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ChevronRight,
  BookOpen,
  BarChart3,
  Quote,
  Hash,
  FileText,
  Clock,
  ArrowUp
} from 'lucide-react';
import type { AnalysisSection, Source } from '@/lib/types';
import { AnalysisSection as AnalysisSectionComponent } from './analysis-section';
import { cn } from '@/lib/utils';

interface DetailedAnalysisViewProps {
  sections: AnalysisSection[];
  sources: Source[];
}

export function DetailedAnalysisView({ sections, sources }: DetailedAnalysisViewProps) {
  const [activeSection, setActiveSection] = useState(0);
  const [readProgress, setReadProgress] = useState(0);
  const [showScrollTop, setShowScrollTop] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const sectionRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Calculate total word count and reading time
  const totalWords = sections.reduce((acc, section) => {
    const words = section.content.split(' ').length;
    const subsectionWords = section.subsections?.reduce(
      (subAcc, sub) => subAcc + sub.content.split(' ').length,
      0
    ) || 0;
    return acc + words + subsectionWords;
  }, 0);
  const readingTime = Math.ceil(totalWords / 200); // 200 words per minute

  // Handle scroll to track active section and progress
  useEffect(() => {
    const handleScroll = () => {
      if (!contentRef.current) return;

      const scrollTop = contentRef.current.scrollTop;
      const scrollHeight = contentRef.current.scrollHeight;
      const clientHeight = contentRef.current.clientHeight;

      // Update reading progress
      const progress = (scrollTop / (scrollHeight - clientHeight)) * 100;
      setReadProgress(Math.min(progress, 100));

      // Show/hide scroll to top button
      setShowScrollTop(scrollTop > 500);

      // Update active section based on scroll position
      let currentSection = 0;
      sectionRefs.current.forEach((ref, index) => {
        if (ref && ref.offsetTop <= scrollTop + 100) {
          currentSection = index;
        }
      });
      setActiveSection(currentSection);
    };

    const contentElement = contentRef.current;
    if (contentElement) {
      contentElement.addEventListener('scroll', handleScroll);
      return () => contentElement.removeEventListener('scroll', handleScroll);
    }
  }, []);

  const scrollToSection = (index: number) => {
    const element = sectionRefs.current[index];
    if (element && contentRef.current) {
      contentRef.current.scrollTo({
        top: element.offsetTop - 20,
        behavior: 'smooth'
      });
    }
  };

  const scrollToTop = () => {
    if (contentRef.current) {
      contentRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="flex gap-6 h-[800px] relative">
      {/* Table of Contents Sidebar */}
      <Card className="w-80 sticky top-0">
        <CardContent className="p-6">
          <div className="space-y-4">
            {/* Header */}
            <div>
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Table of Contents
              </h3>
              <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {readingTime} min read
                </span>
                <span className="flex items-center gap-1">
                  <FileText className="h-4 w-4" />
                  {sections.length} sections
                </span>
              </div>
            </div>

            {/* Reading Progress */}
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-muted-foreground">Reading Progress</span>
                <span className="font-medium">{Math.round(readProgress)}%</span>
              </div>
              <Progress value={readProgress} className="h-2" />
            </div>

            <Separator />

            {/* TOC Items */}
            <nav className="space-y-1 max-h-[600px] overflow-y-auto">
              {sections.map((section, index) => (
                <Button
                  key={index}
                  variant="ghost"
                  className={cn(
                    "w-full justify-start text-left h-auto py-3 px-3 hover:bg-muted/50",
                    activeSection === index && "bg-muted border-l-2 border-primary"
                  )}
                  onClick={() => scrollToSection(index)}
                >
                  <div className="flex items-start gap-2 w-full">
                    <ChevronRight
                      className={cn(
                        "h-4 w-4 mt-0.5 transition-transform flex-shrink-0",
                        activeSection === index && "rotate-90"
                      )}
                    />
                    <div className="flex-1 space-y-1">
                      <div className="font-medium text-sm leading-tight">
                        {section.title}
                      </div>
                      {section.subsections && section.subsections.length > 0 && (
                        <div className="text-xs text-muted-foreground">
                          {section.subsections.length} subsections
                        </div>
                      )}
                      {section.statistics && Object.keys(section.statistics).length > 0 && (
                        <Badge variant="secondary" className="text-xs mt-1">
                          <BarChart3 className="h-3 w-3 mr-1" />
                          Data included
                        </Badge>
                      )}
                    </div>
                  </div>
                </Button>
              ))}
            </nav>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Area */}
      <div className="flex-1 relative">
        <div
          ref={contentRef}
          className="h-full overflow-y-auto scroll-smooth pr-4"
        >
          <div className="space-y-8 pb-20">
            {sections.map((section, index) => (
              <div
                key={index}
                ref={el => sectionRefs.current[index] = el}
              >
                <AnalysisSectionComponent
                  section={section}
                  sources={sources}
                  sectionNumber={index + 1}
                  isActive={activeSection === index}
                />
                {index < sections.length - 1 && (
                  <Separator className="my-8" />
                )}
              </div>
            ))}

            {/* End of content message */}
            <Card className="bg-muted/50">
              <CardContent className="pt-6 text-center">
                <p className="text-sm text-muted-foreground">
                  End of Detailed Analysis • {sections.length} sections • {totalWords.toLocaleString()} words
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Scroll to Top Button */}
        {showScrollTop && (
          <Button
            size="icon"
            className="absolute bottom-4 right-4 rounded-full shadow-lg"
            onClick={scrollToTop}
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}