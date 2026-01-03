import { useEffect, useRef, useState } from 'react';
import { useChat } from '../../contexts/ChatContext';
import { useConversations } from '../../contexts/ConversationContext';
import { MessageBubble } from './MessageBubble';
import { ContextDialog } from '../ContextDialog';
import { Bot, Settings2 } from 'lucide-react';

export function ChatView() {
  const { messages, streamingContent, isGenerating, setMessages } = useChat();
  const { activeConversation, setActiveConversation } = useConversations();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [contextDialogOpen, setContextDialogOpen] = useState(false);
  const [lastSyncedId, setLastSyncedId] = useState<string | null>(null);

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

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

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
          currentSystemPrompt={activeConversation?.system_prompt ?? 'You are a helpful AI assistant.'}
          onSystemPromptUpdate={handleSystemPromptUpdate}
        />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
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
        <div className="mx-auto max-w-3xl">
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
              }}
              isStreaming
            />
          )}

          {/* Generating indicator */}
          {isGenerating && !streamingContent && (
            <div className="flex gap-3 px-4 py-6 bg-secondary/30">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-assistant-bubble">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div className="flex items-center gap-1">
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground" />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Context Dialog */}
      <ContextDialog
        open={contextDialogOpen}
        onClose={() => setContextDialogOpen(false)}
        conversationId={activeConversation?.id ?? null}
        currentSystemPrompt={activeConversation?.system_prompt ?? 'You are a helpful AI assistant.'}
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
