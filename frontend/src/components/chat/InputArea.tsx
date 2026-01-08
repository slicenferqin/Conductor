import { useState, useRef, useEffect } from 'react';
import { Send, AtSign, Paperclip, Sparkles, X } from 'lucide-react';
import type { TeamMember } from '../../types';

interface InputAreaProps {
  team: TeamMember[];
  onSend: (content: string, mentions: string[]) => void;
  disabled?: boolean;
}

export function InputArea({ team, onSend, disabled }: InputAreaProps) {
  const [content, setContent] = useState('');
  const [showMentions, setShowMentions] = useState(false);
  const [mentionFilter, setMentionFilter] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const filteredTeam = team.filter((m) =>
    m.role.name.toLowerCase().includes(mentionFilter.toLowerCase())
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
    if (e.key === '@') {
      setShowMentions(true);
      setMentionFilter('');
    }
    if (e.key === 'Escape') {
      setShowMentions(false);
    }
  };

  const handleSend = () => {
    if (!content.trim() || disabled) return;

    const mentionRegex = /@([\u4e00-\u9fff\w]+)/g;
    const mentions: string[] = [];
    let match;
    while ((match = mentionRegex.exec(content)) !== null) {
      mentions.push(match[1]);
    }

    onSend(content.trim(), mentions);
    setContent('');
    setShowMentions(false);
  };

  const insertMention = (member: TeamMember) => {
    const mention = `@${member.role.name} `;
    setContent((prev) => prev + mention);
    setShowMentions(false);
    inputRef.current?.focus();
  };

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, [content]);

  return (
    <div className="relative max-w-4xl mx-auto">
      {/* Mention Dropdown */}
      {showMentions && (
        <div className="absolute bottom-full left-0 mb-2 w-64 glass-panel rounded-xl overflow-hidden shadow-2xl z-50 animate-enter">
          <div className="p-2 border-b border-white/5 flex items-center justify-between">
            <span className="text-xs font-medium text-text-muted px-2">Mention Agent</span>
            <button onClick={() => setShowMentions(false)} className="text-text-muted hover:text-text-primary">
                <X size={14} />
            </button>
          </div>
          <div className="max-h-48 overflow-y-auto p-1">
            {filteredTeam.map((member) => (
                <button
                key={member.id}
                className="w-full flex items-center gap-3 px-3 py-2 hover:bg-white/5 rounded-lg text-left transition-colors group"
                onClick={() => insertMention(member)}
                >
                <span className="text-lg bg-surface p-1 rounded-md border border-white/5">{member.role.emoji}</span>
                <div className="flex-1">
                    <div className="text-sm font-medium text-text-primary group-hover:text-primary transition-colors">{member.role.name}</div>
                    <div className="text-[10px] text-text-muted capitalize">{member.status.toLowerCase()}</div>
                </div>
                </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Container */}
      <div className="bg-surface-highlight/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-lg ring-1 ring-white/5 focus-within:ring-primary/50 focus-within:border-primary/50 transition-all duration-300">
        <textarea
            ref={inputRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask your AI team..."
            disabled={disabled}
            className="w-full bg-transparent px-5 py-4 text-text-primary placeholder-text-muted resize-none min-h-[60px] max-h-[160px] focus:outline-none"
            rows={1}
        />

        {/* Toolbar */}
        <div className="flex items-center justify-between px-3 pb-3 pt-1">
            <div className="flex items-center gap-1">
                <button
                    className="p-2 rounded-xl text-text-muted hover:text-primary hover:bg-primary/10 transition-all"
                    title="@mention"
                    onClick={() => setShowMentions(!showMentions)}
                >
                    <AtSign size={18} />
                </button>
                <button
                    className="p-2 rounded-xl text-text-muted hover:text-primary hover:bg-primary/10 transition-all"
                    title="Attach file"
                >
                    <Paperclip size={18} />
                </button>
                <div className="w-px h-4 bg-white/10 mx-2" />
                <button
                     className="text-xs flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/5 text-primary hover:bg-primary/10 transition-colors border border-primary/10"
                >
                    <Sparkles size={12} />
                    <span>Auto-Plan</span>
                </button>
            </div>

            <button
                onClick={handleSend}
                disabled={!content.trim() || disabled}
                className="p-2.5 bg-primary hover:bg-primary-hover disabled:bg-surface-highlight disabled:text-text-muted text-white rounded-xl shadow-lg shadow-primary/20 transition-all duration-200 transform active:scale-95"
            >
                <Send size={18} />
            </button>
        </div>
      </div>
    </div>
  );
}
