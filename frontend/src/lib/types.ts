// Chat mode options
export type ChatMode = 'chat' | 'rag' | 'search';

// Source reference for RAG or web search
export interface Source {
  title: string;
  content: string;
  url?: string;
  page?: number;
}

// Chat message
export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  sources: Source[];
  metadata: Record<string, unknown>;
}

// Conversation summary for listing
export interface ConversationSummary {
  id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

// Full conversation detail
export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  system_prompt: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
}

// Context window info
export interface ContextWindow {
  conversation_id: string;
  mode: ChatMode;
  system_prompt: string;
  messages: { role: string; content: string }[];
  message_count: number;
  estimated_tokens: number;
  context_length: number;
  usage_percent: number;
  sources: Array<{ title: string; content: string; url?: string; page?: number }>;
}

// Document info
export interface DocumentInfo {
  id: string;
  filename: string;
  file_path: string;
  chunk_count: number;
  indexed_at: string;
}

// Settings
export interface Settings {
  mode: ChatMode;
  model_path: string | null;
  context_length: number;
  max_tokens: number;
  temperature: number;
  top_p: number;
  top_k: number;
  repeat_penalty: number;
  gpu_layers: number;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  top_k_results: number;
  search_enabled: boolean;
  max_search_results: number;
  theme: string;
}

// Model info
export interface ModelInfo {
  filename: string;
  path: string;
  size_mb: number;
}

// Model status
export interface ModelStatus {
  loaded: boolean;
  model_path: string | null;
  generating: boolean;
  needs_download: boolean;
}

// Download status
export interface DownloadStatus {
  is_downloading: boolean;
  model_name: string;
  filename: string;
  bytes_downloaded: number;
  total_bytes: number;
  progress_percent: number;
  status: 'idle' | 'downloading' | 'completed' | 'error' | 'cancelled';
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

// Available model for download
export interface DownloadableModel {
  name: string;
  filename: string;
  size_mb: number;
  description: string;
  recommended: boolean;
}

// WebSocket message types
export interface WSMessageIn {
  type: 'message' | 'cancel';
  content?: string;
  conversation_id?: string;
}

export interface WSMessageOut {
  type: 'token' | 'complete' | 'error' | 'status';
  content?: string;
  message?: Message;
  sources?: Source[];
  generating?: boolean;
  conversation_id?: string;
}
