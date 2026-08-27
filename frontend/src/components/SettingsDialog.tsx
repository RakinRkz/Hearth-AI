import { useState, useEffect, useCallback } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import { useConversations } from '../contexts/ConversationContext';
import { useChat } from '../contexts/ChatContext';
import { cn } from '../lib/utils';
import {
  X,
  Cpu,
  Sliders,
  Info,
  Download,
  Check,
  Loader2,
  HardDrive,
  Zap,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Shield,
  Trash2,
  MessageSquare,
  AlertTriangle,
} from 'lucide-react';
import * as api from '../lib/api';
import type { ModelInfo, DownloadStatus, DownloadableModel } from '../lib/types';

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsDialog({ open, onClose }: SettingsDialogProps) {
  const { settings, updateSettings, refreshSettings } = useSettings();
  const { conversations, loadConversations, clearActiveConversation } = useConversations();
  const { clearMessages } = useChat();
  const [localModels, setLocalModels] = useState<ModelInfo[]>([]);
  const [downloadableModels, setDownloadableModels] = useState<DownloadableModel[]>([]);
  const [downloadStatus, setDownloadStatus] = useState<DownloadStatus | null>(null);
  const [activeTab, setActiveTab] = useState<'model' | 'generation' | 'data' | 'about'>('model');
  const [switching, setSwitching] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load models and download status
  const loadData = useCallback(async () => {
    try {
      const [modelsRes, downloadModelsRes, statusRes] = await Promise.all([
        api.listModels(),
        api.getDownloadableModels(),
        api.getDownloadStatus(),
      ]);
      setLocalModels(modelsRes.models);
      setDownloadableModels(downloadModelsRes.models);
      setDownloadStatus(statusRes);
    } catch (err) {
      console.error('Failed to load models:', err);
    }
  }, []);

  useEffect(() => {
    if (open) {
      loadData();
    }
  }, [open, loadData]);

  // Poll download status while downloading
  useEffect(() => {
    if (!open || !downloadStatus?.is_downloading) return;

    const interval = setInterval(async () => {
      try {
        const status = await api.getDownloadStatus();
        setDownloadStatus(status);
        
        if (status.status === 'completed') {
          await loadData();
          await refreshSettings();
        }
      } catch (err) {
        console.error('Failed to get download status:', err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [open, downloadStatus?.is_downloading, loadData, refreshSettings]);

  if (!open || !settings) return null;

  const handleSwitchModel = async (modelPath: string) => {
    setSwitching(modelPath);
    setError(null);
    try {
      await api.switchModel(modelPath);
      await refreshSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch model');
    } finally {
      setSwitching(null);
    }
  };

  const handleStartDownload = async (filename: string) => {
    setError(null);
    try {
      await api.startModelDownload(filename);
      const status = await api.getDownloadStatus();
      setDownloadStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start download');
    }
  };

  const handleCancelDownload = async () => {
    try {
      await api.cancelModelDownload();
      const status = await api.getDownloadStatus();
      setDownloadStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel download');
    }
  };

  const handleTemperatureChange = (value: number) => {
    updateSettings({ temperature: value });
  };

  const handleMaxTokensChange = (value: number) => {
    updateSettings({ max_tokens: value });
  };

  const handleGpuLayersChange = (value: number) => {
    updateSettings({ gpu_layers: value });
  };

  const handleContextLengthChange = (value: number) => {
    updateSettings({ context_length: value });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Dialog */}
      <div className="relative z-10 flex h-[85vh] w-full max-w-3xl flex-col rounded-xl border border-zinc-700 bg-zinc-900 shadow-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-700 px-6 py-4">
          <h2 className="text-lg font-semibold text-white">Settings</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-zinc-700">
          <TabButton
            active={activeTab === 'model'}
            onClick={() => setActiveTab('model')}
            icon={<Cpu className="h-4 w-4" />}
            label="Models"
          />
          <TabButton
            active={activeTab === 'generation'}
            onClick={() => setActiveTab('generation')}
            icon={<Sliders className="h-4 w-4" />}
            label="Generation"
          />
          <TabButton
            active={activeTab === 'data'}
            onClick={() => setActiveTab('data')}
            icon={<Shield className="h-4 w-4" />}
            label="Data"
          />
          <TabButton
            active={activeTab === 'about'}
            onClick={() => setActiveTab('about')}
            icon={<Info className="h-4 w-4" />}
            label="About"
          />
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mx-4 mt-4 flex items-center gap-2 rounded-lg bg-red-500/20 px-4 py-3 text-sm text-red-300">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            {error}
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-300">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'model' && (
            <ModelSettings
              localModels={localModels}
              downloadableModels={downloadableModels}
              downloadStatus={downloadStatus}
              currentModel={settings.model_path}
              switching={switching}
              onSwitchModel={handleSwitchModel}
              onStartDownload={handleStartDownload}
              onCancelDownload={handleCancelDownload}
              onRefresh={loadData}
            />
          )}
          {activeTab === 'generation' && (
            <GenerationSettings
              temperature={settings.temperature}
              maxTokens={settings.max_tokens}
              gpuLayers={settings.gpu_layers}
              contextLength={settings.context_length}
              onTemperatureChange={handleTemperatureChange}
              onMaxTokensChange={handleMaxTokensChange}
              onGpuLayersChange={handleGpuLayersChange}
              onContextLengthChange={handleContextLengthChange}
            />
          )}
          {activeTab === 'data' && (
            <PersonalDataSettings
              conversationCount={conversations.length}
              onDeleteAllConversations={async () => {
                try {
                  await api.deleteAllConversations();
                  clearMessages();
                  clearActiveConversation();
                  await loadConversations();
                } catch (err) {
                  setError(err instanceof Error ? err.message : 'Failed to delete conversations');
                }
              }}
            />
          )}
          {activeTab === 'about' && <AboutSettings />}
        </div>
      </div>
    </div>
  );
}

interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}

function TabButton({ active, onClick, icon, label }: TabButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex flex-1 items-center justify-center gap-2 px-4 py-3',
        'text-sm font-medium transition-colors',
        active
          ? 'border-b-2 border-blue-500 text-blue-400'
          : 'text-zinc-400 hover:text-white'
      )}
    >
      {icon}
      {label}
    </button>
  );
}

