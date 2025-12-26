import { useState, useEffect } from 'react';
import { useSettings } from '../contexts/SettingsContext';
import { cn } from '../lib/utils';
import { X, Cpu, Sliders, Info } from 'lucide-react';
import * as api from '../lib/api';
import type { ModelInfo } from '../lib/types';

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
}

export function SettingsDialog({ open, onClose }: SettingsDialogProps) {
  const { settings, updateSettings } = useSettings();
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [activeTab, setActiveTab] = useState<'model' | 'generation' | 'about'>('model');

  useEffect(() => {
    if (open) {
      api.listModels().then((data) => setModels(data.models));
    }
  }, [open]);

  if (!open || !settings) return null;

  const handleTemperatureChange = (value: number) => {
    updateSettings({ temperature: value });
  };

  const handleMaxTokensChange = (value: number) => {
    updateSettings({ max_tokens: value });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="relative z-10 w-full max-w-lg rounded-xl border border-border bg-background shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-lg font-semibold">Settings</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 hover:bg-secondary transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <TabButton
            active={activeTab === 'model'}
            onClick={() => setActiveTab('model')}
            icon={<Cpu className="h-4 w-4" />}
            label="Model"
          />
          <TabButton
            active={activeTab === 'generation'}
            onClick={() => setActiveTab('generation')}
            icon={<Sliders className="h-4 w-4" />}
            label="Generation"
          />
          <TabButton
            active={activeTab === 'about'}
            onClick={() => setActiveTab('about')}
            icon={<Info className="h-4 w-4" />}
            label="About"
          />
        </div>

        {/* Content */}
        <div className="p-4">
          {activeTab === 'model' && (
            <ModelSettings models={models} currentModel={settings.model_path} />
          )}
          {activeTab === 'generation' && (
            <GenerationSettings
              temperature={settings.temperature}
              maxTokens={settings.max_tokens}
              onTemperatureChange={handleTemperatureChange}
              onMaxTokensChange={handleMaxTokensChange}
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
        'flex flex-1 items-center justify-center gap-2 px-4 py-2',
        'text-sm transition-colors',
        active
          ? 'border-b-2 border-primary text-foreground'
          : 'text-muted-foreground hover:text-foreground'
      )}
    >
      {icon}
      {label}
    </button>
  );
}

interface ModelSettingsProps {
  models: ModelInfo[];
  currentModel: string | null;
}

function ModelSettings({ models, currentModel }: ModelSettingsProps) {
  return (
    <div className="space-y-4">
      <div>
        <label className="text-sm font-medium text-foreground">
          Current Model
        </label>
        <p className="mt-1 text-sm text-muted-foreground">
          {currentModel ? currentModel.split('/').pop() : 'No model loaded'}
        </p>
      </div>

      <div>
        <label className="text-sm font-medium text-foreground">
          Available Models
        </label>
        <div className="mt-2 space-y-2">
          {models.map((model) => (
            <div
              key={model.path}
              className={cn(
                'flex items-center justify-between rounded-lg border border-border p-3',
                currentModel === model.path && 'border-primary bg-primary/5'
              )}
            >
              <div>
                <p className="text-sm font-medium">{model.filename}</p>
                <p className="text-xs text-muted-foreground">
                  {model.size_mb.toFixed(1)} MB
                </p>
              </div>
              {currentModel === model.path && (
                <span className="text-xs text-primary">Active</span>
              )}
            </div>
          ))}
          {models.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No models found in the models directory
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

interface GenerationSettingsProps {
  temperature: number;
  maxTokens: number;
  onTemperatureChange: (value: number) => void;
  onMaxTokensChange: (value: number) => void;
}

function GenerationSettings({
  temperature,
  maxTokens,
  onTemperatureChange,
  onMaxTokensChange,
}: GenerationSettingsProps) {
  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-foreground">
            Temperature
          </label>
          <span className="text-sm text-muted-foreground">{temperature}</span>
        </div>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={temperature}
          onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
          className="mt-2 w-full"
        />
        <p className="mt-1 text-xs text-muted-foreground">
          Higher values make output more random, lower values more deterministic
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-foreground">
            Max Tokens
          </label>
          <span className="text-sm text-muted-foreground">{maxTokens}</span>
        </div>
        <input
          type="range"
          min="128"
          max="4096"
          step="128"
          value={maxTokens}
          onChange={(e) => onMaxTokensChange(parseInt(e.target.value))}
          className="mt-2 w-full"
        />
        <p className="mt-1 text-xs text-muted-foreground">
          Maximum length of the generated response
        </p>
      </div>
    </div>
  );
}

function AboutSettings() {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium text-foreground">AI Chat</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          A local AI chat application with RAG and web search capabilities.
        </p>
      </div>

      <div>
        <h4 className="text-sm font-medium text-foreground">Features</h4>
        <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
          <li>💬 Chat - Direct conversation with local LLM</li>
          <li>📄 RAG - Ask questions about your documents</li>
          <li>🌐 Search - Web search with AI summarization</li>
        </ul>
      </div>

      <div>
        <h4 className="text-sm font-medium text-foreground">Tech Stack</h4>
        <p className="mt-1 text-sm text-muted-foreground">
          React + Vite + Tailwind CSS • FastAPI + llama.cpp • ChromaDB
        </p>
      </div>
    </div>
  );
}
