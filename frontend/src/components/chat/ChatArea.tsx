import { useRef, useEffect, useState, useCallback } from 'react';
import type { Message, TeamMember } from '../../types';
import { MessageBubble } from './MessageBubble';
import { InputArea } from './InputArea';
import { Announcement } from './Announcement';
import { Sparkles, ArrowDown } from 'lucide-react';

interface ChatAreaProps {
  messages: Message[];
  team: TeamMember[];
  requirements?: string;
  onSend: (content: string, mentions: string[]) => void;
  onMentionClick?: (mention: string) => void;
  disabled?: boolean;
}

export function ChatArea({
  messages,
  team,
  requirements,
  onSend,
  onMentionClick,
  disabled,
}: ChatAreaProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [isNearBottom, setIsNearBottom] = useState(true);

  const scrollToBottom = useCallback((smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
    setShowScrollButton(false);
  }, []);

  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    // Consider "near bottom" if within 100px of bottom
    const isBottom = scrollHeight - scrollTop - clientHeight < 100;
    setIsNearBottom(isBottom);

    if (isBottom) {
      setShowScrollButton(false);
    }
  };

  // Smart Auto-scroll: Only scroll if user was already near bottom
  useEffect(() => {
    if (messages.length > 0) {
      if (isNearBottom) {
        scrollToBottom();
      } else {
        setShowScrollButton(true);
      }
    }
  }, [messages, isNearBottom, scrollToBottom]);

  return (
    <div className="flex flex-col h-full relative">
      {/* Fixed Announcement at top - outside scroll area */}
      {requirements && (
        <div className="flex-shrink-0 px-4 pt-2">
          <Announcement content={requirements} />
        </div>
      )}

      {/* Messages - scrollable area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-2 space-y-6 scroll-smooth"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-text-muted">
            <div className="text-center max-w-md">
              <div className="w-16 h-16 bg-surface-highlight rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Sparkles size={32} className="text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-text-primary mb-2">Welcome to Conductor</h3>
              <p className="text-text-secondary">Type your requirements below to start collaborating with your AI team.</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              onMentionClick={onMentionClick}
            />
          ))
        )}
        <div ref={messagesEndRef} className="h-4" />
      </div>

      {/* Floating Scroll Button */}
      {showScrollButton && (
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-20">
          <button
            onClick={() => scrollToBottom()}
            className="flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-full shadow-lg hover:bg-primary-hover transition-all animate-bounce-small text-sm font-medium"
          >
            <ArrowDown size={16} />
            New Messages
          </button>
        </div>
      )}

      {/* Input */}
      <div className="p-4 z-10">
        <InputArea team={team} onSend={onSend} disabled={disabled} />
      </div>
    </div>
  );
}
