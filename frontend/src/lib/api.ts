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
  ContextWindow,
} from './types';
import { DEFAULT_SYSTEM_PROMPT } from './constants';

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
      system_prompt: systemPrompt || DEFAULT_SYSTEM_PROMPT,
    }),
  });
}

export async function deleteConversation(id: string): Promise<void> {
  await fetchAPI(`/conversations/${id}`, { method: 'DELETE' });
}

export async function renameConversation(
  id: string,
  title: string
): Promise<{ success: boolean; title: string; message: string }> {
  return fetchAPI(`/conversations/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ title }),
  });
}

export async function deleteAllConversations(): Promise<{
  success: boolean;
  deleted_count: number;
  message: string;
}> {
  return fetchAPI('/conversations/all', { method: 'DELETE' });
}

export async function updateSystemPrompt(
  id: string,
  systemPrompt: string
): Promise<{ success: boolean; system_prompt: string; message: string }> {
  return fetchAPI(`/conversations/${id}/system-prompt`, {
    method: 'PUT',
    body: JSON.stringify({ system_prompt: systemPrompt }),
  });
}

export async function getContextWindow(
  id: string,
  query?: string
): Promise<ContextWindow> {
  const url = query
    ? `/conversations/${id}/context?query=${encodeURIComponent(query)}`
    : `/conversations/${id}/context`;
  return fetchAPI(url);
}

export async function getContextFile(id: string): Promise<{
  conversation_id: string;
  content: string;
  token_count: number;
  max_tokens: number;
  usage_percent: number;
  needs_summary: boolean;
}> {
  return fetchAPI(`/conversations/${id}/context-file`);
}

export async function saveContextFile(
  id: string,
  content: string
): Promise<{
  success: boolean;
  token_count: number;
  usage_percent: number;
  needs_summary: boolean;
}> {
  return fetchAPI(`/conversations/${id}/context-file`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  });
}

export async function summarizeContext(
  id: string,
  keepRecentMessages?: number
): Promise<{
  success: boolean;
  summary: string;
  token_count: number;
  usage_percent: number;
  needs_summary: boolean;
  message: string;
}> {
  return fetchAPI(`/conversations/${id}/summarize-context`, {
    method: 'POST',
    body: JSON.stringify({ keep_recent_messages: keepRecentMessages || 4 }),
  });
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

export async function canQuit(): Promise<{ can_quit: boolean }> {
  return fetchAPI('/settings/app/can-quit');
}

export async function quitApp(): Promise<{ stopping: boolean }> {
  return fetchAPI('/settings/app/quit', { method: 'POST' });
}

export async function switchModel(modelPath: string): Promise<{
  success: boolean;
  model_path: string;
  model_name: string;
  loaded: boolean;
  message: string;
}> {
  return fetchAPI(`/settings/models/switch?model_path=${encodeURIComponent(modelPath)}`, {
    method: 'POST',
  });
}
