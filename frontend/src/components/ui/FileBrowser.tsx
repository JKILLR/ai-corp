import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Folder,
  File,
  FileText,
  Image,
  Code,
  Database,
  Package,
  Paperclip,
  Upload,
  Search,
  ChevronRight,
  HardDrive,
  Cloud,
  ExternalLink,
  Eye,
  Download,
  Check,
} from 'lucide-react';
import { GlassCard } from './GlassCard';

export interface FileItem {
  id: string;
  name: string;
  location: 'internal' | 'google_drive';
  category: 'document' | 'image' | 'code' | 'data' | 'artifact' | 'attachment' | 'export';
  size_bytes: number;
  mime_type: string;
  created_at: string;
  modified_at: string;
  description?: string;
  tags?: string[];
  external_path?: string;
  is_cached?: boolean;
}

export interface FolderItem {
  id: string;
  name: string;
  path: string;
  is_shared: boolean;
}

interface FileBrowserProps {
  internalFiles: FileItem[];
  driveFiles: FileItem[];
  driveFolders: FolderItem[];
  driveConfigured: boolean;
  onFileSelect?: (file: FileItem) => void;
  onFilePreview?: (file: FileItem) => void;
  onFileExport?: (file: FileItem) => void;
  onUpload?: () => void;
  onConfigureDrive?: () => void;
  selectable?: boolean;
  selectedFiles?: string[];
  className?: string;
}

const categoryIcons: Record<string, React.ElementType> = {
  document: FileText,
  image: Image,
  code: Code,
  data: Database,
  artifact: Package,
  attachment: Paperclip,
  export: ExternalLink,
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined,
  });
};

