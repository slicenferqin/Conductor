import { Folder, FolderOpen, FileCode, FileText, ChevronRight, ChevronDown, X, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from '../../services/api';
import type { FileNode } from '../../services/api';

interface FileBrowserProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function FileBrowser({ projectId, isOpen, onClose }: FileBrowserProps) {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  // Load file list
  useEffect(() => {
    if (isOpen && projectId) {
      setLoading(true);
      api.getProjectFiles(projectId)
        .then(setFiles)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [isOpen, projectId]);

  // Load file content
  useEffect(() => {
    if (selectedFile && selectedFile.type === 'file') {
      setContentLoading(true);
      api.getFileContent(projectId, selectedFile.path)
        .then((data) => setFileContent(data.content))
        .catch((err) => setFileContent(`Error loading file: ${err.message}`))
        .finally(() => setContentLoading(false));
    } else {
      setFileContent(null);
    }
  }, [selectedFile, projectId]);

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const renderTree = (nodes: FileNode[], level = 0) => {
    return nodes.map((node) => {
      const isExpanded = expandedFolders.has(node.path);
      const isSelected = selectedFile?.path === node.path;
      
      return (
        <div key={node.path}>
          <div 
            className={`
              flex items-center gap-2 py-1.5 px-2 rounded-lg cursor-pointer transition-colors text-sm
              ${isSelected ? 'bg-primary/20 text-primary' : 'hover:bg-white/5 text-text-secondary'}
            `}
            style={{ paddingLeft: `${level * 16 + 8}px` }}
            onClick={() => {
              if (node.type === 'directory') {
                toggleFolder(node.path);
              } else {
                setSelectedFile(node);
              }
            }}
          >
            {node.type === 'directory' ? (
              <>
                {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <Folder size={16} className="text-primary/80" />
              </>
            ) : (
              <>
                <span className="w-3.5" /> {/* Indent for files without chevron */}
                {node.name.endsWith('.ts') || node.name.endsWith('.tsx') || node.name.endsWith('.py') ? (
                   <FileCode size={16} className="text-secondary" />
                ) : (
                   <FileText size={16} className="text-text-muted" />
                )}
              </>
            )}
            <span className="truncate">{node.name}</span>
          </div>
          
          {node.type === 'directory' && isExpanded && node.children && (
            <div>{renderTree(node.children, level + 1)}</div>
          )}
        </div>
      );
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-surface border border-white/10 rounded-2xl w-[900px] h-[600px] shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-surface-highlight/20">
          <div className="flex items-center gap-3">
             <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                <FolderOpen size={20} className="text-primary" />
             </div>
             <div>
                <h3 className="font-semibold text-lg text-text-primary">Project Files</h3>
                <p className="text-xs text-text-muted font-mono">{projectId}</p>
             </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg text-text-secondary hover:text-text-primary transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 flex overflow-hidden">
          {/* Sidebar: File Tree */}
          <div className="w-64 border-r border-white/10 bg-surface/50 overflow-y-auto p-3">
             {loading ? (
                <div className="flex flex-col items-center justify-center h-40 text-text-muted gap-2">
                   <Loader2 size={24} className="animate-spin text-primary" />
                   <span className="text-xs">Loading files...</span>
                </div>
             ) : files.length === 0 ? (
                <div className="text-center py-10 text-text-muted text-sm">
                   No files found
                </div>
             ) : (
                renderTree(files)
             )}
          </div>

          {/* Content: Preview */}
          <div className="flex-1 bg-[#1e1e1e] overflow-hidden flex flex-col">
            {selectedFile ? (
              <>
                 <div className="flex items-center justify-between px-4 py-2 bg-surface border-b border-white/10">
                    <div className="flex items-center gap-2 text-sm text-text-secondary">
                        <FileCode size={14} />
                        <span className="font-mono">{selectedFile.path}</span>
                    </div>
                    {selectedFile.size && (
                        <span className="text-xs text-text-muted">{(selectedFile.size / 1024).toFixed(1)} KB</span>
                    )}
                 </div>
                 <div className="flex-1 overflow-auto p-4 text-sm text-gray-300 custom-scrollbar">
                    {contentLoading ? (
                        <div className="flex items-center justify-center h-full text-text-muted gap-2">
                           <Loader2 size={24} className="animate-spin" />
                           <span>Loading content...</span>
                        </div>
                    ) : selectedFile.name.endsWith('.md') ? (
                        <div className="prose prose-invert prose-sm max-w-none
                          prose-headings:text-text-primary prose-headings:font-semibold
                          prose-h1:text-2xl prose-h1:border-b prose-h1:border-white/10 prose-h1:pb-2
                          prose-h2:text-xl prose-h2:mt-6
                          prose-h3:text-lg
                          prose-p:text-text-secondary prose-p:leading-relaxed
                          prose-a:text-primary prose-a:no-underline hover:prose-a:underline
                          prose-strong:text-text-primary prose-strong:font-semibold
                          prose-code:text-secondary prose-code:bg-surface prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs
                          prose-pre:bg-surface prose-pre:border prose-pre:border-white/10
                          prose-blockquote:border-l-primary prose-blockquote:text-text-muted
                          prose-ul:text-text-secondary prose-ol:text-text-secondary
                          prose-li:marker:text-text-muted
                          prose-table:border-collapse
                          prose-th:bg-surface prose-th:border prose-th:border-white/10 prose-th:px-3 prose-th:py-2 prose-th:text-left
                          prose-td:border prose-td:border-white/10 prose-td:px-3 prose-td:py-2
                          prose-hr:border-white/10
                        ">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {fileContent || ''}
                          </ReactMarkdown>
                        </div>
                    ) : (
                        <pre className="font-mono whitespace-pre-wrap">{fileContent}</pre>
                    )}
                 </div>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-text-muted">
                 <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
                    <FileText size={32} className="opacity-50" />
                 </div>
                 <p>Select a file to view content</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
