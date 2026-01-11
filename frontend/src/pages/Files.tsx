import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HardDrive,
  Cloud,
  Upload,
  FolderPlus,
  Settings,
  Download,
  ExternalLink,
  Trash2,
  X,
  Check,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { GlassCard, FileBrowser, type FileItem, type FolderItem } from '../components/ui';

// Empty arrays - no mock data
const emptyFiles: FileItem[] = [];
const emptyFolders: FolderItem[] = [];

interface StorageStats {
  internal: {
    total_files: number;
    total_size_bytes: number;
    by_category: Record<string, { count: number; size: number }>;
  };
  drive: {
    is_configured: boolean;
    indexed_files: number;
    indexed_folders: number;
    cached_files: number;
  };
  exports: {
    total_exports: number;
  };
}

const emptyStats: StorageStats = {
  internal: {
    total_files: 0,
    total_size_bytes: 0,
    by_category: {},
  },
  drive: {
    is_configured: false,
    indexed_files: 0,
    indexed_folders: 0,
    cached_files: 0,
  },
  exports: {
    total_exports: 0,
  },
};

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

export const Files = () => {
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDriveConfig, setShowDriveConfig] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [previewFile, setPreviewFile] = useState<FileItem | null>(null);

  // TODO: Fetch from API when available
  const internalFiles = emptyFiles;
  const driveFiles = emptyFiles;
  const driveFolders = emptyFolders;
  const stats = emptyStats;

  const handleFilePreview = (file: FileItem) => {
    setPreviewFile(file);
  };

  const handleFileExport = (file: FileItem) => {
    setSelectedFile(file);
    setShowExportModal(true);
  };

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[var(--text-primary)]">Files</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            Manage internal files and access external sources
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowDriveConfig(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 text-[var(--text-secondary)] text-sm hover:bg-white/10 transition-colors"
          >
            <Settings className="w-4 h-4" />
            Configure Drive
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 text-sm font-medium hover:bg-purple-500/30 transition-colors"
          >
            <Upload className="w-4 h-4" />
            Upload File
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlassCard padding="md">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <HardDrive className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {stats.internal.total_files}
              </p>
              <p className="text-xs text-[var(--text-tertiary)]">Internal Files</p>
            </div>
          </div>
          <p className="text-sm text-[var(--text-secondary)] mt-2">
            {formatBytes(stats.internal.total_size_bytes)} total
          </p>
        </GlassCard>

        <GlassCard padding="md">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
              <Cloud className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {stats.drive.indexed_files}
              </p>
              <p className="text-xs text-[var(--text-tertiary)]">Drive Files</p>
            </div>
          </div>
          <p className="text-sm text-[var(--text-secondary)] mt-2">
            {stats.drive.cached_files} cached locally
          </p>
        </GlassCard>

        <GlassCard padding="md">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
              <FolderPlus className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {stats.drive.indexed_folders}
              </p>
              <p className="text-xs text-[var(--text-tertiary)]">Drive Folders</p>
            </div>
          </div>
          <p className="text-sm text-[var(--text-secondary)] mt-2">
            {stats.drive.is_configured ? 'Connected' : 'Not connected'}
          </p>
        </GlassCard>

        <GlassCard padding="md">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
              <ExternalLink className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-[var(--text-primary)]">
                {stats.exports.total_exports}
              </p>
              <p className="text-xs text-[var(--text-tertiary)]">Total Exports</p>
            </div>
          </div>
          <p className="text-sm text-[var(--text-secondary)] mt-2">Files exported to Drive</p>
        </GlassCard>
      </div>

      {/* Main File Browser */}
      <FileBrowser
        internalFiles={internalFiles}
        driveFiles={driveFiles}
        driveFolders={driveFolders}
        driveConfigured={stats.drive.is_configured}
        onFilePreview={handleFilePreview}
        onFileExport={handleFileExport}
        onUpload={() => setShowUploadModal(true)}
        onConfigureDrive={() => setShowDriveConfig(true)}
      />

      {/* Upload Modal */}
      <AnimatePresence>
        {showUploadModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setShowUploadModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <GlassCard padding="lg">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-[var(--text-primary)]">Upload File</h2>
                  <button
                    onClick={() => setShowUploadModal(false)}
                    className="p-1 rounded hover:bg-white/10"
                  >
                    <X className="w-5 h-5 text-[var(--text-secondary)]" />
                  </button>
                </div>

                {/* Drop zone */}
                <div className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center hover:border-purple-500/50 transition-colors cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-[var(--text-tertiary)]" />
                  <p className="text-sm text-[var(--text-primary)] mb-1">
                    Drop files here or click to browse
                  </p>
                  <p className="text-xs text-[var(--text-tertiary)]">
                    Supports documents, images, code, and data files
                  </p>
                </div>

                {/* Scope selection */}
                <div className="mt-4">
                  <label className="text-sm text-[var(--text-secondary)] mb-2 block">
                    Upload scope
                  </label>
                  <select className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-[var(--text-primary)]">
                    <option value="shared">Shared (all agents)</option>
                    <option value="project">Current Project</option>
                    <option value="task">Current Task</option>
                  </select>
                </div>

                <div className="flex justify-end gap-3 mt-6">
                  <button
                    onClick={() => setShowUploadModal(false)}
                    className="px-4 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:bg-white/5"
                  >
                    Cancel
                  </button>
                  <button className="px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 text-sm font-medium hover:bg-purple-500/30">
                    Upload
                  </button>
                </div>
              </GlassCard>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Drive Config Modal */}
      <AnimatePresence>
        {showDriveConfig && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setShowDriveConfig(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <GlassCard padding="lg">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                    Google Drive Configuration
                  </h2>
                  <button
                    onClick={() => setShowDriveConfig(false)}
                    className="p-1 rounded hover:bg-white/10"
                  >
                    <X className="w-5 h-5 text-[var(--text-secondary)]" />
                  </button>
                </div>

                {stats.drive.is_configured ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                      <Check className="w-5 h-5 text-green-400" />
                      <div>
                        <p className="text-sm text-green-300 font-medium">Connected</p>
                        <p className="text-xs text-green-400/70">
                          Google Drive is configured and ready
                        </p>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                        <span className="text-sm text-[var(--text-secondary)]">Indexed files</span>
                        <span className="text-sm text-[var(--text-primary)]">
                          {stats.drive.indexed_files}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                        <span className="text-sm text-[var(--text-secondary)]">Cached files</span>
                        <span className="text-sm text-[var(--text-primary)]">
                          {stats.drive.cached_files}
                        </span>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-white/5 text-[var(--text-secondary)] text-sm hover:bg-white/10">
                        <RefreshCw className="w-4 h-4" />
                        Refresh Index
                      </button>
                      <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 text-red-400 text-sm hover:bg-red-500/20">
                        <Trash2 className="w-4 h-4" />
                        Clear Cache
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                      <AlertCircle className="w-5 h-5 text-yellow-400" />
                      <div>
                        <p className="text-sm text-yellow-300 font-medium">Not Connected</p>
                        <p className="text-xs text-yellow-400/70">
                          Connect Google Drive to access external files
                        </p>
                      </div>
                    </div>

                    <button className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-blue-500/20 text-blue-300 font-medium hover:bg-blue-500/30 transition-colors">
                      <Cloud className="w-5 h-5" />
                      Connect with Google
                    </button>

                    <p className="text-xs text-[var(--text-tertiary)] text-center">
                      We only index file metadata. Content is fetched on-demand and never stored
                      permanently.
                    </p>
                  </div>
                )}

                <div className="flex justify-end mt-6">
                  <button
                    onClick={() => setShowDriveConfig(false)}
                    className="px-4 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:bg-white/5"
                  >
                    Close
                  </button>
                </div>
              </GlassCard>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Export Modal */}
      <AnimatePresence>
        {showExportModal && selectedFile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setShowExportModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <GlassCard padding="lg">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                    Export to Google Drive
                  </h2>
                  <button
                    onClick={() => setShowExportModal(false)}
                    className="p-1 rounded hover:bg-white/10"
                  >
                    <X className="w-5 h-5 text-[var(--text-secondary)]" />
                  </button>
                </div>

                <div className="space-y-4">
                  {/* File info */}
                  <div className="p-4 rounded-lg bg-white/5">
                    <p className="text-sm text-[var(--text-primary)] font-medium">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-[var(--text-tertiary)] mt-1">
                      {formatBytes(selectedFile.size_bytes)} • {selectedFile.category}
                    </p>
                  </div>

                  {/* Destination folder */}
                  <div>
                    <label className="text-sm text-[var(--text-secondary)] mb-2 block">
                      Destination folder
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Choose a folder..."
                        className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)]"
                      />
                      <button className="px-3 py-2 rounded-lg bg-white/5 text-[var(--text-secondary)] hover:bg-white/10">
                        <FolderPlus className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Rename option */}
                  <div>
                    <label className="text-sm text-[var(--text-secondary)] mb-2 block">
                      File name (optional)
                    </label>
                    <input
                      type="text"
                      defaultValue={selectedFile.name}
                      className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-[var(--text-primary)]"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6">
                  <button
                    onClick={() => setShowExportModal(false)}
                    className="px-4 py-2 rounded-lg text-sm text-[var(--text-secondary)] hover:bg-white/5"
                  >
                    Cancel
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/20 text-blue-300 text-sm font-medium hover:bg-blue-500/30">
                    <ExternalLink className="w-4 h-4" />
                    Export
                  </button>
                </div>
              </GlassCard>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* File Preview Modal */}
      <AnimatePresence>
        {previewFile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setPreviewFile(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="w-full max-w-2xl max-h-[80vh] overflow-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <GlassCard padding="lg">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-lg font-semibold text-[var(--text-primary)]">
                      {previewFile.name}
                    </h2>
                    <p className="text-sm text-[var(--text-tertiary)]">
                      {formatBytes(previewFile.size_bytes)} • {previewFile.mime_type}
                    </p>
                  </div>
                  <button
                    onClick={() => setPreviewFile(null)}
                    className="p-1 rounded hover:bg-white/10"
                  >
                    <X className="w-5 h-5 text-[var(--text-secondary)]" />
                  </button>
                </div>

                {/* File details */}
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-[var(--text-tertiary)]">Category</p>
                      <p className="text-sm text-[var(--text-primary)] capitalize">
                        {previewFile.category}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-[var(--text-tertiary)]">Location</p>
                      <p className="text-sm text-[var(--text-primary)]">
                        {previewFile.location === 'internal' ? 'Internal Storage' : 'Google Drive'}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-[var(--text-tertiary)]">Created</p>
                      <p className="text-sm text-[var(--text-primary)]">
                        {new Date(previewFile.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-[var(--text-tertiary)]">Modified</p>
                      <p className="text-sm text-[var(--text-primary)]">
                        {new Date(previewFile.modified_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  {previewFile.description && (
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-[var(--text-tertiary)] mb-1">Description</p>
                      <p className="text-sm text-[var(--text-primary)]">{previewFile.description}</p>
                    </div>
                  )}

                  {previewFile.tags && previewFile.tags.length > 0 && (
                    <div className="p-3 rounded-lg bg-white/5">
                      <p className="text-xs text-[var(--text-tertiary)] mb-2">Tags</p>
                      <div className="flex flex-wrap gap-2">
                        {previewFile.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-1 rounded bg-purple-500/20 text-purple-300 text-xs"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 mt-6">
                  {previewFile.location === 'internal' && (
                    <button
                      onClick={() => {
                        setPreviewFile(null);
                        handleFileExport(previewFile);
                      }}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/20 text-blue-300 text-sm hover:bg-blue-500/30"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Export to Drive
                    </button>
                  )}
                  <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 text-sm hover:bg-purple-500/30">
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                </div>
              </GlassCard>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Files;
