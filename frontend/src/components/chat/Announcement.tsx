import { Pin, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';

interface AnnouncementProps {
  content?: string;
}

export function Announcement({ content }: AnnouncementProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!content) return null;

  return (
    <div className="mx-4 mt-6 mb-4 animate-fade-in">
      <div className={`
        bg-surface-highlight/30 border border-primary/10 rounded-2xl overflow-hidden backdrop-blur-md shadow-xl
        transition-all duration-300 ease-in-out hover:bg-surface-highlight/40 hover:border-primary/20 hover:shadow-2xl
      `}>
        {/* Header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between px-5 py-4 bg-gradient-to-r from-primary/5 to-transparent hover:from-primary/10 transition-all"
        >
          <div className="flex items-center gap-3 text-primary font-semibold tracking-wide">
            <div className="p-1.5 bg-primary/10 rounded-lg">
                <Pin size={16} className="fill-primary/20" />
            </div>
            <span className="text-base">Project Goal</span>
          </div>
          {isExpanded ? (
            <ChevronUp size={18} className="text-primary/70" />
          ) : (
            <ChevronDown size={18} className="text-primary/70" />
          )}
        </button>

        {/* Content */}
        {isExpanded && (
          <div className="px-6 py-5 text-[15px] text-text-secondary leading-7 bg-surface/20">
            {content}
          </div>
        )}
      </div>
    </div>
  );
}
