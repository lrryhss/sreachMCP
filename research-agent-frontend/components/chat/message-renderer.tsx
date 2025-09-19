"use client";

import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import mermaid from 'mermaid';
import { Copy, Check, Maximize2, Download, Code2, FileText, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import './chat-message.module.css';

// Initialize mermaid with error suppression
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  suppressErrorRendering: true, // Prevent mermaid from showing its own error modal
  logLevel: 'error', // Reduce console noise
  flowchart: {
    curve: 'basis',
    htmlLabels: true,
    useMaxWidth: true,
  },
  themeVariables: {
    primaryColor: '#f3f4f6',
    primaryTextColor: '#1f2937',
    primaryBorderColor: '#d1d5db',
    lineColor: '#6b7280',
    secondaryColor: '#e5e7eb',
    tertiaryColor: '#f9fafb',
    background: '#ffffff',
    mainBkg: '#ffffff',
    secondBkg: '#f3f4f6',
    tertiaryBkg: '#e5e7eb',
  },
});

// Sanitize mermaid content to remove problematic Unicode characters and comments
function sanitizeMermaidContent(content: string): string {
  // First, remove mermaid comments (lines starting with %%)
  const lines = content.split('\n');
  const filteredLines = lines
    .map(line => {
      // Remove inline comments (everything after %% on a line)
      const commentIndex = line.indexOf('%%');
      if (commentIndex !== -1) {
        return line.substring(0, commentIndex).trim();
      }
      return line;
    });

  let cleanedContent = filteredLines.join('\n');

  // Replace all problematic Unicode characters
  cleanedContent = cleanedContent
    // Replace all types of dashes with regular hyphen
    .replace(/[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\u2E3A\u2E3B]/g, '-')
    // Replace non-breaking spaces
    .replace(/[\u00A0\u2007\u202F]/g, ' ')
    // Replace smart quotes with regular quotes
    .replace(/[\u2018\u2019\u201A\u201B]/g, "'")
    .replace(/[\u201C\u201D\u201E\u201F]/g, '"')
    // Replace ellipsis
    .replace(/[\u2026]/g, '...')
    // Remove zero-width spaces and other invisible characters
    .replace(/[\u200B\u200C\u200D\u2060\uFEFF]/g, '')
    // Replace various types of spaces with regular space
    .replace(/[\u2000-\u200A]/g, ' ')
    // Clean up any remaining non-ASCII characters
    .replace(/[^\x20-\x7E\n]/g, '');

  // Clean up excessive blank lines (keep max 1 blank line)
  cleanedContent = cleanedContent.replace(/\n{3,}/g, '\n\n');

  // Ensure no trailing/leading whitespace on lines
  cleanedContent = cleanedContent
    .split('\n')
    .map(line => line.trim())
    .filter((line, index, array) => {
      // Remove empty lines at start and end
      if ((index === 0 || index === array.length - 1) && line === '') {
        return false;
      }
      return true;
    })
    .join('\n');

  return cleanedContent;
}

interface MessageRendererProps {
  content: string;
  className?: string;
}