export const FileBrowser = ({
  internalFiles,
  driveFiles,
  driveFolders,
  driveConfigured,
  onFileSelect,
  onFilePreview,
  onFileExport,
  onUpload,
  onConfigureDrive,
  selectable = false,
  selectedFiles = [],
  className = '',
}: FileBrowserProps) => {
  const [activeTab, setActiveTab] = useState<'internal' | 'drive'>('internal');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentFolder, setCurrentFolder] = useState<string | null>(null);
  const [hoveredFile, setHoveredFile] = useState<string | null>(null);

  const filterFiles = (files: FileItem[]): FileItem[] => {
    if (!searchQuery) return files;
    const query = searchQuery.toLowerCase();
    return files.filter(
      (f) =>
        f.name.toLowerCase().includes(query) ||
        f.description?.toLowerCase().includes(query) ||
        f.tags?.some((t) => t.toLowerCase().includes(query))
    );
  };

  const filteredInternalFiles = filterFiles(internalFiles);
  const filteredDriveFiles = filterFiles(driveFiles);

  const isSelected = (fileId: string) => selectedFiles.includes(fileId);

  const handleFileClick = (file: FileItem) => {
    if (selectable && onFileSelect) {
      onFileSelect(file);
    } else if (onFilePreview) {
      onFilePreview(file);
    }
  };

  const renderFileIcon = (file: FileItem) => {
    const Icon = categoryIcons[file.category] || File;
    return <Icon className="w-5 h-5 text-[var(--text-secondary)]" />;
  };

  const renderFileItem = (file: FileItem) => (
    <motion.div
      key={file.id}
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className={`
        flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all
        ${isSelected(file.id) ? 'bg-purple-500/20 border border-purple-500/40' : 'hover:bg-white/5'}
      `}
      onClick={() => handleFileClick(file)}
      onMouseEnter={() => setHoveredFile(file.id)}
      onMouseLeave={() => setHoveredFile(null)}
    >
      {/* Selection checkbox */}
      {selectable && (
        <div
          className={`
            w-5 h-5 rounded border flex items-center justify-center
            ${isSelected(file.id) ? 'bg-purple-500 border-purple-500' : 'border-white/30'}
          `}
        >
          {isSelected(file.id) && <Check className="w-3 h-3 text-white" />}
        </div>
      )}

      {/* File icon */}
      <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center">
        {renderFileIcon(file)}
      </div>

      {/* File info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-[var(--text-primary)] truncate">
            {file.name}
          </span>
          {file.location === 'google_drive' && file.is_cached && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/20 text-green-400">
              Cached
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
          <span>{formatFileSize(file.size_bytes)}</span>
          <span>•</span>
          <span>{formatDate(file.modified_at || file.created_at)}</span>
          {file.tags && file.tags.length > 0 && (
            <>
              <span>•</span>
              <span className="truncate">{file.tags.slice(0, 2).join(', ')}</span>
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      <AnimatePresence>
        {hoveredFile === file.id && !selectable && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            className="flex items-center gap-1"
          >
            {onFilePreview && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onFilePreview(file);
                }}
                className="p-1.5 rounded hover:bg-white/10 text-[var(--text-secondary)]"
                title="Preview"
              >
                <Eye className="w-4 h-4" />
              </button>
            )}
            {onFileExport && file.location === 'internal' && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onFileExport(file);
                }}
                className="p-1.5 rounded hover:bg-white/10 text-[var(--text-secondary)]"
                title="Export to Drive"
              >
                <ExternalLink className="w-4 h-4" />
              </button>
            )}
            {file.location === 'google_drive' && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  // Download/fetch from drive
                }}
                className="p-1.5 rounded hover:bg-white/10 text-[var(--text-secondary)]"
                title="Download"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );

  const renderFolderItem = (folder: FolderItem) => (
    <motion.div
      key={folder.id}
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3 p-3 rounded-lg cursor-pointer hover:bg-white/5"
      onClick={() => setCurrentFolder(folder.path)}
    >
      <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
        <Folder className="w-5 h-5 text-purple-400" />
      </div>
      <div className="flex-1">
        <span className="text-sm font-medium text-[var(--text-primary)]">{folder.name}</span>
        {folder.is_shared && (
          <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400">
            Shared
          </span>
        )}
      </div>
      <ChevronRight className="w-4 h-4 text-[var(--text-tertiary)]" />
    </motion.div>
  );

  return (
    <GlassCard padding="none" className={`overflow-hidden ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        {/* Tabs */}
        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={() => setActiveTab('internal')}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${activeTab === 'internal' ? 'bg-purple-500/20 text-purple-300' : 'text-[var(--text-secondary)] hover:bg-white/5'}
            `}
          >
            <HardDrive className="w-4 h-4" />
            Internal
            <span className="ml-1 text-xs opacity-60">({internalFiles.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('drive')}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
              ${activeTab === 'drive' ? 'bg-purple-500/20 text-purple-300' : 'text-[var(--text-secondary)] hover:bg-white/5'}
            `}
          >
            <Cloud className="w-4 h-4" />
            Google Drive
            {driveConfigured ? (
              <span className="ml-1 text-xs opacity-60">({driveFiles.length})</span>
            ) : (
              <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-400">
                Not Connected
              </span>
            )}
          </button>
        </div>

        {/* Search and actions */}
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-purple-500/50"
            />
          </div>
          {onUpload && activeTab === 'internal' && (
            <button
              onClick={onUpload}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 text-sm font-medium hover:bg-purple-500/30 transition-colors"
            >
              <Upload className="w-4 h-4" />
              Upload
            </button>
          )}
        </div>
      </div>

      {/* File list */}
      <div className="p-4 max-h-[500px] overflow-y-auto">
        {activeTab === 'internal' && (
          <div className="space-y-1">
            {filteredInternalFiles.length === 0 ? (
              <div className="text-center py-12 text-[var(--text-tertiary)]">
                <HardDrive className="w-12 h-12 mx-auto mb-3 opacity-40" />
                <p className="text-sm">No internal files yet</p>
                {onUpload && (
                  <button
                    onClick={onUpload}
                    className="mt-3 text-sm text-purple-400 hover:text-purple-300"
                  >
                    Upload your first file
                  </button>
                )}
              </div>
            ) : (
              filteredInternalFiles.map(renderFileItem)
            )}
          </div>
        )}

        {activeTab === 'drive' && (
          <>
            {!driveConfigured ? (
              <div className="text-center py-12 text-[var(--text-tertiary)]">
                <Cloud className="w-12 h-12 mx-auto mb-3 opacity-40" />
                <p className="text-sm mb-3">Google Drive not connected</p>
                {onConfigureDrive && (
                  <button
                    onClick={onConfigureDrive}
                    className="px-4 py-2 rounded-lg bg-blue-500/20 text-blue-300 text-sm font-medium hover:bg-blue-500/30 transition-colors"
                  >
                    Connect Google Drive
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-1">
                {/* Breadcrumb */}
                {currentFolder && (
                  <div className="flex items-center gap-2 mb-3 text-sm text-[var(--text-secondary)]">
                    <button
                      onClick={() => setCurrentFolder(null)}
                      className="hover:text-[var(--text-primary)]"
                    >
                      Root
                    </button>
                    <ChevronRight className="w-4 h-4" />
                    <span className="text-[var(--text-primary)]">{currentFolder}</span>
                  </div>
                )}

                {/* Folders */}
                {driveFolders.length > 0 && (
                  <div className="mb-2">
                    {driveFolders.map(renderFolderItem)}
                  </div>
                )}

                {/* Files */}
                {filteredDriveFiles.length === 0 ? (
                  <div className="text-center py-8 text-[var(--text-tertiary)]">
                    <File className="w-8 h-8 mx-auto mb-2 opacity-40" />
                    <p className="text-sm">No files in this folder</p>
                  </div>
                ) : (
                  filteredDriveFiles.map(renderFileItem)
                )}
              </div>
            )}
          </>
        )}
      </div>
    </GlassCard>
  );
};

export default FileBrowser;
