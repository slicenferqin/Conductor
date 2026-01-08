import { Users, Activity, Zap } from 'lucide-react';
import type { TeamMember } from '../../types';
import { AgentCard } from './AgentCard';

interface TeamPanelProps {
  team: TeamMember[];
  selectedAgentId?: string;
  onMention?: (member: TeamMember) => void;
  onSelectAgent?: (member: TeamMember) => void;
}

export function TeamPanel({
  team,
  selectedAgentId,
  onMention,
  onSelectAgent,
}: TeamPanelProps) {
  const workingCount = team.filter((m) => m.status === 'WORKING').length;
  const onlineCount = team.filter((m) => m.status === 'ONLINE' || m.status === 'WORKING').length;
  const totalCount = team.length;

  return (
    <div className="flex flex-col h-full bg-surface/30">
      {/* Header */}
      <div className="p-6 border-b border-white/5">
        <div className="flex items-center justify-between mb-6">
           <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
             <Users size={18} className="text-primary" />
             团队成员
           </h2>
           <div className="text-xs font-medium px-2 py-1 rounded-full bg-white/5 text-text-muted border border-white/5">
              {onlineCount}/{totalCount} 在线
           </div>
        </div>

        {/* Status Summary */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-surface-highlight/50 rounded-xl p-3 border border-white/5 flex flex-col items-center justify-center">
             <div className="text-2xl font-bold text-primary mb-1">{workingCount}</div>
             <div className="text-xs text-text-muted flex items-center gap-1">
                <Activity size={10} /> 工作中
             </div>
          </div>
          <div className="bg-surface-highlight/50 rounded-xl p-3 border border-white/5 flex flex-col items-center justify-center">
             <div className="text-2xl font-bold text-success mb-1">{onlineCount - workingCount}</div>
             <div className="text-xs text-text-muted flex items-center gap-1">
                <Zap size={10} /> 待命
             </div>
          </div>
        </div>
      </div>

      {/* Agent List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {team.map((member) => (
          <AgentCard
            key={member.id}
            member={member}
            isSelected={member.id === selectedAgentId}
            onMention={onMention}
            onClick={onSelectAgent}
          />
        ))}
      </div>
    </div>
  );
}
