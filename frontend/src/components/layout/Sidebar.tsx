import { Plus, FolderOpen, Sparkles, CheckCircle, Loader2, Clock, XCircle, LayoutGrid } from 'lucide-react';
import type { Project } from '../../types';

interface SidebarProps {
  projects: Project[];
  currentProjectId: string | null;
  onSelectProject: (projectId: string) => void;
  onNewProject: () => void;
}

const statusConfig: Record<Project['status'], { icon: React.ReactNode; color: string }> = {
  PLANNING: { icon: <Clock size={14} />, color: 'text-warning' },
  FORMING: { icon: <Loader2 size={14} className="animate-spin" />, color: 'text-primary' },
  RUNNING: { icon: <Loader2 size={14} className="animate-spin" />, color: 'text-secondary' },
  PAUSED: { icon: <Clock size={14} />, color: 'text-warning' },
  COMPLETED: { icon: <CheckCircle size={14} />, color: 'text-success' },
  FAILED: { icon: <XCircle size={14} />, color: 'text-error' },
};

export function Sidebar({
  projects,
  currentProjectId,
  onSelectProject,
  onNewProject,
}: SidebarProps) {
  const activeProjects = projects.filter((p) =>
    ['PLANNING', 'FORMING', 'RUNNING', 'PAUSED'].includes(p.status)
  );
  const completedProjects = projects.filter((p) =>
    ['COMPLETED', 'FAILED'].includes(p.status)
  );

  return (
    <aside className="h-full w-64 flex flex-col glass-panel rounded-2xl overflow-hidden">
      {/* Brand */}
      <div className="h-16 flex items-center px-6 border-b border-white/5">
        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center mr-3">
            <Sparkles size={18} className="text-primary" />
        </div>
        <span className="font-bold text-lg tracking-tight">Conductor</span>
      </div>

      {/* Projects List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-6">
        {/* Actions */}
        <button
          onClick={onNewProject}
          className="w-full flex items-center justify-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 hover:border-primary/30 rounded-xl px-4 py-2.5 font-medium transition-all duration-200"
        >
          <Plus size={16} />
          <span>新建项目</span>
        </button>

        {/* Active Projects */}
        <div>
          <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3 px-2 flex items-center gap-2">
            <LayoutGrid size={12} />
            进行中
          </h3>
          {activeProjects.length === 0 ? (
            <p className="text-sm text-text-muted px-2 py-2 text-center italic">暂无活跃项目</p>
          ) : (
            <div className="space-y-1">
              {activeProjects.map((project) => (
                <ProjectItem
                  key={project.id}
                  project={project}
                  isSelected={project.id === currentProjectId}
                  onClick={() => onSelectProject(project.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Completed Projects */}
        {completedProjects.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3 px-2 flex items-center gap-2">
              <CheckCircle size={12} />
              已完成
            </h3>
            <div className="space-y-1">
              {completedProjects.map((project) => (
                <ProjectItem
                  key={project.id}
                  project={project}
                  isSelected={project.id === currentProjectId}
                  onClick={() => onSelectProject(project.id)}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-white/5 bg-black/20">
        <button className="w-full flex items-center gap-3 text-sm text-text-secondary hover:text-text-primary px-3 py-2.5 rounded-xl hover:bg-white/5 transition-all">
          <FolderOpen size={16} />
          <span>工作空间</span>
        </button>
      </div>
    </aside>
  );
}

function ProjectItem({
  project,
  isSelected,
  onClick,
}: {
  project: Project;
  isSelected: boolean;
  onClick: () => void;
}) {
  const config = statusConfig[project.status];

  return (
    <button
      onClick={onClick}
      className={`
        w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-200 group
        ${isSelected
          ? 'bg-surface-highlight text-text-primary shadow-sm ring-1 ring-white/5'
          : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'
        }
      `}
    >
      <span className={`${config.color} opacity-80 group-hover:opacity-100 transition-opacity`}>{config.icon}</span>
      <span className="flex-1 truncate text-sm font-medium">{project.name}</span>
    </button>
  );
}
