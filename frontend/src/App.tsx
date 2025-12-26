import { useState } from 'react';
import { SettingsProvider } from './contexts/SettingsContext';
import { ConversationProvider } from './contexts/ConversationContext';
import { ChatProvider } from './contexts/ChatContext';
import { Sidebar } from './components/Sidebar';
import { ChatView } from './components/chat/ChatView';
import { MessageInput } from './components/chat/MessageInput';
import { SettingsDialog } from './components/SettingsDialog';

function AppContent() {
  const [settingsOpen, setSettingsOpen] = useState(false);

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
