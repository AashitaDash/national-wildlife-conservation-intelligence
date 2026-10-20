import React, { useState } from 'react';
import { Bot, X, MessageSquare, Maximize2 } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ChatPanel } from './ChatPanel';
import { chatService } from '../services/api';
import { ChatMessage } from '../types';

export const FloatingChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // If already on the dedicated /assistant page, hide floating launcher to prevent duplicate interfaces
  if (location.pathname === '/assistant') {
    return null;
  }

  const handleSendMessage = async (query: string) => {
    const userMsg: ChatMessage = {
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await chatService.ask({
        question: query,
        conversation_history: messages.slice(-4),
      });

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
        retrieval_metadata: res.retrieval_metadata,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content:
          "Unable to reach the conservation assistant service or backend platform. Please verify your connection or check that the backend service is operational.",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Expanded Floating Chat Panel */}
      {isOpen && (
        <div className="mb-3 w-[400px] h-[550px] bg-[#171613] rounded-xl border border-stone-800 shadow-2xl flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5 duration-200">
          {/* Header */}
          <div className="px-4 py-3 bg-[#1e1c18] border-b border-stone-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                <Bot className="w-4 h-4" />
              </span>
              <div>
                <h4 className="font-mono text-xs font-bold text-stone-200 uppercase tracking-wider">
                  Wildlife AI Assistant
                </h4>
                <span className="text-[10px] text-emerald-400 font-mono block">
                  Grounded Decision Support
                </span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  navigate('/assistant');
                }}
                title="Expand to Full Page"
                className="p-1.5 text-stone-400 hover:text-stone-200 hover:bg-stone-800 rounded transition-colors"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Close Chat"
                className="p-1.5 text-stone-400 hover:text-stone-200 hover:bg-stone-800 rounded transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Panel Content */}
          <div className="flex-1 overflow-hidden">
            <ChatPanel
              messages={messages}
              loading={loading}
              onSendMessage={handleSendMessage}
              isCompact={true}
            />
          </div>
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-3 rounded-full bg-[#11682f] hover:bg-emerald-700 text-white shadow-xl hover:shadow-2xl font-mono text-xs font-semibold tracking-wider transition-all transform hover:scale-105 border border-emerald-500/30"
      >
        {isOpen ? (
          <>
            <X className="w-4 h-4" />
            <span>CLOSE</span>
          </>
        ) : (
          <>
            <Bot className="w-4 h-4 text-emerald-200 animate-pulse" />
            <span>AI ASSISTANT</span>
          </>
        )}
      </button>
    </div>
  );
};
