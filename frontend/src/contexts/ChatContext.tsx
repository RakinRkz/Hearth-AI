import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from 'react';
import type { Message, WSMessageOut } from '../lib/types';
import { useConversations } from './ConversationContext';

interface ChatContextType {
  messages: Message[];
  streamingContent: string;
  isGenerating: boolean;
  error: string | null;
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
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const { activeId, loadConversations } = useConversations();

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
            setStreamingContent((prev) => prev + (data.content || ''));
            break;
            
          case 'complete':
            if (data.message) {
              setMessages((prev) => [...prev, data.message!]);
            }
            setStreamingContent('');
            setIsGenerating(false);
            // Refresh conversation list to update titles
            loadConversations();
            break;
            
          case 'error':
            setError(data.content || 'Unknown error');
            setStreamingContent('');
            setIsGenerating(false);
            break;
            
          case 'status':
            setIsGenerating(data.generating ?? false);
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
  }, [loadConversations]);

  const sendMessage = useCallback((content: string) => {
    if (!content.trim() || isGenerating) return;

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
  }, [isGenerating, connectWebSocket, activeId]);

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
        error,
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
