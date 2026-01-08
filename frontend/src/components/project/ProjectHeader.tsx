import { useState } from 'react';
import { Pause, Play, Square, FolderOpen, BarChart3, Activity, Loader2 } from 'lucide-react';
import type { Project } from '../../types';

interface ProjectHeaderProps {
  project: Project;
  onPause?: () => Promise<void>;
  onResume?: () => Promise<void>;
  onStop?: () => Promise<void>;
  onOpenWorkspace?: () => void;
}

export function ProjectHeader({
  project,
  onPause,
  onResume,
  onStop,
  onOpenWorkspace,
}: ProjectHeaderProps) {
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const workingCount = project.team.filter((m) => m.status === 'WORKING').length;
  const totalCount = project.team.length;

  const handleAction = async (action: string, handler?: () => Promise<void>) => {
    if (!handler || actionLoading) return;

    setActionLoading(action);
    try {
      await handler();
    } finally {
      setActionLoading(null);
    }
  };

  const isRunning = project.status === 'RUNNING';
  const isPaused = project.status === 'PAUSED';
  const canControl = isRunning || isPaused;

  return (
    <div className="px-6 py-3 border-b border-white/10 bg-surface/30 backdrop-blur-sm z-10 flex items-center justify-between min-h-[56px] shadow-sm">
        {/* Left: Project Stats / Quick Info */}
        <div className="flex items-center gap-4">
             <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-highlight/50 border border-white/5">
                <Activity size={14} className="text-primary" />
                <span className="text-xs font-medium text-text-secondary">
                    智能体活跃度: <span className="text-text-primary">{workingCount}/{totalCount}</span>
                </span>
             </div>

             {project.lastUpdated && (
                 <div className="text-xs text-text-muted">
                    Last updated: {new Date(project.lastUpdated).toLocaleTimeString()}
                 </div>
             )}
        </div>

        {/* Right: Actions Toolbar */}
        <div className="flex items-center gap-2">
          {/* Running: Show Pause and Stop */}
          {isRunning && (
            <>
              <button
                onClick={() => handleAction('pause', onPause)}
                disabled={!!actionLoading}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium glass-panel hover:bg-warning/10 text-text-secondary hover:text-warning rounded-lg transition-all disabled:opacity-50"
              >
                {actionLoading === 'pause' ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Pause size={14} />
                )}
                暂停
              </button>
              <button
                onClick={() => handleAction('stop', onStop)}
                disabled={!!actionLoading}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium glass-panel hover:bg-error/10 text-text-secondary hover:text-error rounded-lg transition-all disabled:opacity-50"
              >
                {actionLoading === 'stop' ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Square size={14} />
                )}
                停止
              </button>
              <div className="w-px h-4 bg-white/10 mx-1" />
            </>
          )}

          {/* Paused: Show Resume and Stop */}
          {isPaused && (
            <>
              <button
                onClick={() => handleAction('resume', onResume)}
                disabled={!!actionLoading}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium glass-panel hover:bg-success/10 text-text-secondary hover:text-success rounded-lg transition-all disabled:opacity-50"
              >
                {actionLoading === 'resume' ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Play size={14} />
                )}
                恢复
              </button>
              <button
                onClick={() => handleAction('stop', onStop)}
                disabled={!!actionLoading}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium glass-panel hover:bg-error/10 text-text-secondary hover:text-error rounded-lg transition-all disabled:opacity-50"
              >
                {actionLoading === 'stop' ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Square size={14} />
                )}
                停止
              </button>
              <div className="w-px h-4 bg-white/10 mx-1" />
            </>
          )}

          <button
            onClick={onOpenWorkspace}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium glass-panel hover:bg-primary/10 text-text-secondary hover:text-primary rounded-lg transition-all"
          >
            <FolderOpen size={14} />
            工作目录
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium glass-panel hover:bg-primary/10 text-text-secondary hover:text-primary rounded-lg transition-all">
            <BarChart3 size={14} />
            进度
          </button>
        </div>
    </div>
  );
}
