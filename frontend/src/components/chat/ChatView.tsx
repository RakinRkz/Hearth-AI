import { useEffect, useRef } from 'react';
import { useChat } from '../../contexts/ChatContext';
import { useConversations } from '../../contexts/ConversationContext';
import { MessageBubble } from './MessageBubble';
import { Bot } from 'lucide-react';

export function ChatView() {
  const { messages, streamingContent, isGenerating } = useChat();
  const { activeConversation } = useConversations();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

  // Load messages from active conversation
  const displayMessages = activeConversation?.messages ?? messages;

  if (displayMessages.length === 0 && !streamingContent) {
    return <EmptyState />;
  }

  return (
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
  );
}

function EmptyState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
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
