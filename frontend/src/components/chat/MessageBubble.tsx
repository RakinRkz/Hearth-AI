import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { cn } from '../../lib/utils';
import type { Message, Source, SearchMetadata } from '../../lib/types';
import { User, Bot, ExternalLink, FileText, ChevronDown, ChevronRight, Search, Copy, Check } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

// Code block component with copy functionality
function CodeBlock({ children }: { children: React.ReactNode }) {
  const [copied, setCopied] = useState(false);
  const code = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="relative group my-2">
      <pre className="bg-secondary/50 rounded p-3 overflow-x-auto text-sm text-foreground">
        {children}
      </pre>
      <button
        onClick={handleCopy}
        className="absolute right-2 top-2 rounded-lg bg-secondary/80 p-2 text-zinc-400 transition-colors hover:bg-secondary hover:text-foreground opacity-0 group-hover:opacity-100"
        title="Copy code"
      >
        {copied ? (
          <Check className="h-4 w-4 text-green-400" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
      </button>
    </div>
  );
}


export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopyMessage = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div
      className={cn(
        'flex gap-3 px-4 py-6 group relative',
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
        {/* Search Info (collapsible).
            searchMetadata is only set on the live socket message; after a
            conversation reload it survives as message.metadata.search. */}
        {resolveSearchMetadata(message) && (
          <SearchInfo metadata={resolveSearchMetadata(message)!} />
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
              pre: ({ children }: any) => <CodeBlock>{children}</CodeBlock>,
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

        {wasTruncated(message) && (
          <div className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-300/90">
            <span>
              This reply hit the length limit and stopped early. Raise
              &ldquo;Max tokens&rdquo; in Settings, or ask Hearth to continue.
            </span>
          </div>
        )}

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <SourcesList sources={message.sources} />
        )}
      </div>

      {/* Copy Button - visible on hover for assistant messages */}
      {!isUser && (
        <button
          onClick={handleCopyMessage}
          className="absolute right-4 top-4 rounded-lg p-2 text-zinc-400 transition-colors hover:bg-secondary hover:text-foreground opacity-0 group-hover:opacity-100"
          title="Copy message"
        >
          {copied ? (
            <Check className="h-4 w-4 text-green-400" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </button>
      )}
    </div>
  );
}

interface SearchInfoProps {
  metadata: SearchMetadata;
}

function wasTruncated(message: Message): boolean {
  return message.metadata?.truncated === true;
}

function resolveSearchMetadata(message: Message): SearchMetadata | undefined {
  if (message.searchMetadata) return message.searchMetadata;
  const persisted = message.metadata?.search;
  return persisted ? (persisted as SearchMetadata) : undefined;
}

function SearchInfo({ metadata }: SearchInfoProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (metadata.skipped) {
    return (
      <div className="mb-3 flex items-center gap-2 rounded-lg border border-border/50 bg-secondary/20 px-3 py-2 text-xs text-muted-foreground">
        <Search className="h-3.5 w-3.5" />
        <span>No search needed &mdash; answered directly</span>
      </div>
    );
  }

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
