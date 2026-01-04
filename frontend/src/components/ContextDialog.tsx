import { useState, useEffect, useCallback, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  X,
  Save,
  RefreshCw,
  FileText,
  MessageSquare,
  Loader2,
  Cpu,
  Sparkles,
  AlertTriangle,
  Edit3,
  Eye,
  Check,
} from 'lucide-react';
import * as api from '../lib/api';

interface ContextDialogProps {
  open: boolean;
  onClose: () => void;
  conversationId: string | null;
  currentSystemPrompt: string;
  onSystemPromptUpdate: (newPrompt: string) => void;
}

interface ContextFileData {
  conversation_id: string;
  content: string;
  token_count: number;
  max_tokens: number;
  usage_percent: number;
  needs_summary: boolean;
}

export function ContextDialog({
  open,
  onClose,
  conversationId,
  currentSystemPrompt,
  onSystemPromptUpdate,
}: ContextDialogProps) {
  const [activeTab, setActiveTab] = useState<'prompt' | 'context'>('context');
  const [systemPrompt, setSystemPrompt] = useState(currentSystemPrompt);
  const [contextFile, setContextFile] = useState<ContextFileData | null>(null);
  const [editedContent, setEditedContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savingContext, setSavingContext] = useState(false);
  const [contextSaved, setContextSaved] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync system prompt when prop changes
  useEffect(() => {
    setSystemPrompt(currentSystemPrompt);
  }, [currentSystemPrompt]);

  // Auto-save context file with debounce
  const saveContextFile = useCallback(async (content: string) => {
    if (!conversationId) return;
    
    setSavingContext(true);
    setContextSaved(false);
    try {
      const result = await api.saveContextFile(conversationId, content);
      // Update usage metrics
      if (contextFile) {
        setContextFile({
          ...contextFile,
          content,
          token_count: result.token_count,
          usage_percent: result.usage_percent,
          needs_summary: result.needs_summary,
        });
      }
      setContextSaved(true);
      setTimeout(() => setContextSaved(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save context');
    } finally {
      setSavingContext(false);
    }
  }, [conversationId, contextFile]);

  // Debounced auto-save when content changes
  useEffect(() => {
    if (!isEditing || !conversationId) return;
    if (editedContent === contextFile?.content) return;
    
    // Clear previous timeout
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }
    
    // Set new timeout for auto-save (800ms debounce)
    saveTimeoutRef.current = setTimeout(() => {
      saveContextFile(editedContent);
    }, 800);
    
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [editedContent, isEditing, conversationId, contextFile?.content, saveContextFile]);

  // Load context file when tab changes or dialog opens
  const loadContextFile = useCallback(async () => {
    if (!conversationId) return;

    setLoading(true);
    setError(null);
    try {
      const data = await api.getContextFile(conversationId);
      setContextFile(data);
      setEditedContent(data.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load context');
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  useEffect(() => {
    if (open && activeTab === 'context' && conversationId) {
      loadContextFile();
    }
  }, [open, activeTab, conversationId, loadContextFile]);

  const handleSavePrompt = async () => {
    if (!conversationId) return;

    setSaving(true);
    setError(null);
    try {
      await api.updateSystemPrompt(conversationId, systemPrompt);
      onSystemPromptUpdate(systemPrompt);
      setSuccessMessage('System prompt saved');
      setTimeout(() => setSuccessMessage(null), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const handleSummarize = async () => {
    if (!conversationId) return;

    setSummarizing(true);
    setError(null);
    try {
      const result = await api.summarizeContext(conversationId, 4);
      // Reload context file to get updated content
      await loadContextFile();
      setSuccessMessage(`Context summarized! Now at ${result.usage_percent}% usage`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to summarize');
    } finally {
      setSummarizing(false);
    }
  };

  const getUsageColor = (percent: number) => {
    if (percent > 80) return 'bg-red-500';
    if (percent > 70) return 'bg-yellow-500';
    if (percent > 50) return 'bg-blue-500';
    return 'bg-green-500';
  };

  const getUsageTextColor = (percent: number) => {
    if (percent > 80) return 'text-red-400';
    if (percent > 70) return 'text-yellow-400';
    return 'text-zinc-400';
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
            onClick={() => setActiveTab('context')}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'context'
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            Context File
          </button>
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
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-hidden flex flex-col">
          {error && (
            <div className="mx-6 mt-4 rounded-lg bg-red-500/20 px-4 py-3 text-sm text-red-300 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </div>
          )}
          
          {successMessage && (
            <div className="mx-6 mt-4 rounded-lg bg-green-500/20 px-4 py-3 text-sm text-green-300">
              {successMessage}
            </div>
          )}

          {/* Context File Tab */}
          {activeTab === 'context' && (
            <div className="flex-1 flex flex-col overflow-hidden p-4">
              {loading && !contextFile ? (
                <div className="flex flex-1 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-400" />
                </div>
              ) : contextFile ? (
                <>
                  {/* Stats Bar */}
                  <div className="mb-4 flex items-center gap-4 rounded-lg bg-zinc-800 p-4">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-zinc-400">Context Usage</span>
                        <span className={`text-sm font-medium ${getUsageTextColor(contextFile.usage_percent)}`}>
                          {contextFile.token_count.toLocaleString()} / {contextFile.max_tokens.toLocaleString()} tokens
                        </span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-700">
                        <div
                          className={`h-full rounded-full transition-all ${getUsageColor(contextFile.usage_percent)}`}
                          style={{ width: `${Math.min(contextFile.usage_percent, 100)}%` }}
                        />
                      </div>
                      <div className="mt-1 flex items-center justify-between text-xs text-zinc-500">
                        <span>{contextFile.usage_percent}% used</span>
                        {contextFile.needs_summary && (
                          <span className="flex items-center gap-1 text-yellow-400">
                            <AlertTriangle className="h-3 w-3" />
                            Summarization recommended
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setIsEditing(!isEditing)}
                        className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                          isEditing
                            ? 'bg-blue-600 text-white'
                            : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
                        }`}
                      >
                        {isEditing ? <Eye className="h-4 w-4" /> : <Edit3 className="h-4 w-4" />}
                        {isEditing ? 'Preview' : 'Edit'}
                      </button>
                      <button
                        onClick={loadContextFile}
                        disabled={loading}
                        className="flex items-center gap-2 rounded-lg bg-zinc-700 px-3 py-2 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-600"
                      >
                        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                      </button>
                      <button
                        onClick={handleSummarize}
                        disabled={summarizing || !contextFile?.content?.trim()}
                        className="flex items-center gap-2 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {summarizing ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Sparkles className="h-4 w-4" />
                        )}
                        Summarize
                      </button>
                    </div>
                  </div>

                  {/* Context Content */}
                  <div className="flex-1 overflow-hidden rounded-lg border border-zinc-700 bg-zinc-800">
                    {isEditing ? (
                      <textarea
                        value={editedContent}
                        onChange={(e) => setEditedContent(e.target.value)}
                        className="h-full w-full resize-none bg-transparent p-4 font-mono text-sm text-zinc-200 focus:outline-none"
                        placeholder="Context content..."
                      />
                    ) : (
                      <div className="h-full overflow-y-auto p-4">
                        <MarkdownPreview content={contextFile.content} />
                      </div>
                    )}
                  </div>

                  {/* Footer */}
                  <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
                    <span>
                      This is the context sent to the LLM for each response.
                      {contextFile.needs_summary && ' Click Summarize to compress older messages.'}
                    </span>
                    {isEditing && (
                      <span className="flex items-center gap-1.5">
                        {savingContext ? (
                          <>
                            <Loader2 className="h-3 w-3 animate-spin text-blue-400" />
                            <span className="text-blue-400">Saving...</span>
                          </>
                        ) : contextSaved ? (
                          <>
                            <Check className="h-3 w-3 text-green-400" />
                            <span className="text-green-400">Saved</span>
                          </>
                        ) : editedContent !== contextFile.content ? (
                          <span className="text-yellow-400">Unsaved changes</span>
                        ) : null}
                      </span>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex flex-1 flex-col items-center justify-center text-zinc-500">
                  <MessageSquare className="h-12 w-12 mb-3 opacity-50" />
                  <p>No context available</p>
                  <p className="text-sm mt-1">Start a conversation to see context here</p>
                </div>
              )}
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
                  This prompt sets the AI's behavior and personality. It's included at the start of every context.
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
        </div>
      </div>
    </div>
  );
}

// Markdown preview component using react-markdown
function MarkdownPreview({ content }: { content: string }) {
  return (
    <ReactMarkdown
      components={{
        h1: ({ children }) => <h1 className="text-lg font-bold text-blue-400 mt-4 mb-2 first:mt-0">{children}</h1>,
        h2: ({ children }) => {
          const text = String(children).toLowerCase();
          const isUser = text === 'user';
          const isAssistant = text === 'assistant';
          const isSummary = text.includes('summary');
          
          return (
            <div
              className={`inline-block mt-4 mb-2 first:mt-0 px-2 py-1 rounded text-xs font-semibold ${
                isUser
                  ? 'bg-blue-500/20 text-blue-300'
                  : isAssistant
                  ? 'bg-green-500/20 text-green-300'
                  : isSummary
                  ? 'bg-purple-500/20 text-purple-300'
                  : 'bg-zinc-700 text-zinc-300'
              }`}
            >
              {children}
            </div>
          );
        },
        h3: ({ children }) => <h3 className="text-sm font-bold text-indigo-400 mt-3 mb-2">{children}</h3>,
        h4: ({ children }) => <h4 className="text-sm font-semibold text-violet-400 mt-2 mb-1">{children}</h4>,
        p: ({ children }) => <p className="text-zinc-300 text-sm leading-relaxed">{children}</p>,
        strong: ({ children }) => <strong className="font-bold text-yellow-300">{children}</strong>,
        em: ({ children }) => <em className="italic text-cyan-300">{children}</em>,
        code: ({ inline, children }: any) => {
          if (inline) {
            return (
              <code className="bg-zinc-700 px-1.5 py-0.5 rounded text-orange-300 font-mono text-xs whitespace-nowrap">
                {children}
              </code>
            );
          }
          return <code className="font-mono">{children}</code>;
        },
        pre: ({ children }: any) => (
          <pre className="bg-zinc-700 rounded p-3 overflow-x-auto text-sm text-zinc-200 mt-2 mb-2">
            {children}
          </pre>
        ),
        hr: () => <hr className="my-4 border-zinc-700" />,
        ul: ({ children }) => <ul className="list-disc list-inside ml-2 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside ml-2 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="text-zinc-300 text-sm">{children}</li>,
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline">
            {children}
          </a>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
