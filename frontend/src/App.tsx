import { useState, useEffect, useCallback } from 'react';
import { SettingsProvider } from './contexts/SettingsContext';
import { ConversationProvider } from './contexts/ConversationContext';
import { ChatProvider } from './contexts/ChatContext';
import { Sidebar } from './components/Sidebar';
import { ChatView } from './components/chat/ChatView';
import { MessageInput } from './components/chat/MessageInput';
import { SettingsDialog } from './components/SettingsDialog';
import { ModelDownloadOverlay } from './components/ModelDownloadOverlay';
import * as api from './lib/api';
import { Loader2 } from 'lucide-react';

function AppContent() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [needsModel, setNeedsModel] = useState<boolean | null>(null);
  const [checkingModel, setCheckingModel] = useState(true);

  const checkModelStatus = useCallback(async () => {
    try {
      const status = await api.getModelStatus();
      setNeedsModel(status.needs_download);
    } catch (err) {
      console.error('Failed to check model status:', err);
      // If we can't connect, assume we need a model
      setNeedsModel(true);
    } finally {
      setCheckingModel(false);
    }
  }, []);

  useEffect(() => {
    checkModelStatus();
  }, [checkModelStatus]);

  const handleDownloadComplete = useCallback(() => {
    // Refresh model status after download completes
    setNeedsModel(false);
    // Optionally reload the page to reinitialize everything
    window.location.reload();
  }, []);

  // Show loading while checking model status
  if (checkingModel) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4 text-foreground">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          <p className="text-zinc-400">Starting Hearth AI...</p>
        </div>
      </div>
    );
  }

  // Show model download overlay if needed
  if (needsModel) {
    return <ModelDownloadOverlay onComplete={handleDownloadComplete} />;
  }

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <Sidebar onSettingsClick={() => setSettingsOpen(true)} />

      {/* Main Content */}
      <div className="flex flex-1 flex-col">
        {/* Chat Area */}
        <ChatView />

        {/* Input Area */}
        <MessageInput />
      </div>

      {/* Settings Dialog */}
      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <SettingsProvider>
      <ConversationProvider>
        <ChatProvider>
          <AppContent />
        </ChatProvider>
      </ConversationProvider>
    </SettingsProvider>
  );
}
