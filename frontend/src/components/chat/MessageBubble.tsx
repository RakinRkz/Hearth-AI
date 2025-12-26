import { cn } from '../../lib/utils';
import type { Message, Source } from '../../lib/types';
import { User, Bot, ExternalLink, FileText } from 'lucide-react';

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
        <div className="prose prose-invert max-w-none">
          <p className="whitespace-pre-wrap text-foreground leading-relaxed">
            {message.content}
            {isStreaming && (
              <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-foreground" />
            )}
          </p>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <SourcesList sources={message.sources} />
        )}
      </div>
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
