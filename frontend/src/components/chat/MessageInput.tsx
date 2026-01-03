import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { useChat } from '../../contexts/ChatContext';
import { useSettings } from '../../contexts/SettingsContext';
import { cn } from '../../lib/utils';
import { Send, MessageSquare, Search, FileText } from 'lucide-react';

export function MessageInput() {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, isGenerating } = useChat();
  const { mode } = useSettings();

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (!input.trim() || isGenerating) return;
    sendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const getModeIcon = () => {
    switch (mode) {
      case 'rag':
        return <FileText className="h-4 w-4" />;
      case 'search':
        return <Search className="h-4 w-4" />;
      default:
        return <MessageSquare className="h-4 w-4" />;
    }
  };

  const getPlaceholder = () => {
    switch (mode) {
      case 'rag':
        return 'Ask about your documents...';
      case 'search':
        return 'Search the web...';
      default:
        return 'Message AI...';
    }
  };

  return (
    <div className="border-t border-border bg-background p-4">
      <div className="mx-auto max-w-3xl">
        <div className="relative flex items-end gap-2 rounded-xl border border-border bg-secondary/50 p-2">
          {/* Mode indicator */}
          <div className="flex h-10 items-center px-2 text-muted-foreground">
            {getModeIcon()}
          </div>

          {/* Input */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={getPlaceholder()}
            disabled={isGenerating}
            rows={1}
            className={cn(
              'flex-1 resize-none bg-transparent text-foreground placeholder:text-muted-foreground',
              'focus:outline-none disabled:opacity-50',
              'max-h-[200px] py-2.5'
            )}
          />

          {/* Send button */}
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isGenerating}
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-lg',
              'bg-primary text-primary-foreground',
              'hover:bg-primary/90 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
            title="Send message"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>

        {/* Mode hint */}
        <p className="mt-2 text-center text-xs text-muted-foreground">
          {mode === 'chat' && 'Direct chat with AI'}
          {mode === 'rag' && 'Questions answered from your documents'}
          {mode === 'search' && 'Answers with web search results'}
        </p>
      </div>
    </div>
  );
}
