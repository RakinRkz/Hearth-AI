import { useState, useEffect, useCallback } from 'react';
import { Download, Loader2, CheckCircle, XCircle, Cpu, HardDrive } from 'lucide-react';
import * as api from '../lib/api';
import type { DownloadStatus, DownloadableModel } from '../lib/types';

interface ModelDownloadOverlayProps {
  onComplete: () => void;
}

export function ModelDownloadOverlay({ onComplete }: ModelDownloadOverlayProps) {
  const [status, setStatus] = useState<DownloadStatus | null>(null);
  const [models, setModels] = useState<DownloadableModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch available models on mount
  useEffect(() => {
    async function fetchModels() {
      try {
        const { models } = await api.getDownloadableModels();
        setModels(models);
        // Select recommended model by default
        const recommended = models.find(m => m.recommended);
        if (recommended) {
          setSelectedModel(recommended.filename);
        } else if (models.length > 0) {
          setSelectedModel(models[0].filename);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load models');
      } finally {
        setLoading(false);
      }
    }
    fetchModels();
  }, []);

  // Poll download status when downloading
  useEffect(() => {
    if (!status?.is_downloading && status?.status !== 'downloading') return;

    const interval = setInterval(async () => {
      try {
        const newStatus = await api.getDownloadStatus();
        setStatus(newStatus);

        if (newStatus.status === 'completed') {
          // Try to reload services
          try {
            const reloadResult = await api.reloadServices();
            if (reloadResult.success) {
              // Services loaded successfully, complete
              setTimeout(() => onComplete(), 1000);
            } else {
              // Services failed to load, show error with restart option
              setStatus(prev => prev ? {
                ...prev,
                status: 'error',
                error: 'Model downloaded but failed to load. Please restart the application.',
              } : null);
            }
          } catch (reloadErr) {
            console.error('Failed to reload services:', reloadErr);
            // Still mark as completed but suggest restart
            setStatus(prev => prev ? {
              ...prev,
              status: 'completed',
              error: 'Model downloaded. Please restart the application to load it.',
            } : null);
          }
        }
      } catch (err) {
        console.error('Failed to get download status:', err);
      }
    }, 500);

    return () => clearInterval(interval);
  }, [status?.is_downloading, status?.status, onComplete]);

  const handleStartDownload = useCallback(async () => {
    if (!selectedModel) return;

    try {
      setError(null);
      const result = await api.startModelDownload(selectedModel);
      
      if (result.status === 'already_installed') {
        // Model already exists, complete immediately
        onComplete();
        return;
      }

      // Start polling status
      setStatus({
        is_downloading: true,
        model_name: result.model_name || '',
        filename: result.filename || selectedModel,
        bytes_downloaded: 0,
        total_bytes: (result.size_mb || 0) * 1024 * 1024,
        progress_percent: 0,
        status: 'downloading',
        error: null,
        started_at: new Date().toISOString(),
        completed_at: null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start download');
    }
  }, [selectedModel, onComplete]);

  const handleCancelDownload = useCallback(async () => {
    try {
      await api.cancelModelDownload();
      setStatus(null);
    } catch (err) {
      console.error('Failed to cancel download:', err);
    }
  }, []);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`;
  };

  const getEstimatedTime = (): string | null => {
    if (!status || status.bytes_downloaded === 0 || !status.started_at) return null;
    
    const elapsed = (Date.now() - new Date(status.started_at).getTime()) / 1000;
    if (elapsed < 3) return null; // Wait a bit before showing estimate
    
    const rate = status.bytes_downloaded / elapsed;
    const remaining = (status.total_bytes - status.bytes_downloaded) / rate;
    
    return formatTime(remaining);
  };

  // Loading state
  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
        <div className="flex flex-col items-center gap-4 text-white">
          <Loader2 className="h-8 w-8 animate-spin" />
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // Downloading state
  if (status?.status === 'downloading') {
    const eta = getEstimatedTime();
    
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
        <div className="mx-4 w-full max-w-lg rounded-xl bg-zinc-900 p-8 shadow-2xl">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/20">
              <Download className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Downloading Model</h2>
              <p className="text-sm text-zinc-400">{status.model_name}</p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mb-4">
            <div className="mb-2 flex justify-between text-sm">
              <span className="text-zinc-400">
                {formatBytes(status.bytes_downloaded)} / {formatBytes(status.total_bytes)}
              </span>
              <span className="text-zinc-300 font-medium">{status.progress_percent.toFixed(1)}%</span>
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full bg-zinc-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-400 transition-all duration-300"
                style={{ width: `${status.progress_percent}%` }}
              />
            </div>
            {eta && (
              <p className="mt-2 text-center text-sm text-zinc-500">
                Estimated time remaining: {eta}
              </p>
            )}
          </div>

          <button
            onClick={handleCancelDownload}
            className="w-full rounded-lg border border-zinc-700 py-2.5 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-800"
          >
            Cancel Download
          </button>
        </div>
      </div>
    );
  }

  // Completed state
  if (status?.status === 'completed') {
    const needsRestart = status.error != null;
    
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
        <div className="mx-4 w-full max-w-lg rounded-xl bg-zinc-900 p-8 shadow-2xl text-center">
          <div className="mb-4 flex justify-center">
            <div className={`flex h-16 w-16 items-center justify-center rounded-full ${needsRestart ? 'bg-yellow-500/20' : 'bg-green-500/20'}`}>
              <CheckCircle className={`h-8 w-8 ${needsRestart ? 'text-yellow-400' : 'text-green-400'}`} />
            </div>
          </div>
          <h2 className="mb-2 text-xl font-semibold text-white">Download Complete!</h2>
          {needsRestart ? (
            <>
              <p className="mb-4 text-zinc-400">{status.error}</p>
              <button
                onClick={() => window.location.reload()}
                className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500"
              >
                Restart Application
              </button>
            </>
          ) : (
            <p className="text-zinc-400">Loading the model...</p>
          )}
        </div>
      </div>
    );
  }

  // Error state
  if (status?.status === 'error') {
    const isLoadError = status.error?.includes('downloaded') || status.error?.includes('load');
    
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
        <div className="mx-4 w-full max-w-lg rounded-xl bg-zinc-900 p-8 shadow-2xl">
          <div className="mb-4 flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500/20">
              <XCircle className="h-8 w-8 text-red-400" />
            </div>
          </div>
          <h2 className="mb-2 text-center text-xl font-semibold text-white">
            {isLoadError ? 'Model Load Failed' : 'Download Failed'}
          </h2>
          <p className="mb-6 text-center text-zinc-400">{status.error}</p>
          <div className="flex gap-3">
            {isLoadError ? (
              <button
                onClick={() => window.location.reload()}
                className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500"
              >
                Restart Application
              </button>
            ) : (
              <button
                onClick={() => setStatus(null)}
                className="flex-1 rounded-lg bg-zinc-800 py-2.5 text-sm font-medium text-white transition-colors hover:bg-zinc-700"
              >
                Try Again
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Model selection state (initial)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-2xl rounded-xl bg-zinc-900 p-8 shadow-2xl">
        <div className="mb-6 text-center">
          <div className="mb-4 flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-500/20">
              <Cpu className="h-8 w-8 text-blue-400" />
            </div>
          </div>
          <h2 className="mb-2 text-2xl font-semibold text-white">Welcome to Hearth AI</h2>
          <p className="text-zinc-400">
            No AI model found. Please download a model to get started.
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-500/20 p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* Model selection */}
        <div className="mb-6 space-y-3">
          {models.map((model) => (
            <button
              key={model.filename}
              onClick={() => setSelectedModel(model.filename)}
              className={`w-full rounded-lg border p-4 text-left transition-all ${
                selectedModel === model.filename
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white">{model.name}</span>
                    {model.recommended && (
                      <span className="rounded bg-blue-500/20 px-2 py-0.5 text-xs font-medium text-blue-300">
                        Recommended
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-zinc-400">{model.description}</p>
                </div>
                <div className="flex items-center gap-1.5 text-sm text-zinc-500">
                  <HardDrive className="h-4 w-4" />
                  <span>{(model.size_mb / 1024).toFixed(1)} GB</span>
                </div>
              </div>
            </button>
          ))}
        </div>

        <button
          onClick={handleStartDownload}
          disabled={!selectedModel}
          className="w-full rounded-lg bg-blue-600 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Download className="mr-2 inline-block h-4 w-4" />
          Download & Install
        </button>

        <p className="mt-4 text-center text-xs text-zinc-500">
          Models are downloaded from HuggingFace and stored locally.
          <br />
          You only need to download once.
        </p>
      </div>
    </div>
  );
}
