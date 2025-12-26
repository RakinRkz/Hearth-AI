import type {
  ConversationSummary,
  Conversation,
  DocumentInfo,
  Settings,
  ModelInfo,
  ModelStatus,
  ChatMode,
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
