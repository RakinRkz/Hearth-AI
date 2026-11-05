import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import type { Settings, ChatMode } from '../lib/types';
import * as api from '../lib/api';

interface SettingsContextType {
  settings: Settings | null;
  loading: boolean;
  error: string | null;
  mode: ChatMode;
  setMode: (mode: ChatMode) => Promise<void>;
  updateSettings: (settings: Partial<Settings>) => Promise<void>;
  refreshSettings: () => Promise<void>;
}

const defaultSettings: Settings = {
  mode: 'chat',
  model_path: null,
  context_length: 2048,
  max_tokens: 1024,
  temperature: 0.7,
  top_p: 0.9,
  top_k: 40,
  repeat_penalty: 1.1,
  gpu_layers: -1,
  embedding_model: 'all-MiniLM-L6-v2',
  chunk_size: 500,
  chunk_overlap: 50,
  top_k_results: 4,
  search_enabled: true,
  max_search_results: 5,
  theme: 'dark',
};

const SettingsContext = createContext<SettingsContextType | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshSettings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSettings();
      setSettings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
      setSettings(defaultSettings);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSettings();
  }, [refreshSettings]);

  const setMode = useCallback(async (mode: ChatMode) => {
    try {
      const updated = await api.setMode(mode);
      setSettings(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set mode');
      throw err;
    }
  }, []);

  const updateSettings = useCallback(async (newSettings: Partial<Settings>) => {
    const previousSettings = settings;
    const reloadRequired =
      previousSettings !== null &&
      (newSettings.context_length !== undefined || newSettings.gpu_layers !== undefined);
    let settingsUpdated = false;

    try {
      const updated = await api.updateSettings(newSettings);
      settingsUpdated = true;

      if (reloadRequired) {
        const reload = await api.reloadServices();
        if (!reload.success) {
          const errors = Object.values(reload.status)
            .filter((value): value is string[] => Array.isArray(value))
            .flat();
          throw new Error(errors.join(', ') || 'Failed to reload the model');
        }
      }
      setSettings(updated);
    } catch (err) {
      let errorMessage = err instanceof Error ? err.message : 'Failed to update settings';
      if (previousSettings && settingsUpdated && reloadRequired) {
        try {
          await api.updateSettings({
            context_length: previousSettings.context_length,
            gpu_layers: previousSettings.gpu_layers,
          });
          const rollback = await api.reloadServices();
          if (!rollback.success) {
            errorMessage += '; failed to restore the previous model settings';
          }
        } catch {
          errorMessage += '; failed to restore the previous model settings';
        } finally {
          setSettings(previousSettings);
        }
      }
      setError(errorMessage);
      throw err;
    }
  }, [settings]);

  const mode = settings?.mode ?? 'chat';

  return (
    <SettingsContext.Provider
      value={{
        settings,
        loading,
        error,
        mode,
        setMode,
        updateSettings,
        refreshSettings,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}
