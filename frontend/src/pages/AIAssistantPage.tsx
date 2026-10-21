import React, { useState } from 'react';
import { Bot, Sparkles, Database, FileText, ArrowRight } from 'lucide-react';
import { ChatPanel } from '../components/ChatPanel';
import { chatService } from '../services/api';
import { ChatMessage, ChatResponse } from '../types';

export const AIAssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const activeRequestIdRef = React.useRef(0);

  const handleSendMessage = async (query: string) => {
    const currentRequestId = ++activeRequestIdRef.current;
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
        conversation_history: messages.slice(-6), // Send bounded recent conversation
      });

      if (activeRequestIdRef.current !== currentRequestId) return;

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: res.answer || "No verified platform records were found matching this inquiry.",
        sources: res.sources,
        retrieval_metadata: res.retrieval_metadata,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setLastResponse(res);
    } catch (err: any) {
      if (activeRequestIdRef.current !== currentRequestId) return;
      const detail = err?.response?.data?.detail;
      const errorMsg: ChatMessage = {
        role: 'assistant',
        content: detail
          ? `Conservation Assistant: ${detail}`
          : "Unable to reach the conservation assistant service or backend platform. Please verify your connection or check that the backend service is operational.",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      if (activeRequestIdRef.current === currentRequestId) {
        setLoading(false);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-stone-300">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
              <Bot className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-mono font-bold tracking-tight text-stone-900 uppercase">
              AI Conservation Assistant
            </h1>
          </div>
          <p className="text-xs text-stone-600 font-sans">
            Multi-source Retrieval-Augmented Generation (RAG) assistant grounded in verified PostgreSQL telemetry and indexed research documents.
          </p>
        </div>

        {/* Quick telemetry indicators */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-stone-200/80 border border-stone-300 text-stone-700">
            <Database className="w-3.5 h-3.5 text-emerald-700" />
            <span>392 Species · 46.2k Obs</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-stone-200/80 border border-stone-300 text-stone-700">
            <FileText className="w-3.5 h-3.5 text-amber-700" />
            <span>Dense Embeddings (384-d)</span>
          </div>
        </div>
      </div>

      {/* Main Chat Interface Container */}
      <div className="bg-[#171613] rounded-lg border border-stone-800 shadow-xl overflow-hidden flex flex-col h-[700px]">
        <ChatPanel
          messages={messages}
          loading={loading}
          onSendMessage={handleSendMessage}
          isCompact={false}
        />
      </div>

      {/* Grounding & Ethics Governance Note */}
      <div className="p-4 rounded-lg bg-stone-100 border border-stone-300 text-stone-700 text-xs leading-relaxed flex items-start gap-3">
        <Sparkles className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold font-mono text-[11px] uppercase tracking-wider text-stone-900 block mb-1">
            Institutional RAG Grounding & Scientific Integrity Standard
          </span>
          <p>
            All responses are synthesized exclusively from verified PostgreSQL database records (species taxonomy, official IUCN statuses, georeferenced observation bounds) and 384-dimensional vector embeddings of stored field reports. Predictive ML risk scores are explicitly demarcated and never conflated with official IUCN extinction determinations. When platform evidence is silent or insufficient, responses are qualified rather than extrapolated.
          </p>
        </div>
      </div>
    </div>
  );
};
