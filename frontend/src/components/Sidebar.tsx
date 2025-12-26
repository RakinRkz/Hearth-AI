import { useState, useRef, useEffect } from 'react';
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
  Upload,
  File,
  X,
  Loader2,
} from 'lucide-react';
import type { ChatMode, DocumentInfo } from '../lib/types';
import * as api from '../lib/api';

interface SidebarProps {
  onSettingsClick: () => void;
}

export function Sidebar({ onSettingsClick }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const {
    conversations,
    activeId,
    loadConversation,
    createConversation,
    deleteConversation,
  } = useConversations();
  const { clearMessages } = useChat();
  const { mode, setMode } = useSettings();

  // Load documents when in RAG mode
  useEffect(() => {
    if (mode === 'rag') {
      loadDocuments();
    }
  }, [mode]);

  const loadDocuments = async () => {
    try {
      const docs = await api.listDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await api.uploadDocument(file);
      }
      await loadDocuments();
    } catch (err) {
      console.error('Failed to upload document:', err);
      alert(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteDocument = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await api.deleteDocument(id);
      await loadDocuments();
    } catch (err) {
      console.error('Failed to delete document:', err);
    }
  };

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

      {/* Documents Section (RAG mode only) */}
      {mode === 'rag' && (
        <div className="border-b border-sidebar-border p-2">
          <div className="mb-2 flex items-center justify-between px-2">
            <p className="text-xs font-medium text-muted-foreground">
              Documents
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,.md,.docx"
              multiple
              onChange={handleFileUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className={cn(
                'flex items-center gap-1 rounded px-2 py-1 text-xs',
                'bg-sidebar-accent text-sidebar-accent-foreground',
                'hover:bg-sidebar-accent/80 transition-colors',
                'disabled:opacity-50'
              )}
            >
              {uploading ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Upload className="h-3 w-3" />
              )}
              Upload
            </button>
          </div>
          <div className="max-h-32 space-y-1 overflow-y-auto">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="group flex items-center gap-2 rounded px-2 py-1 text-xs text-sidebar-foreground hover:bg-sidebar-accent/50"
              >
                <File className="h-3 w-3 shrink-0 text-muted-foreground" />
                <span className="flex-1 truncate" title={doc.filename}>
                  {doc.filename}
                </span>
                <span className="text-muted-foreground">
                  {doc.chunk_count}
                </span>
                <button
                  onClick={(e) => handleDeleteDocument(e, doc.id)}
                  className="rounded p-0.5 opacity-0 hover:bg-destructive/20 hover:text-destructive group-hover:opacity-100"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
            {documents.length === 0 && (
              <p className="px-2 py-2 text-center text-xs text-muted-foreground">
                No documents uploaded
              </p>
            )}
          </div>
        </div>
      )}

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
