import React, { useState } from 'react';
import {
  Bot,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Database,
  FileText,
  Globe,
  Sparkles,
  Info,
  Clock
} from 'lucide-react';
import { ChatMessage, ChatSourceItem } from '../types';

interface ChatPanelProps {
  messages: ChatMessage[];
  loading: boolean;
  onSendMessage: (query: string) => void;
  suggestedQuestions?: string[];
  placeholder?: string;
  isCompact?: boolean;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  loading,
  onSendMessage,
  suggestedQuestions = [
    "Which mammals have the fewest observation records?",
    "Summarize the retrieved evidence about elephant habitat threats.",
    "Which species have the highest platform-generated risk scores?",
    "What do the uploaded research documents say about amphibian conservation?"
  ],
  placeholder = "Ask a question about species observations, threats, ML risk scores, or research documents...",
  isCompact = false
}) => {
  const [input, setInput] = useState('');
  const [expandedSourceMsgIndex, setExpandedSourceMsgIndex] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  React.useEffect(() => {
    let timer: any = null;
    if (loading) {
      setElapsedSeconds(0);
      timer = setInterval(() => {
        setElapsedSeconds((s) => s + 1);
      }, 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = input.trim();
    if (!clean || loading) return;
    setInput('');
    onSendMessage(clean);
  };

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'DATABASE':
        return <Database className="w-3.5 h-3.5 text-emerald-400" />;
      case 'DOCUMENT':
        return <FileText className="w-3.5 h-3.5 text-amber-400" />;
      case 'EXTERNAL':
        return <Globe className="w-3.5 h-3.5 text-blue-400" />;
      default:
        return <Database className="w-3.5 h-3.5 text-stone-400" />;
    }
  };

  return (
    <div className={`flex flex-col h-full ${isCompact ? 'text-xs' : 'text-sm'}`}>
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="py-6 px-4 text-center">
            <div className="inline-flex p-3 rounded-full bg-emerald-950/40 border border-emerald-800/50 mb-3">
              <Bot className="w-6 h-6 text-emerald-400" />
            </div>
            <h3 className="font-mono text-sm font-semibold tracking-wider text-stone-200 uppercase mb-1">
              RAG Conservation Intelligence Assistant
            </h3>
            <p className="text-xs text-stone-400 max-w-md mx-auto mb-6 leading-relaxed">
              Synthesizes verified platform evidence across 392 Indian wildlife species, 46,000+ georeferenced observations, ML extinction risk models, and indexed research documents.
            </p>

            {/* Suggested Queries */}
            <div className="text-left max-w-lg mx-auto">
              <div className="flex items-center gap-1.5 mb-2 text-[11px] font-mono font-semibold tracking-wider uppercase text-emerald-400/90">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Suggested Intelligence Inquiries</span>
              </div>
              <div className="grid gap-2">
                {suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => onSendMessage(q)}
                    className="w-full text-left p-2.5 rounded border border-stone-800 bg-stone-900/60 hover:bg-stone-800/80 hover:border-emerald-700/60 text-stone-300 hover:text-white transition-all text-xs flex items-center justify-between group"
                  >
                    <span>{q}</span>
                    <span className="text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity font-mono text-[10px]">Ask →</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[88%] rounded-lg p-3.5 leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-emerald-800 text-white font-medium rounded-br-none'
                    : 'bg-[#1e1c18] border border-stone-800 text-stone-200 rounded-bl-none shadow-md'
                }`}
              >
                {/* Role header for assistant */}
                {msg.role === 'assistant' && (
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-stone-800 text-[10px] font-mono text-stone-400">
                    <div className="flex items-center gap-1.5">
                      <Bot className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="font-semibold text-emerald-400">Grounded Wildlife Assistant</span>
                    </div>
                    {msg.retrieval_metadata && (
                      <span className="text-stone-400">
                        {msg.retrieval_metadata.llm_provider} ({msg.retrieval_metadata.retrieval_time_ms + msg.retrieval_metadata.generation_time_ms}ms)
                      </span>
                    )}
                  </div>
                )}

                {/* Message body with Markdown line breaks */}
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Grounding Source Citations Drawer */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-stone-800">
                    <button
                      type="button"
                      onClick={() => setExpandedSourceMsgIndex(expandedSourceMsgIndex === idx ? null : idx)}
                      className="flex items-center justify-between w-full text-[11px] font-mono text-emerald-400 hover:text-emerald-300 py-1"
                    >
                      <span className="flex items-center gap-1.5 font-semibold">
                        <Info className="w-3 h-3" />
                        Verified Sources & Citations ({msg.sources.length})
                      </span>
                      {expandedSourceMsgIndex === idx ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {expandedSourceMsgIndex === idx && (
                      <div className="mt-2 space-y-2 pt-1">
                        {msg.sources.map((s, sIdx) => (
                          <div
                            key={sIdx}
                            className="p-2.5 rounded bg-stone-900/90 border border-stone-800/80 text-xs"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <div className="flex items-center gap-1.5">
                                <span className="font-mono font-bold text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                                  {s.id}
                                </span>
                                {getSourceIcon(s.source_type)}
                                <span className="font-semibold text-stone-200 truncate max-w-[200px]">
                                  {s.title}
                                </span>
                              </div>
                              <span className="text-[10px] font-mono text-stone-400">
                                Rel: {(s.relevance_score * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-[11px] text-stone-400 italic line-clamp-3 mb-1">
                              "{s.snippet}"
                            </p>
                            {s.reference && (
                              <div className="flex justify-end">
                                <span className="text-[10px] font-mono text-emerald-400/80">
                                  Ref: {s.reference}
                                </span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading Spinner */}
        {loading && (
          <div className="flex items-center gap-2.5 text-stone-300 p-3 bg-[#1e1c18] border border-stone-800 rounded-lg max-w-sm text-xs font-mono shadow-md">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping shrink-0" />
            <div className="flex flex-col">
              <span className="text-emerald-400 font-semibold">Retrieving platform evidence...</span>
              <span className="text-[10px] text-stone-400">
                {elapsedSeconds > 0 ? `Elapsed: ${elapsedSeconds}s · Searching PostgreSQL facts` : 'Querying database telemetry'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Input Field */}
      <div className="p-3 border-t border-stone-800 bg-[#171613]">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder={placeholder}
            className="flex-1 px-3 py-2 rounded bg-stone-900 border border-stone-700/70 text-stone-200 placeholder-stone-400 focus:outline-none focus:border-emerald-600 text-xs font-sans"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 bg-[#11682f] hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-mono text-xs font-semibold rounded uppercase tracking-wider transition-all shrink-0"
          >
            Ask
          </button>
        </form>
        <div className="flex items-center justify-between mt-2 text-[9px] font-mono text-stone-400">
          <span>Grounded in DB telemetry & research embeddings</span>
          <span>Max 2000 chars · Non-extrapolative</span>
        </div>
      </div>
    </div>
  );
};
