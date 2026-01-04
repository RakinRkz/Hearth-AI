import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { cn } from '../../lib/utils';
import type { Message, Source, SearchMetadata } from '../../lib/types';
import { User, Bot, ExternalLink, FileText, ChevronDown, ChevronRight, Search } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex gap-3 px-4 py-6',
        isUser ? 'bg-transparent' : 'bg-secondary/30'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-user-bubble' : 'bg-assistant-bubble'
        )}
      >
        {isUser ? (
          <User className="h-5 w-5 text-white" />
        ) : (
          <Bot className="h-5 w-5 text-white" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 space-y-2 overflow-hidden">
        {/* Search Info (collapsible) */}
        {message.searchMetadata && (
          <SearchInfo metadata={message.searchMetadata} />
        )}
        
        <div className="max-w-none space-y-2 text-foreground">
          <ReactMarkdown
            components={{
              h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-2 text-blue-300">{children}</h1>,
              h2: ({ children }) => <h2 className="text-lg font-bold mt-4 mb-2 text-blue-300">{children}</h2>,
              h3: ({ children }) => <h3 className="text-base font-semibold mt-4 mb-2 text-indigo-300">{children}</h3>,
              h4: ({ children }) => <h4 className="text-sm font-semibold mt-3 mb-1 text-violet-300">{children}</h4>,
              p: ({ children }) => <p className="text-foreground leading-relaxed">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold text-yellow-300 inline">{children}</strong>,
              em: ({ children }) => <em className="italic text-cyan-300 inline">{children}</em>,
              code: ({ inline, children }: any) => {
                // Only render inline code styling, block code is handled by pre
                if (inline) {
                  return (
                    <code className="bg-orange-500/20 px-1.5 py-0.5 rounded text-xs font-mono text-orange-300 whitespace-nowrap">
                      {children}
                    </code>
                  );
                }
                // Return just the code content for block code (pre will handle styling)
                return <code className="font-mono">{children}</code>;
              },
              pre: ({ children }: any) => (
                <pre className="bg-secondary/50 rounded p-3 overflow-x-auto text-sm text-foreground mt-2 mb-2">
                  {children}
                </pre>
              ),
              ul: ({ children }) => <ul className="list-disc list-inside ml-2 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside ml-2 space-y-1">{children}</ol>,
              li: ({ children }) => <li className="text-foreground">{children}</li>,
              a: ({ href, children }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 underline"
                >
                  {children}
                </a>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
          {isStreaming && (
            <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-foreground" />
          )}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <SourcesList sources={message.sources} />
        )}
      </div>
    </div>
  );
}

interface SearchInfoProps {
  metadata: SearchMetadata;
}

function SearchInfo({ metadata }: SearchInfoProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mb-3 rounded-lg border border-border/50 bg-secondary/20 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-xs text-muted-foreground hover:bg-secondary/30 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
        <Search className="h-3.5 w-3.5" />
        <span>Searched: </span>
        <span className="font-medium text-foreground/80 truncate">"{metadata.query}"</span>
        <span className="ml-auto text-muted-foreground/70">
          {metadata.results.length} results
        </span>
      </button>
      
      {isExpanded && (
        <div className="border-t border-border/30 px-3 py-2 space-y-2">
          {metadata.results.map((result, index) => (
            <a
              key={index}
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded-md px-2 py-1.5 hover:bg-secondary/40 transition-colors"
            >
              <div className="flex items-center gap-2 text-xs">
                <span className="text-muted-foreground">{index + 1}.</span>
                <span className="font-medium text-foreground/90 truncate">{result.title}</span>
                <ExternalLink className="h-3 w-3 text-muted-foreground shrink-0" />
              </div>
              <p className="mt-0.5 text-xs text-muted-foreground/80 line-clamp-2 pl-4">
                {result.snippet}
              </p>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

interface SourcesListProps {
  sources: Source[];
}

function SourcesList({ sources }: SourcesListProps) {
  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-medium text-muted-foreground">Sources:</p>
      <div className="flex flex-wrap gap-2">
        {sources.map((source, index) => (
          <SourceBadge key={index} source={source} index={index + 1} />
        ))}
      </div>
    </div>
  );
}

interface SourceBadgeProps {
  source: Source;
  index: number;
}

function SourceBadge({ source, index }: SourceBadgeProps) {
  const isWebSource = !!source.url;

  if (isWebSource) {
    return (
      <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 rounded-md bg-secondary px-2 py-1 text-xs text-secondary-foreground hover:bg-secondary/80 transition-colors"
        title={source.content}
      >
        <span className="font-medium">[{index}]</span>
        <ExternalLink className="h-3 w-3" />
        <span className="max-w-[150px] truncate">{source.title}</span>
      </a>
    );
  }

  return (
    <div
      className="inline-flex items-center gap-1.5 rounded-md bg-secondary px-2 py-1 text-xs text-secondary-foreground"
      title={source.content}
    >
      <span className="font-medium">[{index}]</span>
      <FileText className="h-3 w-3" />
      <span className="max-w-[150px] truncate">{source.title}</span>
      {source.page && <span className="text-muted-foreground">p.{source.page}</span>}
    </div>
  );
}
