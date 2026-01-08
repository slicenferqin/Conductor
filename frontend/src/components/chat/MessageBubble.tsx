import { FileCode, Bot, Terminal, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
  onMentionClick?: (mention: string) => void;
}

export function MessageBubble({ message, onMentionClick }: MessageBubbleProps) {
  const { fromName, content, attachments, timestamp, type } = message;

  const time = new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });

  // Pre-process content to turn @mentions into special links
  // regex: find @Name, replace with [@Name](mention://Name)
  const processedContent = content.replace(
      /@([\u4e00-\u9fff\w]+)/g, 
      '[@$1](mention://$1)'
  );

  const MarkdownComponents = {
      // Custom renderer for links to handle mentions
      a: ({ href, children, ...props }: any) => {
          if (href?.startsWith('mention://')) {
              const mentionName = href.replace('mention://', '');
              return (
                  <button
                      className="text-primary hover:text-primary-hover font-medium hover:underline bg-primary/10 px-1 rounded mx-0.5 transition-colors inline-block"
                      onClick={(e) => {
                          e.preventDefault();
                          onMentionClick?.(mentionName);
                      }}
                  >
                      {children}
                  </button>
              );
          }
          return (
              <a 
                href={href} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-blue-400 hover:text-blue-300 underline decoration-blue-400/30 hover:decoration-blue-300" 
                {...props}
              >
                  {children}
              </a>
          );
      },
      p: ({ children }: any) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
      ul: ({ children }: any) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
      ol: ({ children }: any) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
      li: ({ children }: any) => <li className="text-text-secondary/90">{children}</li>,
      code: ({ inline, className, children, ...props }: any) => {
          if (inline) {
              return <code className="bg-surface-highlight/50 px-1.5 py-0.5 rounded text-xs font-mono text-primary/90 border border-white/5" {...props}>{children}</code>;
          }
          return (
              <div className="relative group my-2">
                  <pre className="bg-surface-highlight/30 p-3 rounded-lg overflow-x-auto border border-white/5 text-xs font-mono scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                      <code className={className} {...props}>{children}</code>
                  </pre>
              </div>
          );
      },
      blockquote: ({ children }: any) => (
          <blockquote className="border-l-2 border-primary/30 pl-3 py-1 my-2 text-text-muted italic bg-primary/5 rounded-r">
              {children}
          </blockquote>
      ),
      h1: ({ children }: any) => <h1 className="text-lg font-bold mb-2 text-text-primary mt-4 first:mt-0">{children}</h1>,
      h2: ({ children }: any) => <h2 className="text-base font-bold mb-2 text-text-primary mt-3 first:mt-0">{children}</h2>,
      h3: ({ children }: any) => <h3 className="text-sm font-bold mb-1 text-text-primary mt-2 first:mt-0">{children}</h3>,
      strong: ({ children }: any) => <strong className="font-semibold text-text-primary">{children}</strong>,
  };

  // User message
  if (type === 'user') {
    return (
      <div className="flex justify-end animate-enter group mb-6">
        <div className="max-w-[80%] flex flex-col items-end">
           <div className="bg-primary text-white rounded-2xl rounded-tr-sm px-5 py-3 shadow-md shadow-primary/10">
              <div className="text-sm whitespace-pre-wrap">{content}</div>
           </div>
           <span className="text-xs text-text-muted mt-1 opacity-0 group-hover:opacity-100 transition-opacity">{time}</span>
        </div>
      </div>
    );
  }

  // System message
  if (type === 'system') {
    return (
      <div className="flex justify-center animate-enter py-4 mb-2">
        <div className="bg-surface-highlight/50 border border-white/5 rounded-full px-4 py-1.5 flex items-center gap-2 backdrop-blur-sm">
          <Sparkles size={14} className="text-primary" />
          <p className="text-xs text-text-secondary font-medium">{content.split('\n')[0]}</p>
        </div>
      </div>
    );
  }

  // Progress message
  if (type === 'progress') {
    return (
      <div className="flex animate-enter pl-4 border-l-2 border-surface-highlight ml-4 py-1 relative">
         {/* Vertical line connector helper */}
         <div className="absolute left-[-2px] top-[-8px] bottom-[-8px] w-[2px] bg-surface-highlight/50 -z-10" />
         
         <div className="flex items-start gap-3 w-full">
             <div className="mt-0.5 flex-shrink-0">
                 <Terminal size={14} className="text-text-muted" />
             </div>
             <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-text-secondary truncate">{fromName}</span>
                    <span className="text-[10px] text-text-muted flex-shrink-0">{time}</span>
                </div>
                <p className="text-sm text-text-secondary mt-0.5 font-mono truncate">{content}</p>
             </div>
         </div>
      </div>
    );
  }

  // Agent message
  return (
    <div className="flex animate-enter group mb-6">
      <div className="flex items-start gap-3 max-w-[85%]">
        {/* Avatar */}
        <div className="w-8 h-8 rounded-lg bg-surface-highlight flex items-center justify-center flex-shrink-0 border border-white/5 shadow-sm mt-1">
           <Bot size={18} className="text-primary" />
        </div>

        <div className="flex flex-col min-w-0">
            <div className="flex items-baseline gap-2 mb-1.5">
                <span className="text-sm font-semibold text-text-primary">{fromName}</span>
                <span className="text-xs text-text-muted">{time}</span>
            </div>

            <div className="bg-surface-highlight/40 border border-white/5 rounded-2xl rounded-tl-sm px-5 py-4 backdrop-blur-sm shadow-sm hover:border-white/10 transition-colors">
                <div className="text-text-secondary text-sm markdown-content">
                    <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={MarkdownComponents}
                    >
                        {processedContent}
                    </ReactMarkdown>
                </div>

                {/* Attachments */}
                {attachments.length > 0 && (
                <div className="mt-4 pt-3 border-t border-white/5 space-y-2">
                    {attachments.map((file, i) => (
                    <div
                        key={i}
                        className="flex items-center gap-2 text-sm text-primary hover:text-primary-hover cursor-pointer transition-colors p-2 hover:bg-white/5 rounded-lg border border-transparent hover:border-white/5"
                    >
                        <FileCode size={16} />
                        <span className="font-medium">{file}</span>
                    </div>
                    ))}
                </div>
                )}
            </div>
        </div>
      </div>
    </div>
  );
}
