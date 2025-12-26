import type {
  ConversationSummary,
  Conversation,
  DocumentInfo,
  Settings,
  ModelInfo,
  ModelStatus,
  ChatMode,
  DownloadStatus,
  DownloadableModel,
} from './types';

const API_BASE = '/api';

// Helper for fetch with error handling
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============== Health ==============

export async function checkHealth(): Promise<{ status: string }> {
  return fetchAPI('/health');
}

export async function getModelStatus(): Promise<ModelStatus> {
  return fetchAPI('/model/status');
}

// ============== Conversations ==============

export async function listConversations(): Promise<ConversationSummary[]> {
  return fetchAPI('/conversations');
}

export async function getConversation(id: string): Promise<Conversation> {
  return fetchAPI(`/conversations/${id}`);
}

export async function createConversation(
  title?: string,
  systemPrompt?: string
): Promise<Conversation> {
  return fetchAPI('/conversations', {
    method: 'POST',
    body: JSON.stringify({
      title: title || 'New Conversation',
      system_prompt: systemPrompt || 'You are a helpful AI assistant.',
    }),
  });
}

export async function deleteConversation(id: string): Promise<void> {
  await fetchAPI(`/conversations/${id}`, { method: 'DELETE' });
}

// ============== Documents ==============

export async function listDocuments(): Promise<DocumentInfo[]> {
  return fetchAPI('/documents');
}

export async function uploadDocument(file: File): Promise<{
  success: boolean;
  filename: string;
  chunk_count: number;
  message: string;
}> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/documents`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail);
  }

  return response.json();
}

export async function deleteDocument(id: string): Promise<void> {
  await fetchAPI(`/documents/${id}`, { method: 'DELETE' });
}

// ============== Settings ==============

export async function getSettings(): Promise<Settings> {
  return fetchAPI('/settings');
}

export async function updateSettings(
  settings: Partial<Settings>
): Promise<Settings> {
  return fetchAPI('/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

export async function setMode(mode: ChatMode): Promise<Settings> {
  return fetchAPI('/settings/mode', {
    method: 'PUT',
    body: JSON.stringify({ mode }),
  });
}

export async function listModels(): Promise<{ models: ModelInfo[] }> {
  return fetchAPI('/settings/models');
}

// ============== Model Download ==============

export async function getDownloadStatus(): Promise<DownloadStatus> {
  return fetchAPI('/settings/download/status');
}

export async function getDownloadableModels(): Promise<{ models: DownloadableModel[] }> {
  return fetchAPI('/settings/download/models');
}

export async function startModelDownload(filename?: string): Promise<{
  status: string;
  model_name?: string;
  filename?: string;
  size_mb?: number;
  message: string;
  model_path?: string;
}> {
  const url = filename
    ? `/settings/download/start?filename=${encodeURIComponent(filename)}`
    : '/settings/download/start';
  return fetchAPI(url, { method: 'POST' });
}

export async function cancelModelDownload(): Promise<{ status: string; message: string }> {
  return fetchAPI('/settings/download/cancel', { method: 'POST' });
}

export async function reloadServices(): Promise<{
  success: boolean;
  status: Record<string, boolean | string[]>;
  model_loaded: boolean;
  chat_ready: boolean;
  model_path: string;
}> {
  return fetchAPI('/settings/reload', { method: 'POST' });
}
