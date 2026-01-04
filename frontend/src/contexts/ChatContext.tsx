import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  useEffect,
  type ReactNode,
} from 'react';
import type { Message, WSMessageOut, SearchMetadata, ContextUsage } from '../lib/types';
import { useConversations } from './ConversationContext';

interface ChatContextType {
  messages: Message[];
  streamingContent: string;
  isGenerating: boolean;
  isSummarizing: boolean;
  error: string | null;
  pendingSearchMetadata: SearchMetadata | null;
  contextUsage: ContextUsage | null;
  sendMessage: (content: string) => void;
  cancelGeneration: () => void;
  clearMessages: () => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
}

const ChatContext = createContext<ChatContextType | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingSearchMetadata, setPendingSearchMetadata] = useState<SearchMetadata | null>(null);
  const [contextUsage, setContextUsage] = useState<ContextUsage | null>(null);
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null);
  const pendingSearchMetadataRef = useRef<SearchMetadata | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const { activeId, loadConversations, loadConversation } = useConversations();
  
  // Keep ref in sync with state
  useEffect(() => {
    pendingSearchMetadataRef.current = pendingSearchMetadata;
  }, [pendingSearchMetadata]);
  
  // Send pending message after summarization completes
  useEffect(() => {
    if (!isSummarizing && pendingUserMessage) {
      // Use a small delay to ensure state is settled
      const timer = setTimeout(() => {
        const messageToSend = pendingUserMessage;
        setPendingUserMessage(null);
        
        // Add user message
        const userMessage: Message = {
          role: 'user',
          content: messageToSend,
          timestamp: new Date().toISOString(),
          sources: [],
          metadata: {},
        };
        setMessages((prev) => [...prev, userMessage]);
        
        // Connect and send
        const ws = wsRef.current;
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({
            type: 'message',
            content: messageToSend,
            conversation_id: activeId,
          }));
          setIsGenerating(true);
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isSummarizing, pendingUserMessage, activeId]);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return wsRef.current;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data: WSMessageOut = JSON.parse(event.data);
        
        switch (data.type) {
          case 'token':
            // Direct update - server already throttles at 300ms intervals
            setStreamingContent(prev => prev + (data.content || ''));
            break;
          
          case 'search_info':
            // Store search metadata to attach to the upcoming message
            if (data.query && data.results) {
              setPendingSearchMetadata({
                query: data.query,
                results: data.results,
              });
            }
            break;
            
          case 'complete':
            if (data.message) {
              // Attach pending search metadata to the message (use ref for current value)
              const messageWithSearch: Message = {
                ...data.message,
                searchMetadata: pendingSearchMetadataRef.current || undefined,
              };
              setMessages((prev) => [...prev, messageWithSearch]);
              setPendingSearchMetadata(null);
            }
            setStreamingContent('');
            setIsGenerating(false);
            // Refresh conversation list to update titles
            loadConversations();
            // If a new conversation was created, load it to set it as active
            if (data.conversation_id && data.conversation_id !== activeId) {
              loadConversation(data.conversation_id);
            }
            break;
            
          case 'error':
            setError(data.content || 'Unknown error');
            setStreamingContent('');
            setIsGenerating(false);
            setPendingSearchMetadata(null);
            break;
            
          case 'status':
            setIsGenerating(data.generating ?? false);
            break;
          
          case 'summarizing':
            setIsSummarizing(true);
            break;
          
          case 'summary_complete':
            setIsSummarizing(false);
            // Update context usage if provided
            if (data.context_usage) {
              setContextUsage(data.context_usage);
            }
            break;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('Connection error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      wsRef.current = null;
    };

    wsRef.current = ws;
    return ws;
  }, [loadConversations, loadConversation, activeId]);

  const sendMessage = useCallback((content: string) => {
    if (!content.trim() || isGenerating) return;
    
    // If summarizing, queue the message
    if (isSummarizing) {
      setPendingUserMessage(content.trim());
      return;
    }

    setError(null);
    
    // Add user message immediately
    const userMessage: Message = {
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
      sources: [],
      metadata: {},
    };
    setMessages((prev) => [...prev, userMessage]);
    
    // Connect and send
    const ws = connectWebSocket();
    
    const sendWhenReady = () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'message',
          content: content.trim(),
          conversation_id: activeId,
        }));
        setIsGenerating(true);
      } else if (ws.readyState === WebSocket.CONNECTING) {
        setTimeout(sendWhenReady, 100);
      } else {
        setError('Failed to connect');
      }
    };
    
    sendWhenReady();
  }, [isGenerating, isSummarizing, connectWebSocket, activeId]);

  const cancelGeneration = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'cancel' }));
    }
    setIsGenerating(false);
    setStreamingContent('');
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setStreamingContent('');
    setError(null);
  }, []);

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        streamingContent,
        isGenerating,
        isSummarizing,
        error,
        pendingSearchMetadata,
        contextUsage,
        sendMessage,
        cancelGeneration,
        clearMessages,
        addMessage,
        setMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
