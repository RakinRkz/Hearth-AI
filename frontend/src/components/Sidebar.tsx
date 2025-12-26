import { useState } from 'react';
import { useConversations } from '../contexts/ConversationContext';
import { useChat } from '../contexts/ChatContext';
import { useSettings } from '../contexts/SettingsContext';
import { cn } from '../lib/utils';
import {
  Plus,
  MessageSquare,
  Search,
  FileText,
  Trash2,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { ChatMode } from '../lib/types';

interface SidebarProps {
  onSettingsClick: () => void;
}

export function Sidebar({ onSettingsClick }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const {
    conversations,
    activeId,
    loadConversation,
    createConversation,
    deleteConversation,
  } = useConversations();
  const { clearMessages } = useChat();
  const { mode, setMode } = useSettings();

  const handleNewChat = async () => {
    clearMessages();
    await createConversation();
  };

  const handleSelectConversation = async (id: string) => {
    try {
      await loadConversation(id);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteConversation(id);
  };

  const handleModeChange = async (newMode: ChatMode) => {
    try {
      await setMode(newMode);
    } catch (err) {
      console.error('Failed to set mode:', err);
    }
  };

  if (collapsed) {
    return (
      <div className="flex w-12 flex-col border-r border-sidebar-border bg-sidebar">
        <button
          onClick={() => setCollapsed(false)}
          className="flex h-12 items-center justify-center hover:bg-sidebar-accent"
        >
          <ChevronRight className="h-5 w-5 text-sidebar-foreground" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex w-64 flex-col border-r border-sidebar-border bg-sidebar">
      {/* Header */}
      <div className="flex h-12 items-center justify-between border-b border-sidebar-border px-3">
        <span className="text-sm font-semibold text-sidebar-foreground">
          AI Chat
        </span>
        <button
          onClick={() => setCollapsed(true)}
          className="rounded p-1 hover:bg-sidebar-accent"
        >
          <ChevronLeft className="h-4 w-4 text-sidebar-foreground" />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-2">
        <button
          onClick={handleNewChat}
          className={cn(
            'flex w-full items-center gap-2 rounded-lg px-3 py-2',
            'border border-sidebar-border',
            'hover:bg-sidebar-accent transition-colors',
            'text-sm text-sidebar-foreground'
          )}
        >
          <Plus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      {/* Mode Selector */}
      <div className="border-b border-sidebar-border px-2 pb-2">
        <p className="mb-2 px-2 text-xs font-medium text-muted-foreground">
          Mode
        </p>
        <div className="flex gap-1">
          <ModeButton
            mode="chat"
            currentMode={mode}
            onClick={() => handleModeChange('chat')}
            icon={<MessageSquare className="h-4 w-4" />}
            label="Chat"
          />
          <ModeButton
            mode="rag"
            currentMode={mode}
            onClick={() => handleModeChange('rag')}
            icon={<FileText className="h-4 w-4" />}
            label="RAG"
          />
          <ModeButton
            mode="search"
            currentMode={mode}
            onClick={() => handleModeChange('search')}
            icon={<Search className="h-4 w-4" />}
            label="Web"
          />
        </div>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto p-2">
        <p className="mb-2 px-2 text-xs font-medium text-muted-foreground">
          Recent Chats
        </p>
        <div className="space-y-1">
          {conversations.map((conv) => (
            <ConversationItem
              key={conv.id}
              id={conv.id}
              title={conv.title}
              isActive={conv.id === activeId}
              onClick={() => handleSelectConversation(conv.id)}
              onDelete={(e) => handleDeleteConversation(e, conv.id)}
            />
          ))}
          {conversations.length === 0 && (
            <p className="px-2 py-4 text-center text-xs text-muted-foreground">
              No conversations yet
            </p>
          )}
        </div>
      </div>

      {/* Settings Button */}
      <div className="border-t border-sidebar-border p-2">
        <button
          onClick={onSettingsClick}
          className={cn(
            'flex w-full items-center gap-2 rounded-lg px-3 py-2',
            'hover:bg-sidebar-accent transition-colors',
            'text-sm text-sidebar-foreground'
          )}
        >
          <Settings className="h-4 w-4" />
          Settings
        </button>
      </div>
    </div>
  );
}

interface ModeButtonProps {
  mode: ChatMode;
  currentMode: ChatMode;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}

function ModeButton({ mode, currentMode, onClick, icon, label }: ModeButtonProps) {
  const isActive = mode === currentMode;

  return (
    <button
      onClick={onClick}
      className={cn(
        'flex flex-1 items-center justify-center gap-1 rounded-md px-2 py-1.5',
        'text-xs transition-colors',
        isActive
          ? 'bg-sidebar-accent text-sidebar-accent-foreground'
          : 'text-muted-foreground hover:bg-sidebar-accent/50'
      )}
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </button>
  );
}

interface ConversationItemProps {
  id: string;
  title: string;
  isActive: boolean;
  onClick: () => void;
  onDelete: (e: React.MouseEvent) => void;
}

function ConversationItem({
  title,
  isActive,
  onClick,
  onDelete,
}: ConversationItemProps) {
  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
      className={cn(
        'group flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left cursor-pointer',
        'transition-colors',
        isActive
          ? 'bg-sidebar-accent text-sidebar-accent-foreground'
          : 'text-sidebar-foreground hover:bg-sidebar-accent/50'
      )}
    >
      <MessageSquare className="h-4 w-4 shrink-0" />
      <span className="flex-1 truncate text-sm">{title}</span>
      <button
        onClick={onDelete}
        className={cn(
          'rounded p-1 opacity-0 transition-opacity',
          'hover:bg-destructive/20 hover:text-destructive',
          'group-hover:opacity-100'
        )}
      >
        <Trash2 className="h-3 w-3" />
      </button>
    </div>
  );
}
