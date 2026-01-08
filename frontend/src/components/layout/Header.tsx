import { Sparkles, Settings, User } from 'lucide-react';

interface HeaderProps {
  projectName?: string;
}

export function Header({ projectName }: HeaderProps) {
  return (
    <header className="h-16 glass border-b border-purple-500/10 flex items-center justify-between px-6">
      {/* Logo */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Sparkles size={20} className="text-white" />
          </div>
          <span className="text-xl font-bold gradient-text">Conductor</span>
        </div>
        {projectName && (
          <>
            <span className="text-purple-500/30">/</span>
            <span className="text-slate-400 truncate max-w-[400px] font-medium">{projectName}</span>
          </>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        <button className="p-2.5 rounded-xl hover:bg-white/5 text-slate-400 hover:text-purple-400 transition-all">
          <Settings size={20} />
        </button>
        <button className="p-2.5 rounded-xl hover:bg-white/5 text-slate-400 hover:text-purple-400 transition-all">
          <User size={20} />
        </button>
      </div>
    </header>
  );
}
