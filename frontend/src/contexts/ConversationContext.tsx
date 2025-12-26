import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import type { ConversationSummary, Conversation } from '../lib/types';
import * as api from '../lib/api';

interface ConversationContextType {
  conversations: ConversationSummary[];
  activeConversation: Conversation | null;
  activeId: string | null;
  loading: boolean;
  error: string | null;
  loadConversations: () => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  createConversation: () => Promise<Conversation>;
  deleteConversation: (id: string) => Promise<void>;
  setActiveConversation: (conversation: Conversation | null) => void;
  clearActiveConversation: () => void;
}

const ConversationContext = createContext<ConversationContextType | null>(null);

export function ConversationProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listConversations();
      setConversations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const loadConversation = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getConversation(id);
      setActiveConversation(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversation');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createConversation = useCallback(async () => {
    try {
      const newConv = await api.createConversation();
      setActiveConversation(newConv);
      await loadConversations();
      return newConv;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create conversation');
      throw err;
    }
  }, [loadConversations]);

  const deleteConversation = useCallback(async (id: string) => {
    try {
      await api.deleteConversation(id);
      if (activeConversation?.id === id) {
        setActiveConversation(null);
      }
      await loadConversations();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete conversation');
      throw err;
    }
  }, [activeConversation?.id, loadConversations]);

  const clearActiveConversation = useCallback(() => {
    setActiveConversation(null);
  }, []);

  const activeId = activeConversation?.id ?? null;

  return (
    <ConversationContext.Provider
      value={{
        conversations,
        activeConversation,
        activeId,
        loading,
        error,
        loadConversations,
        loadConversation,
        createConversation,
        deleteConversation,
        setActiveConversation,
        clearActiveConversation,
      }}
    >
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversations() {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error('useConversations must be used within a ConversationProvider');
  }
  return context;
}
