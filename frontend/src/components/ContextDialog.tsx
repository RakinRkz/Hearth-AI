import { useState, useEffect, useCallback } from 'react';
import {
  X,
  Save,
  RefreshCw,
  FileText,
  MessageSquare,
  Loader2,
  ChevronDown,
  ChevronRight,
  Cpu,
  Edit3,
  Trash2,
} from 'lucide-react';
import * as api from '../lib/api';
import type { ContextWindow } from '../lib/types';

interface ContextDialogProps {
  open: boolean;
  onClose: () => void;
  conversationId: string | null;
  currentSystemPrompt: string;
  onSystemPromptUpdate: (newPrompt: string) => void;
}

export function ContextDialog({
  open,
  onClose,
  conversationId,
  currentSystemPrompt,
  onSystemPromptUpdate,
}: ContextDialogProps) {
  const [activeTab, setActiveTab] = useState<'prompt' | 'context'>('prompt');
  const [systemPrompt, setSystemPrompt] = useState(currentSystemPrompt);
  const [contextData, setContextData] = useState<ContextWindow | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedMessages, setExpandedMessages] = useState<Set<number>>(new Set());
  const [testQuery, setTestQuery] = useState('');
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editContent, setEditContent] = useState('');

  // Sync system prompt when prop changes
  useEffect(() => {
    setSystemPrompt(currentSystemPrompt);
  }, [currentSystemPrompt]);

  // Load context when tab changes to context or dialog opens
  const loadContext = useCallback(async (query?: string) => {
    if (!conversationId) return;

    setLoading(true);
    setError(null);
    try {
      const data = await api.getContextWindow(conversationId, query);
      setContextData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load context');
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  useEffect(() => {
    if (open && activeTab === 'context' && conversationId) {
      loadContext();
    }
  }, [open, activeTab, conversationId, loadContext]);

  const handleSavePrompt = async () => {
    if (!conversationId) return;

    setSaving(true);
    setError(null);
    try {
      await api.updateSystemPrompt(conversationId, systemPrompt);
      onSystemPromptUpdate(systemPrompt);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const toggleMessageExpand = (index: number) => {
    setExpandedMessages((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const handleTestQuery = () => {
    loadContext(testQuery);
  };

  const startEditing = (index: number, content: string) => {
    setEditingIndex(index);
    setEditContent(content);
    setExpandedMessages((prev) => new Set(prev).add(index));
  };

  const cancelEditing = () => {
    setEditingIndex(null);
    setEditContent('');
  };

  const saveEdit = (index: number) => {
    if (contextData) {
      const updatedMessages = [...contextData.messages];
      updatedMessages[index] = { ...updatedMessages[index], content: editContent };
      setContextData({ ...contextData, messages: updatedMessages });
    }
    setEditingIndex(null);
    setEditContent('');
  };

  const deleteMessage = (index: number) => {
    if (contextData) {
      const updatedMessages = contextData.messages.filter((_, i) => i !== index);
      setContextData({
        ...contextData,
        messages: updatedMessages,
        message_count: updatedMessages.length,
        estimated_tokens: updatedMessages.reduce((sum, m) => sum + Math.ceil(m.content.length / 4), 0),
      });
    }
  };

  const addMessage = (role: 'system' | 'user' | 'assistant') => {
    if (contextData) {
      const newMessage = { role, content: '' };
      const updatedMessages = [...contextData.messages, newMessage];
      setContextData({
        ...contextData,
        messages: updatedMessages,
        message_count: updatedMessages.length,
      });
      // Start editing the new message
      startEditing(updatedMessages.length - 1, '');
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="mx-4 flex h-[85vh] w-full max-w-4xl flex-col rounded-xl bg-zinc-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
          <div className="flex items-center gap-3">
            <Cpu className="h-5 w-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">Context Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-zinc-800">
          <button
            onClick={() => setActiveTab('prompt')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'prompt'
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <FileText className="h-4 w-4" />
            System Prompt
          </button>
          <button
            onClick={() => setActiveTab('context')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'context'
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            Context Window
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {error && (
            <div className="mx-6 mt-4 rounded-lg bg-red-500/20 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          {/* System Prompt Tab */}
          {activeTab === 'prompt' && (
            <div className="flex h-full flex-col p-6">
              <div className="mb-4">
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  System Prompt
                </label>
                <p className="mb-3 text-xs text-zinc-500">
                  This prompt sets the AI's behavior and personality. It's sent at the start of every conversation.
                </p>
              </div>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="flex-1 resize-none rounded-lg border border-zinc-700 bg-zinc-800 p-4 font-mono text-sm text-zinc-200 placeholder-zinc-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="You are a helpful AI assistant..."
              />
              <div className="mt-4 flex items-center justify-between">
                <span className="text-xs text-zinc-500">
                  {systemPrompt.length} characters (~{Math.ceil(systemPrompt.length / 4)} tokens)
                </span>
                <button
                  onClick={handleSavePrompt}
                  disabled={saving || systemPrompt === currentSystemPrompt}
                  className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {saving ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  Save Changes
                </button>
              </div>
            </div>
          )}

          {/* Context Window Tab */}
          {activeTab === 'context' && (
            <div className="flex h-full flex-col overflow-hidden">
              {/* Test Query Input */}
              <div className="border-b border-zinc-800 p-4">
                <label className="mb-2 block text-sm font-medium text-zinc-300">
                  Test Query (for RAG/Search preview)
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={testQuery}
                    onChange={(e) => setTestQuery(e.target.value)}
                    placeholder="Enter a test query to see how context would be generated..."
                    className="flex-1 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm text-zinc-200 placeholder-zinc-500 focus:border-blue-500 focus:outline-none"
                  />
                  <button
                    onClick={handleTestQuery}
                    disabled={loading}
                    className="flex items-center gap-2 rounded-lg bg-zinc-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-600"
                  >
                    <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    Test
                  </button>
                </div>
              </div>

              {/* Context Info */}
              {loading && !contextData ? (
                <div className="flex flex-1 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-400" />
                </div>
              ) : contextData ? (
                <div className="flex-1 overflow-y-auto p-4">
                  {/* Stats Bar */}
                  <div className="mb-4 grid grid-cols-4 gap-3">
                    <div className="rounded-lg bg-zinc-800 p-3">
                      <div className="text-xs text-zinc-500">Mode</div>
                      <div className="mt-1 text-sm font-medium text-zinc-200 capitalize">
                        {contextData.mode}
                      </div>
                    </div>
                    <div className="rounded-lg bg-zinc-800 p-3">
                      <div className="text-xs text-zinc-500">Messages</div>
                      <div className="mt-1 text-sm font-medium text-zinc-200">
                        {contextData.message_count}
                      </div>
                    </div>
                    <div className="rounded-lg bg-zinc-800 p-3">
                      <div className="text-xs text-zinc-500">Est. Tokens</div>
                      <div className="mt-1 text-sm font-medium text-zinc-200">
                        {contextData.estimated_tokens.toLocaleString()}
                      </div>
                    </div>
                    <div className="rounded-lg bg-zinc-800 p-3">
                      <div className="text-xs text-zinc-500">Context Usage</div>
                      <div className="mt-1 flex items-center gap-2">
                        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-700">
                          <div
                            className={`h-full rounded-full transition-all ${
                              contextData.usage_percent > 80
                                ? 'bg-red-500'
                                : contextData.usage_percent > 50
                                ? 'bg-yellow-500'
                                : 'bg-green-500'
                            }`}
                            style={{ width: `${Math.min(contextData.usage_percent, 100)}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-zinc-200">
                          {contextData.usage_percent}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Messages Preview */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-zinc-300">Context Messages</h4>
                      <div className="flex gap-1">
                        <button
                          onClick={() => addMessage('system')}
                          className="rounded px-2 py-1 text-xs bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 transition-colors"
                        >
                          + System
                        </button>
                        <button
                          onClick={() => addMessage('user')}
                          className="rounded px-2 py-1 text-xs bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 transition-colors"
                        >
                          + User
                        </button>
                        <button
                          onClick={() => addMessage('assistant')}
                          className="rounded px-2 py-1 text-xs bg-green-500/20 text-green-300 hover:bg-green-500/30 transition-colors"
                        >
                          + Assistant
                        </button>
                      </div>
                    </div>
                    {contextData.messages.map((msg, i) => (
                      <div
                        key={i}
                        className="overflow-hidden rounded-lg border border-zinc-700 bg-zinc-800"
                      >
                        <div className="flex w-full items-center gap-2 px-3 py-2 hover:bg-zinc-750">
                          <button onClick={() => toggleMessageExpand(i)} className="flex items-center gap-2 flex-1 text-left">
                            {expandedMessages.has(i) ? (
                              <ChevronDown className="h-4 w-4 text-zinc-500" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-zinc-500" />
                            )}
                            <span
                              className={`rounded px-2 py-0.5 text-xs font-medium ${
                                msg.role === 'system'
                                  ? 'bg-purple-500/20 text-purple-300'
                                  : msg.role === 'user'
                                  ? 'bg-blue-500/20 text-blue-300'
                                  : 'bg-green-500/20 text-green-300'
                              }`}
                            >
                              {msg.role}
                            </span>
                            <span className="flex-1 truncate text-sm text-zinc-400">
                              {msg.content.slice(0, 100)}
                              {msg.content.length > 100 ? '...' : ''}
                            </span>
                            <span className="text-xs text-zinc-500">
                              ~{Math.ceil(msg.content.length / 4)} tokens
                            </span>
                          </button>
                          <button
                            onClick={() => startEditing(i, msg.content)}
                            className="p-1.5 rounded hover:bg-zinc-700 text-zinc-400 hover:text-blue-400 transition-colors"
                            title="Edit message"
                          >
                            <Edit3 className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => deleteMessage(i)}
                            className="p-1.5 rounded hover:bg-zinc-700 text-zinc-400 hover:text-red-400 transition-colors"
                            title="Delete message"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                        {expandedMessages.has(i) && (
                          <div className="border-t border-zinc-700 bg-zinc-850 p-3">
                            {editingIndex === i ? (
                              <div className="space-y-2">
                                <textarea
                                  value={editContent}
                                  onChange={(e) => setEditContent(e.target.value)}
                                  className="w-full h-32 resize-none rounded-lg border border-zinc-600 bg-zinc-900 p-3 font-mono text-xs text-zinc-200 focus:border-blue-500 focus:outline-none"
                                  autoFocus
                                />
                                <div className="flex gap-2 justify-end">
                                  <button
                                    onClick={cancelEditing}
                                    className="px-3 py-1.5 rounded text-xs text-zinc-400 hover:bg-zinc-700 transition-colors"
                                  >
                                    Cancel
                                  </button>
                                  <button
                                    onClick={() => saveEdit(i)}
                                    className="px-3 py-1.5 rounded text-xs bg-blue-600 text-white hover:bg-blue-500 transition-colors"
                                  >
                                    Save
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <pre className="whitespace-pre-wrap font-mono text-xs text-zinc-300">
                                {msg.content}
                              </pre>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Sources (if any) */}
                  {contextData.sources.length > 0 && (
                    <div className="mt-4">
                      <h4 className="mb-2 text-sm font-medium text-zinc-300">
                        Sources ({contextData.sources.length})
                      </h4>
                      <div className="space-y-2">
                        {contextData.sources.map((source, i) => (
                          <div
                            key={i}
                            className="rounded-lg border border-zinc-700 bg-zinc-800 p-3"
                          >
                            <div className="text-sm font-medium text-zinc-200">
                              [{i + 1}] {source.title}
                            </div>
                            <p className="mt-1 text-xs text-zinc-400 line-clamp-2">
                              {source.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-1 items-center justify-center text-zinc-500">
                  No context data available
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