interface ModelSettingsProps {
  localModels: ModelInfo[];
  downloadableModels: DownloadableModel[];
  downloadStatus: DownloadStatus | null;
  currentModel: string | null;
  switching: string | null;
  onSwitchModel: (path: string) => void;
  onStartDownload: (filename: string) => void;
  onCancelDownload: () => void;
  onRefresh: () => void;
}

function ModelSettings({
  localModels,
  downloadableModels,
  downloadStatus,
  currentModel,
  switching,
  onSwitchModel,
  onStartDownload,
  onCancelDownload,
  onRefresh,
}: ModelSettingsProps) {
  const [showDownloadable, setShowDownloadable] = useState(false);
  const isDownloading = downloadStatus?.is_downloading || downloadStatus?.status === 'downloading';

  // Check which downloadable models are already installed
  const installedFilenames = new Set(localModels.map((m) => m.filename));

  return (
    <div className="space-y-6">
      {/* Current Model */}
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/20">
            <Zap className="h-5 w-5 text-green-400" />
          </div>
          <div className="flex-1">
            <div className="text-sm text-zinc-400">Active Model</div>
            <div className="font-medium text-white">
              {currentModel ? currentModel.split('/').pop() : 'No model loaded'}
            </div>
          </div>
          <button
            onClick={onRefresh}
            className="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-700 hover:text-white"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Download Progress */}
      {isDownloading && downloadStatus && (
        <div className="rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
              <span className="text-sm font-medium text-blue-300">
                Downloading {downloadStatus.model_name}
              </span>
            </div>
            <button
              onClick={onCancelDownload}
              className="rounded px-2 py-1 text-xs text-red-400 hover:bg-red-500/20"
            >
              Cancel
            </button>
          </div>
          <div className="mb-2 h-2 overflow-hidden rounded-full bg-zinc-700">
            <div
              className="h-full rounded-full bg-blue-500 transition-all"
              style={{ width: `${downloadStatus.progress_percent}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-zinc-400">
            <span>{downloadStatus.progress_percent.toFixed(1)}%</span>
            <span>
              {(downloadStatus.bytes_downloaded / 1024 / 1024).toFixed(0)} /{' '}
              {(downloadStatus.total_bytes / 1024 / 1024).toFixed(0)} MB
            </span>
          </div>
        </div>
      )}

      {/* Download Complete Message */}
      {downloadStatus?.status === 'completed' && (
        <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4">
          <div className="flex items-center gap-2 text-green-300">
            <Check className="h-4 w-4" />
            <span className="text-sm font-medium">
              {downloadStatus.model_name} downloaded successfully!
            </span>
          </div>
        </div>
      )}

      {/* Installed Models */}
      <div>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-zinc-300">
          <HardDrive className="h-4 w-4" />
          Installed Models ({localModels.length})
        </h3>
        <div className="space-y-2">
          {localModels.map((model) => {
            const isActive = currentModel === model.path;
            const isSwitching = switching === model.path;
            
            return (
              <div
                key={model.path}
                className={cn(
                  'flex items-center justify-between rounded-lg border p-3 transition-colors',
                  isActive
                    ? 'border-green-500/50 bg-green-500/10'
                    : 'border-zinc-700 bg-zinc-800/50 hover:bg-zinc-800'
                )}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate font-medium text-white">{model.filename}</p>
                    {isActive && (
                      <span className="flex items-center gap-1 rounded bg-green-500/20 px-1.5 py-0.5 text-xs text-green-400">
                        <Check className="h-3 w-3" /> Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-zinc-500">{model.size_mb.toFixed(0)} MB</p>
                </div>
                {!isActive && (
                  <button
                    onClick={() => onSwitchModel(model.path)}
                    disabled={isSwitching || isDownloading}
                    className="ml-3 flex items-center gap-1.5 rounded-lg bg-zinc-700 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-zinc-600 disabled:opacity-50"
                  >
                    {isSwitching ? (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      'Use'
                    )}
                  </button>
                )}
              </div>
            );
          })}
          {localModels.length === 0 && (
            <p className="text-sm text-zinc-500">No models installed. Download one below.</p>
          )}
        </div>
      </div>

      {/* Download New Models */}
      <div>
        <button
          onClick={() => setShowDownloadable(!showDownloadable)}
          className="mb-3 flex w-full items-center gap-2 text-sm font-medium text-zinc-300 hover:text-white"
        >
          {showDownloadable ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          <Download className="h-4 w-4" />
          Download New Models ({downloadableModels.length})
        </button>

        {showDownloadable && (
          <div className="space-y-2">
            {downloadableModels.map((model) => {
              const isInstalled = installedFilenames.has(model.filename);
              
              return (
                <div
                  key={model.filename}
                  className={cn(
                    'rounded-lg border p-4 transition-colors',
                    model.recommended
                      ? 'border-yellow-500/30 bg-yellow-500/5'
                      : 'border-zinc-700 bg-zinc-800/50'
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-white">{model.name}</p>
                        {model.recommended && (
                          <span className="rounded bg-yellow-500/20 px-1.5 py-0.5 text-xs text-yellow-400">
                            Recommended
                          </span>
                        )}
                        {isInstalled && (
                          <span className="rounded bg-green-500/20 px-1.5 py-0.5 text-xs text-green-400">
                            Installed
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-xs text-zinc-400">{model.description}</p>
                      <p className="mt-1 text-xs text-zinc-500">
                        {model.size_mb.toLocaleString()} MB • {model.filename}
                      </p>
                    </div>
                    {!isInstalled && (
                      <button
                        onClick={() => onStartDownload(model.filename)}
                        disabled={isDownloading}
                        className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
                      >
                        <Download className="h-3 w-3" />
                        Download
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

interface GenerationSettingsProps {
  temperature: number;
  maxTokens: number;
  gpuLayers: number;
  contextLength: number;
  onTemperatureChange: (value: number) => void;
  onMaxTokensChange: (value: number) => void;
  onGpuLayersChange: (value: number) => void;
  onContextLengthChange: (value: number) => void;
}

function GenerationSettings({
  temperature,
  maxTokens,
  gpuLayers,
  contextLength,
  onTemperatureChange,
  onMaxTokensChange,
  onGpuLayersChange,
  onContextLengthChange,
}: GenerationSettingsProps) {
  return (
    <div className="space-y-6">
      {/* Temperature */}
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-white">Temperature</label>
          <span className="rounded bg-zinc-700 px-2 py-0.5 text-sm font-mono text-zinc-300">
            {temperature.toFixed(1)}
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={temperature}
          onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
          className="mt-3 w-full accent-blue-500"
        />
        <p className="mt-2 text-xs text-zinc-500">
          Higher values make output more random and creative, lower values more deterministic and focused.
        </p>
      </div>

      {/* Max Tokens */}
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-white">Max Response Tokens</label>
          <span className="rounded bg-zinc-700 px-2 py-0.5 text-sm font-mono text-zinc-300">
            {maxTokens}
          </span>
        </div>
        <input
          type="range"
          min="128"
          max="4096"
          step="128"
          value={maxTokens}
          onChange={(e) => onMaxTokensChange(parseInt(e.target.value))}
          className="mt-3 w-full accent-blue-500"
        />
        <p className="mt-2 text-xs text-zinc-500">
          Maximum length of the generated response. Higher values allow longer responses but use more memory.
        </p>
      </div>

      {/* Context Length */}
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-white">Context Length</label>
          <span className="rounded bg-zinc-700 px-2 py-0.5 text-sm font-mono text-zinc-300">
            {contextLength.toLocaleString()}
          </span>
        </div>
        <input
          type="range"
          min="512"
          max="8192"
          step="512"
          value={contextLength}
          onChange={(e) => onContextLengthChange(parseInt(e.target.value))}
          className="mt-3 w-full accent-blue-500"
        />
        <p className="mt-2 text-xs text-zinc-500">
          Total context window size. Larger values allow more conversation history but require more VRAM.
        </p>
      </div>

      {/* GPU Layers */}
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-white">GPU Layers</label>
          <span className="rounded bg-zinc-700 px-2 py-0.5 text-sm font-mono text-zinc-300">
            {gpuLayers === 0 ? 'CPU Only' : gpuLayers === -1 ? 'All' : gpuLayers}
          </span>
        </div>
        <input
          type="range"
          min="0"
          max="64"
          step="1"
          value={gpuLayers === -1 ? 64 : gpuLayers}
          onChange={(e) => {
            const val = parseInt(e.target.value);
            onGpuLayersChange(val === 64 ? -1 : val);
          }}
          className="mt-3 w-full accent-blue-500"
        />
        <p className="mt-2 text-xs text-zinc-500">
          Number of layers to offload to GPU. Use 0 for CPU-only, or higher values for faster inference.
          Set to 64 for all layers. Requires model reload to take effect.
        </p>
      </div>
    </div>
  );
}

interface PersonalDataSettingsProps {
  conversationCount: number;
  onDeleteAllConversations: () => Promise<void>;
}

function PersonalDataSettings({
  conversationCount,
  onDeleteAllConversations,
}: PersonalDataSettingsProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleted, setDeleted] = useState(false);

  const handleDeleteAll = async () => {
    setDeleting(true);
    try {
      await onDeleteAllConversations();
      setDeleted(true);
      setShowConfirm(false);
      setTimeout(() => setDeleted(false), 3000);
    } catch (err) {
      console.error('Failed to delete conversations:', err);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Privacy Notice */}
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/20">
            <Shield className="h-5 w-5 text-green-400" />
          </div>
          <div>
            <h3 className="text-sm font-medium text-white">Your Data is Private</h3>
            <p className="text-xs text-zinc-400">
              All conversations are stored locally on your device. Nothing is sent to external servers.
            </p>
          </div>
        </div>
      </div>

      {/* Storage Info */}
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
          <MessageSquare className="h-4 w-4" />
          Stored Data
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-lg bg-zinc-900/50 p-3">
            <div>
              <p className="text-sm text-white">Conversations</p>
              <p className="text-xs text-zinc-500">Chat history and messages</p>
            </div>
            <span className="rounded-full bg-zinc-700 px-3 py-1 text-sm font-medium text-zinc-300">
              {conversationCount}
            </span>
          </div>
        </div>
      </div>

      {/* Success Message */}
      {deleted && (
        <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4">
          <div className="flex items-center gap-2 text-green-300">
            <Check className="h-4 w-4" />
            <span className="text-sm font-medium">All conversations deleted successfully!</span>
          </div>
        </div>
      )}

      {/* Danger Zone */}
      <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-red-400">
          <AlertTriangle className="h-4 w-4" />
          Danger Zone
        </h3>
        
        {!showConfirm ? (
          <div className="flex items-center justify-between rounded-lg bg-zinc-900/50 p-3">
            <div>
              <p className="text-sm text-white">Delete All Conversations</p>
              <p className="text-xs text-zinc-500">
                Permanently remove all {conversationCount} conversation{conversationCount !== 1 ? 's' : ''}
              </p>
            </div>
            <button
              onClick={() => setShowConfirm(true)}
              disabled={conversationCount === 0}
              className="flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete All
            </button>
          </div>
        ) : (
          <div className="rounded-lg bg-zinc-900/50 p-4">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/20">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">Are you sure?</p>
                <p className="text-xs text-zinc-400">
                  This will permanently delete all {conversationCount} conversations. This action cannot be undone.
                </p>
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                disabled={deleting}
                className="rounded-lg px-4 py-2 text-sm text-zinc-400 hover:bg-zinc-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAll}
                disabled={deleting}
                className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-500 disabled:opacity-50"
              >
                {deleting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    Yes, Delete All
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function AboutSettings() {
  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-6 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600">
          <Cpu className="h-8 w-8 text-white" />
        </div>
        <h3 className="text-xl font-bold text-white">Hearth AI</h3>
        <p className="mt-1 text-sm text-zinc-400">Local AI Assistant</p>
        <p className="mt-2 text-xs text-zinc-500">Version 1.0.0</p>
      </div>

      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
        <h4 className="mb-3 text-sm font-medium text-white">Features</h4>
        <div className="space-y-2 text-sm text-zinc-400">
          <div className="flex items-center gap-2">
            <span className="text-lg">💬</span>
            <span>Direct conversation with local LLMs</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg">📄</span>
            <span>RAG - Ask questions about your documents</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg">🌐</span>
            <span>Web search with AI summarization</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg">🔒</span>
            <span>100% local & private - your data never leaves your machine</span>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-4">
        <h4 className="mb-3 text-sm font-medium text-white">Tech Stack</h4>
        <div className="flex flex-wrap gap-2">
          {['React', 'Vite', 'Tailwind CSS', 'FastAPI', 'llama.cpp', 'ChromaDB', 'FastEmbed'].map(
            (tech) => (
              <span
                key={tech}
                className="rounded-full bg-zinc-700 px-3 py-1 text-xs text-zinc-300"
              >
                {tech}
              </span>
            )
          )}
        </div>
      </div>
    </div>
  );
}
