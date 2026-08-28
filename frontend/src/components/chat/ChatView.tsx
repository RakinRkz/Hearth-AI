import { useEffect, useRef, useState } from 'react';
import { useChat } from '../../contexts/ChatContext';
import { useConversations } from '../../contexts/ConversationContext';
import { MessageBubble } from './MessageBubble';
import { ContextDialog } from '../ContextDialog';
import { Bot, Settings2, Search, ChevronDown, ChevronRight, ExternalLink, Sparkles, ArrowDown } from 'lucide-react';
import type { SearchMetadata } from '../../lib/types';
import { DEFAULT_SYSTEM_PROMPT } from '../../lib/constants';

export function ChatView() {
  const { messages, streamingContent, isGenerating, isSummarizing, pendingSearchMetadata, setMessages } = useChat();
  const { activeConversation, setActiveConversation } = useConversations();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [contextDialogOpen, setContextDialogOpen] = useState(false);
  const [lastSyncedId, setLastSyncedId] = useState<string | null>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const [showScrollButton, setShowScrollButton] = useState(false);

  // Sync messages when active conversation changes
  useEffect(() => {
    if (activeConversation && activeConversation.id !== lastSyncedId) {
      setMessages(activeConversation.messages || []);
      setLastSyncedId(activeConversation.id);
    } else if (!activeConversation && lastSyncedId !== null) {
      setMessages([]);
      setLastSyncedId(null);
    }
  }, [activeConversation, lastSyncedId, setMessages]);

  // Check if user is scrolled to bottom
  const checkIfAtBottom = () => {
    if (!scrollRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const atBottom = scrollHeight - scrollTop - clientHeight < 100; // 100px threshold
    setIsAtBottom(atBottom);
    setShowScrollButton(!atBottom && (messages.length > 0 || streamingContent.length > 0));
  };

  // Auto-scroll only if user is at bottom
  useEffect(() => {
    if (isAtBottom && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent, isAtBottom]);

  // Listen to scroll events
  useEffect(() => {
    const scrollContainer = scrollRef.current;
    if (!scrollContainer) return;

    scrollContainer.addEventListener('scroll', checkIfAtBottom);
    return () => scrollContainer.removeEventListener('scroll', checkIfAtBottom);
  }, []);

  // Also check on initial load
  useEffect(() => {
    checkIfAtBottom();
  }, [messages]);

  // Always use messages from ChatContext (which are synced with active conversation)
  const displayMessages = messages;

  const handleSystemPromptUpdate = (newPrompt: string) => {
    if (activeConversation) {
      setActiveConversation({
        ...activeConversation,
        system_prompt: newPrompt,
      });
    }
  };

  if (displayMessages.length === 0 && !streamingContent) {
    return (
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header for empty state */}
        <div className="flex items-center justify-between border-b border-border px-4 py-2">
          <h2 className="truncate text-sm font-medium text-foreground">New Chat</h2>
          <button
            onClick={() => setContextDialogOpen(true)}
            className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            title="Context Settings"
          >
            <Settings2 className="h-4 w-4" />
            <span>Context</span>
          </button>
        </div>
        <EmptyState />
        {/* Context Dialog */}
        <ContextDialog
          open={contextDialogOpen}
          onClose={() => setContextDialogOpen(false)}
          conversationId={activeConversation?.id ?? null}
          currentSystemPrompt={activeConversation?.system_prompt ?? DEFAULT_SYSTEM_PROMPT}
          onSystemPromptUpdate={handleSystemPromptUpdate}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden relative">
      {/* Header - Always show when there are messages */}
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <h2 className="truncate text-sm font-medium text-foreground">
          {activeConversation?.title || 'Chat'}
        </h2>
        <button
          onClick={() => setContextDialogOpen(true)}
          className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          title="Context Settings"
        >
          <Settings2 className="h-4 w-4" />
          <span>Context</span>
        </button>
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto scrollbar-thin"
      >
        <div className="mx-auto w-[80%]">
          {displayMessages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}

          {/* Streaming message */}
          {streamingContent && (
            <MessageBubble
              message={{
                role: 'assistant',
                content: streamingContent,
                timestamp: new Date().toISOString(),
                sources: [],
                metadata: {},
                searchMetadata: pendingSearchMetadata || undefined,
              }}
              isStreaming
            />
          )}

          {/* Generating indicator (with search info if available) */}
          {isGenerating && !streamingContent && (
            <div className="flex gap-3 px-4 py-6 bg-secondary/30">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-assistant-bubble">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 space-y-2">
                {/* Show pending search metadata */}
                {pendingSearchMetadata && (
                  <PendingSearchInfo metadata={pendingSearchMetadata} />
                )}
                <div className="flex items-center gap-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
                </div>
              </div>
            </div>
          )}

          {/* Summarizing indicator */}
          {isSummarizing && !isGenerating && (
            <div className="flex gap-3 px-4 py-6 bg-amber-500/10">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-500">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 space-y-1">
                <span className="text-sm text-amber-600 dark:text-amber-400 font-medium">Summarizing context...</span>
                <p className="text-xs text-muted-foreground">
                  Compressing conversation history to save space
                </p>
                <div className="flex items-center gap-1 pt-1">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-amber-500 [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-amber-500 [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-amber-500" />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-10">
          <button
            onClick={() => {
              if (scrollRef.current) {
                scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
              }
            }}
            className="flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-lg hover:bg-primary/90 transition-all"
            title="Scroll to latest message"
          >
            <ArrowDown className="h-4 w-4" />
            <span>New message</span>
          </button>
        </div>
      )}

      {/* Context Dialog */}
      <ContextDialog
        open={contextDialogOpen}
        onClose={() => setContextDialogOpen(false)}
        conversationId={activeConversation?.id ?? null}
        currentSystemPrompt={activeConversation?.system_prompt ?? DEFAULT_SYSTEM_PROMPT}
        onSystemPromptUpdate={handleSystemPromptUpdate}
      />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-8 text-center bg-background">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
        <Bot className="h-8 w-8 text-muted-foreground" />
      </div>
      <h2 className="mb-2 text-xl font-semibold text-foreground">
        Start a conversation
      </h2>
      <p className="max-w-sm text-muted-foreground">
        Ask me anything! I can help with questions, search the web, or answer
        questions about your documents.
      </p>
    </div>
  );
}

interface PendingSearchInfoProps {
  metadata: SearchMetadata;
}

function PendingSearchInfo({ metadata }: PendingSearchInfoProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (metadata.skipped) {
    return (
      <div className="mb-2 flex items-center gap-2 rounded-lg border border-border/50 bg-secondary/20 px-3 py-2 text-xs text-muted-foreground">
        <Search className="h-3.5 w-3.5" />
        <span>No search needed &mdash; answered directly</span>
      </div>
    );
  }

  return (
    <div className="mb-2 rounded-lg border border-border/50 bg-secondary/20 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-xs text-muted-foreground hover:bg-secondary/30 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
        <Search className="h-3.5 w-3.5 animate-pulse" />
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
