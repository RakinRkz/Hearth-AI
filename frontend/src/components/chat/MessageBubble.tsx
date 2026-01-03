import { useState } from 'react';
import { cn } from '../../lib/utils';
import type { Message, Source, SearchMetadata } from '../../lib/types';
import { User, Bot, ExternalLink, FileText, ChevronDown, ChevronRight, Search } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

// Simple markdown renderer
function renderMarkdown(content: string): React.ReactNode[] {
  const lines = content.split('\n');
  const result: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    
    // Headers
    if (line.startsWith('### ')) {
      result.push(
        <h3 key={i} className="text-base font-semibold mt-4 mb-2 text-foreground">
          {line.slice(4)}
        </h3>
      );
    } else if (line.startsWith('## ')) {
      result.push(
        <h2 key={i} className="text-lg font-bold mt-4 mb-2 text-foreground">
          {line.slice(3)}
        </h2>
      );
    } else if (line.startsWith('# ')) {
      result.push(
        <h1 key={i} className="text-xl font-bold mt-4 mb-2 text-foreground">
          {line.slice(2)}
        </h1>
      );
    }
    // Bold and italic
    else if (line.trim().length === 0) {
      result.push(<br key={i} />);
    }
    // Lists
    else if (line.match(/^[\*\-\+]\s/)) {
      result.push(
        <li key={i} className="ml-4 text-foreground">
          {line.replace(/^[\*\-\+]\s/, '')}
        </li>
      );
    }
    // Code blocks
    else if (line.startsWith('```')) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      result.push(
        <pre
          key={`code-${i}`}
          className="bg-secondary/50 rounded p-3 overflow-x-auto text-sm text-foreground mt-2 mb-2"
        >
          <code>{codeLines.join('\n')}</code>
        </pre>
      );
    }
    // Regular text with inline formatting
    else if (line.trim().length > 0) {
      const formattedContent = formatInlineMarkdown(line);
      result.push(
        <p key={i} className="text-foreground leading-relaxed">
          {formattedContent}
        </p>
      );
    }
    
    i++;
  }

  return result;
}

// Handle inline markdown: **bold**, *italic*, `code`, etc.
function formatInlineMarkdown(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  let currentIndex = 0;

  // Pattern to match **text**, *text*, `text`, [text](url)
  const regex = /\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|\[(.+?)\]\((.+?)\)/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Add text before match
    if (match.index > currentIndex) {
      parts.push(text.slice(currentIndex, match.index));
    }

    // Add matched element
    if (match[1]) {
      // **bold**
      parts.push(
        <strong key={`bold-${currentIndex}`} className="font-semibold">
          {match[1]}
        </strong>
      );
    } else if (match[2]) {
      // *italic*
      parts.push(
        <em key={`italic-${currentIndex}`} className="italic">
          {match[2]}
        </em>
      );
    } else if (match[3]) {
      // `code`
      parts.push(
        <code
          key={`code-${currentIndex}`}
          className="bg-secondary/50 px-1.5 py-0.5 rounded text-xs font-mono text-foreground"
        >
          {match[3]}
        </code>
      );
    } else if (match[4] && match[5]) {
      // [link](url)
      parts.push(
        <a
          key={`link-${currentIndex}`}
          href={match[5]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 underline"
        >
          {match[4]}
        </a>
      );
    }

    currentIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (currentIndex < text.length) {
    parts.push(text.slice(currentIndex));
  }

  return parts.length > 0 ? parts : [text];
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
        
        <div className="prose prose-invert max-w-none space-y-2 text-foreground">
          {renderMarkdown(message.content)}
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
