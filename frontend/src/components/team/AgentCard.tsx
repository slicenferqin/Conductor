import { AtSign, FileText } from 'lucide-react';
import type { TeamMember } from '../../types';
import { StatusIndicator, StatusBadge } from './StatusIndicator';

interface AgentCardProps {
  member: TeamMember;
  isSelected?: boolean;
  onMention?: (member: TeamMember) => void;
  onViewFiles?: (member: TeamMember) => void;
  onClick?: (member: TeamMember) => void;
}

export function AgentCard({
  member,
  isSelected,
  onMention,
  onViewFiles,
  onClick,
}: AgentCardProps) {
  const { role, status, currentAction, progress, errorMessage } = member;

  return (
    <div
      className={`
        relative rounded-xl p-4 cursor-pointer transition-all duration-200 group
        ${isSelected
          ? 'bg-surface-highlight border border-primary/30 shadow-lg shadow-primary/5'
          : 'bg-surface/50 border border-white/5 hover:bg-surface-highlight hover:border-white/10'
        }
      `}
      onClick={() => onClick?.(member)}
    >
      {/* Header: Avatar + Name + Status */}
      <div className="flex items-center gap-3 mb-3">
        <div className={`
          w-10 h-10 rounded-xl flex items-center justify-center text-xl transition-all duration-300
          ${status === 'WORKING'
            ? 'bg-primary/20 text-primary ring-2 ring-primary/20'
            : 'bg-surface-highlight text-text-secondary'
          }
        `}>
          {role.emoji}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className={`font-medium truncate transition-colors ${isSelected ? 'text-primary' : 'text-text-primary'}`}>{role.name}</h3>
          <StatusBadge status={status} />
        </div>
        {status === 'WORKING' && (
             <div className="animate-pulse-slow">
                <StatusIndicator status={status} size="sm" />
             </div>
        )}
      </div>

      {/* Current Action / Status Detail */}
      <div className="min-h-[48px] mb-3">
        {status === 'WORKING' && currentAction && (
          <div className="space-y-2">
            <p className="text-xs text-text-secondary truncate">{currentAction}</p>
            {progress !== undefined && (
              <div className="space-y-1">
                <div className="h-1 bg-surface-highlight rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {status === 'WAITING' && currentAction && (
          <p className="text-xs text-warning/80">{currentAction}</p>
        )}

        {status === 'ERROR' && errorMessage && (
          <p className="text-xs text-error">{errorMessage}</p>
        )}

        {status === 'ONLINE' && (
          <p className="text-xs text-text-muted">等待任务分配...</p>
        )}

        {status === 'OFFLINE' && (
          <p className="text-xs text-text-muted">离线</p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-1 pt-3 border-t border-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        <button
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-[10px] font-medium text-text-muted hover:text-primary hover:bg-primary/10 transition-all uppercase tracking-wide"
          onClick={(e) => {
            e.stopPropagation();
            onMention?.(member);
          }}
        >
          <AtSign size={10} />
          提及
        </button>
        <button
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-[10px] font-medium text-text-muted hover:text-primary hover:bg-primary/10 transition-all uppercase tracking-wide"
          onClick={(e) => {
            e.stopPropagation();
            onViewFiles?.(member);
          }}
        >
          <FileText size={10} />
          文件
        </button>
      </div>
    </div>
  );
}
