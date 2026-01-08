import type { AgentStatus } from '../../types';

interface StatusIndicatorProps {
  status: AgentStatus;
  size?: 'sm' | 'md' | 'lg';
}

const statusConfig: Record<AgentStatus, { color: string; ring: string; label: string }> = {
  ONLINE: { color: 'bg-success', ring: 'ring-success/30', label: '在线' },
  WORKING: { color: 'bg-primary', ring: 'ring-primary/30', label: '工作中' },
  WAITING: { color: 'bg-warning', ring: 'ring-warning/30', label: '等待中' },
  OFFLINE: { color: 'bg-text-muted', ring: '', label: '离线' },
  ERROR: { color: 'bg-error', ring: 'ring-error/30', label: '错误' },
};

const sizeConfig = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-2.5 h-2.5',
};

export function StatusIndicator({ status, size = 'md' }: StatusIndicatorProps) {
  const config = statusConfig[status];
  const sizeClass = sizeConfig[size];

  return (
    <span
      className={`
        inline-block rounded-full ${config.color} ${sizeClass}
        ${status === 'WORKING' ? 'shadow-[0_0_8px_rgba(139,92,246,0.5)]' : ''}
      `}
      title={config.label}
    />
  );
}

export function StatusBadge({ status }: { status: AgentStatus }) {
  const config = statusConfig[status];

  const textColor = {
    ONLINE: 'text-success',
    WORKING: 'text-primary',
    WAITING: 'text-warning',
    OFFLINE: 'text-text-muted',
    ERROR: 'text-error',
  };

  return (
    <span className={`flex items-center gap-1.5 text-xs font-medium ${textColor[status]}`}>
      <StatusIndicator status={status} size="sm" />
      <span>{config.label}</span>
    </span>
  );
}