interface CodeBlockProps {
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

export function MessageRenderer({ content, className }: MessageRendererProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [downloadingCode, setDownloadingCode] = useState<string | null>(null);
  const mermaidRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  useEffect(() => {
    // Render all mermaid diagrams
    const renderMermaidDiagrams = async () => {
      for (const [id, element] of mermaidRefs.current.entries()) {
        if (element && element.textContent) {
          try {
            // Sanitize the content before rendering
            const sanitizedContent = sanitizeMermaidContent(element.textContent);

            // First validate the syntax using parse
            let isValidSyntax = true;
            try {
              await mermaid.parse(sanitizedContent);
            } catch (parseError) {
              isValidSyntax = false;
            }

            if (isValidSyntax) {
              // Only render if syntax is valid
              const { svg } = await mermaid.render(`mermaid-${id}`, sanitizedContent);
              element.innerHTML = svg;
            } else {
              throw new Error('Invalid mermaid syntax');
            }
          } catch (error) {
            // Silently handle the error without console warnings that trigger modals
            // Show the diagram as a code block with error message
            element.innerHTML = `
              <div class="space-y-2">
                <div class="text-amber-600 dark:text-amber-400 text-sm font-medium flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  Diagram syntax error - displaying as code
                </div>
                <pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                  <code>${element.textContent.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code>
                </pre>
                <div class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Tip: Copy the code and validate it in a Mermaid live editor
                </div>
              </div>
            `;
          }
        }
      }
    };

    // Wrap in setTimeout to ensure DOM is ready
    const timeoutId = setTimeout(renderMermaidDiagrams, 100);
    return () => clearTimeout(timeoutId);
  }, [content]);

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedCode(id);
      setTimeout(() => setCopiedCode(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const downloadCode = (text: string, filename: string, id: string) => {
    setDownloadingCode(id);
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setTimeout(() => setDownloadingCode(null), 1500);
  };

  const getLanguageLabel = (language: string) => {
    const labels: Record<string, string> = {
      javascript: 'JavaScript',
      typescript: 'TypeScript',
      python: 'Python',
      java: 'Java',
      cpp: 'C++',
      csharp: 'C#',
      html: 'HTML',
      css: 'CSS',
      json: 'JSON',
      yaml: 'YAML',
      sql: 'SQL',
      bash: 'Bash',
      shell: 'Shell',
      markdown: 'Markdown',
      mermaid: 'Mermaid Diagram'
    };
    return labels[language] || language.toUpperCase();
  };

  const toggleExpanded = (id: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const components = {
    code({ inline, className, children, ...props }: CodeBlockProps) {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      const codeString = String(children).replace(/\n$/, '');
      const codeId = `code-${Math.random().toString(36).substr(2, 9)}`;

      // Handle mermaid diagrams
      if (language === 'mermaid') {
        const isExpanded = expandedSections.has(codeId);
        return (
          <div className="relative my-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="absolute top-2 left-2 z-10">
              <Badge variant="secondary" className="text-xs">
                <FileText className="w-3 h-3 mr-1" />
                Mermaid Diagram
              </Badge>
            </div>
            <div className="absolute top-2 right-2 flex gap-2 z-10">
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-2 transition-all hover:bg-white/10"
                onClick={() => copyToClipboard(sanitizeMermaidContent(codeString), codeId)}
                title="Copy diagram code"
              >
                {copiedCode === codeId ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-2 transition-all hover:bg-white/10"
                onClick={() => downloadCode(sanitizeMermaidContent(codeString), 'diagram.mmd', codeId)}
                title="Download diagram"
              >
                {downloadingCode === codeId ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-2 transition-all hover:bg-white/10"
                onClick={() => toggleExpanded(codeId)}
                title={isExpanded ? "Close fullscreen" : "View fullscreen"}
              >
                {isExpanded ? (
                  <X className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
            </div>
            <div
              ref={(el) => {
                if (el) mermaidRefs.current.set(codeId, el);
              }}
              className={cn(
                "mermaid-diagram bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 p-6 rounded-lg overflow-auto transition-all duration-300",
                isExpanded && "fixed inset-8 z-50 bg-white dark:bg-gray-900 shadow-2xl"
              )}
              data-original-content={codeString}
            >
              {codeString}
            </div>
          </div>
        );
      }

      // Regular code blocks
      if (!inline && match) {
        const fileExtensions: Record<string, string> = {
          javascript: 'js',
          typescript: 'ts',
          python: 'py',
          java: 'java',
          cpp: 'cpp',
          csharp: 'cs',
          html: 'html',
          css: 'css',
          json: 'json',
          yaml: 'yml',
          sql: 'sql',
          bash: 'sh',
          shell: 'sh'
        };
        const ext = fileExtensions[language] || 'txt';
        const filename = `code.${ext}`;

        return (
          <div className="relative my-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="absolute top-2 left-2 z-10">
              <Badge variant="secondary" className="text-xs bg-gray-800 text-gray-300">
                <Code2 className="w-3 h-3 mr-1" />
                {getLanguageLabel(language)}
              </Badge>
            </div>
            <div className="absolute top-2 right-2 flex gap-1 z-10">
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-2 text-gray-400 hover:text-gray-200 transition-all hover:bg-gray-800"
                onClick={() => copyToClipboard(codeString, codeId)}
                title="Copy code"
              >
                {copiedCode === codeId ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-8 px-2 text-gray-400 hover:text-gray-200 transition-all hover:bg-gray-800"
                onClick={() => downloadCode(codeString, filename, codeId)}
                title="Download code"
              >
                {downloadingCode === codeId ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
              </Button>
            </div>
            <pre className="bg-gray-900 text-gray-100 pt-10 pb-4 px-4 rounded-lg overflow-auto shadow-lg">
              <code className={className} {...props}>
                {children}
              </code>
            </pre>
          </div>
        );
      }

      // Inline code
      return (
        <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm" {...props}>
          {children}
        </code>
      );
    },

    // Enhanced table rendering
    table({ children }: { children: React.ReactNode }) {
      return (
        <div className="my-4 overflow-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            {children}
          </table>
        </div>
      );
    },

    thead({ children }: { children: React.ReactNode }) {
      return (
        <thead className="bg-gray-50 dark:bg-gray-800">
          {children}
        </thead>
      );
    },

    tbody({ children }: { children: React.ReactNode }) {
      return (
        <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-900 dark:divide-gray-700">
          {children}
        </tbody>
      );
    },

    tr({ children }: { children: React.ReactNode }) {
      return (
        <tr className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
          {children}
        </tr>
      );
    },

    th({ children }: { children: React.ReactNode }) {
      return (
        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-gray-400">
          {children}
        </th>
      );
    },

    td({ children }: { children: React.ReactNode }) {
      return (
        <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 whitespace-normal">
          {children}
        </td>
      );
    },

    // Better list styling
    ul({ children }: { children: React.ReactNode }) {
      return (
        <ul className="my-2 ml-6 list-disc space-y-1">
          {children}
        </ul>
      );
    },

    ol({ children }: { children: React.ReactNode }) {
      return (
        <ol className="my-2 ml-6 list-decimal space-y-1">
          {children}
        </ol>
      );
    },

    li({ children }: { children: React.ReactNode }) {
      return (
        <li className="text-gray-700 dark:text-gray-300">
          {children}
        </li>
      );
    },

    // Headers with better spacing
    h1({ children }: { children: React.ReactNode }) {
      return <h1 className="text-2xl font-bold mt-6 mb-4">{children}</h1>;
    },

    h2({ children }: { children: React.ReactNode }) {
      return <h2 className="text-xl font-semibold mt-5 mb-3">{children}</h2>;
    },

    h3({ children }: { children: React.ReactNode }) {
      return <h3 className="text-lg font-semibold mt-4 mb-2">{children}</h3>;
    },

    // Blockquotes
    blockquote({ children }: { children: React.ReactNode }) {
      return (
        <blockquote className="border-l-4 border-gray-300 pl-4 py-2 my-4 italic text-gray-700 dark:border-gray-600 dark:text-gray-300">
          {children}
        </blockquote>
      );
    },

    // Horizontal rules
    hr() {
      return <hr className="my-6 border-gray-200 dark:border-gray-700" />;
    },

    // Paragraphs with proper spacing
    p({ children }: { children: React.ReactNode }) {
      return <p className="my-2 leading-relaxed">{children}</p>;
    },

    // Links
    a({ href, children }: { href?: string; children: React.ReactNode }) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 underline dark:text-blue-400 dark:hover:text-blue-300"
        >
          {children}
        </a>
      );
    },

    // Strong/Bold
    strong({ children }: { children: React.ReactNode }) {
      return <strong className="font-semibold">{children}</strong>;
    },

    // Emphasis/Italic
    em({ children }: { children: React.ReactNode }) {
      return <em className="italic">{children}</em>;
    },
  };

  return (
    <div className={cn("markdown-content", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight, rehypeRaw]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}