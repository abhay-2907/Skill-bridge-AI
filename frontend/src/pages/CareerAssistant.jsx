import React, { useState } from 'react';
import api from '../services/api';
import {
  MessageSquare, Send, Sparkles, BookOpen, AlertCircle,
  Bot, User, ChevronRight, CheckCircle2, Shield
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CareerAssistant() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I am your CareerPilot AI Assistant. I am directly grounded in our curated technical knowledge base of backend architectures, RAG systems, and interview standards.\n\nAsk me anything about interview questions, technical concepts, or how to bridge your specific skill gaps!',
      sources: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const samplePrompts = [
    "What is the GIL in Python and how do we bypass it?",
    "Explain the RAG pipeline steps from chunking to FAISS retrieval.",
    "What are B-Tree indexes in SQL and why do they speed up queries?",
    "How should I explain my FastAPI project during an interview?"
  ];

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMsg = { role: 'user', content: text, sources: [] };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.post('/rag/chat', { message: userMsg.content });
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.data.answer,
          sources: res.data.sources || [],
          is_grounded: res.data.is_grounded
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I encountered an issue querying the vector index. Please check your backend connection and try again.',
          sources: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-7.5rem)] space-y-4">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-blue-400" />
            Grounded Career Assistant
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            RAG-powered technical chatbot citing verified knowledge base sources.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-semibold text-blue-300">
          <Shield className="h-3.5 w-3.5" /> Zero-Hallucination Threshold
        </div>
      </div>

      {/* Chat Messages Log */}
      <div className="flex-1 overflow-y-auto glass-panel rounded-3xl p-6 space-y-5 border border-white/[0.08]">
        {messages.map((m, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex items-start gap-3.5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`h-8 w-8 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
              m.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gradient-to-tr from-purple-600 to-indigo-600 text-white'
            }`}>
              {m.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>

            <div className={`max-w-2xl space-y-2`}>
              <div
                className={`p-4 rounded-2xl text-xs md:text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === 'user'
                    ? 'bg-blue-600 text-white rounded-tr-none shadow-lg shadow-blue-600/20'
                    : 'bg-[#0E1320] text-gray-200 border border-white/[0.06] rounded-tl-none shadow-md'
                }`}
              >
                {m.content}
              </div>

              {/* RAG Citations */}
              {m.sources && m.sources.length > 0 && (
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-1.5">
                  <div className="flex items-center gap-1.5 text-[11px] font-bold text-blue-400">
                    <BookOpen className="h-3.5 w-3.5" /> Retrieved Citations:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {m.sources.map((s, sIdx) => (
                      <span key={sIdx} className="text-[10px] bg-white/[0.04] border border-white/[0.08] px-2.5 py-1 rounded-md text-gray-300">
                        {s.title} ({Math.round(s.relevance_score * 100)}% match)
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-xs text-blue-400 p-2">
            <span className="h-2 w-2 rounded-full bg-blue-400 animate-ping"></span>
            Searching vector store & synthesizing answer...
          </div>
        )}
      </div>

      {/* Quick Prompts Suggestion Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider shrink-0">Try Asking:</span>
        {samplePrompts.map((p, i) => (
          <button
            key={i}
            onClick={() => handleSend(p)}
            className="px-3 py-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] text-gray-400 hover:text-white border border-white/[0.06] whitespace-nowrap transition text-xs"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2">
        <input
          type="text"
          placeholder="Ask a technical or career query..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-[#0E1320] border border-white/[0.08] rounded-2xl px-5 py-3.5 text-xs md:text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 shadow-inner"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="px-6 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 text-white font-bold text-xs flex items-center justify-center gap-2 transition shadow-lg shadow-blue-500/20"
        >
          <Send className="h-4 w-4" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </form>
    </div>
  );
}
