"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, FileText, CheckCircle, Loader2, Send, MessageSquare, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { fetchDocuments, uploadDocument, askQuestion } from "@/lib/api";

type DocumentStatus = "PENDING" | "PROCESSING" | "INDEXED" | "FAILED";

interface DocumentItem {
  id: string;
  filename: string;
  status: DocumentStatus;
}

interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
  sources?: { chunk_index: number; text_snippet: string }[];
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [query, setQuery] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const loadDocuments = async () => {
    try {
      const data = await fetchDocuments();
      setDocuments(data.items);
    } catch (err) {
      console.error("Failed to load documents", err);
    }
  };

  useEffect(() => {
    loadDocuments();
    const interval = setInterval(loadDocuments, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isTyping]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await uploadDocument(file);
      await loadDocuments();
    } catch (err) {
      alert("Failed to upload document");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMsg = query;
    setQuery("");
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setIsTyping(true);

    try {
      const res = await askQuestion(userMsg);
      setChatHistory(prev => [...prev, { role: 'ai', text: res.answer, sources: res.sources }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'ai', text: "Error connecting to AI backend." }]);
    } finally {
      setIsTyping(false);
    }
  };

  const getStatusIcon = (status: DocumentStatus) => {
    switch (status) {
      case "INDEXED": return <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />;
      case "PROCESSING":
      case "PENDING": return <Loader2 className="w-4 h-4 text-primary-600 animate-spin shrink-0" />;
      case "FAILED": return <div className="w-3.5 h-3.5 rounded-full bg-rose-500/20 border border-rose-500/60 shrink-0" />;
    }
  };

  return (
    <div className="min-h-screen p-6 md:p-12 flex flex-col md:flex-row gap-8 max-w-7xl mx-auto">
      
      {/* Left Sidebar - Documents */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-full md:w-1/3 flex flex-col gap-6"
      >
        <Link href="/" className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-900 transition-colors text-sm font-medium">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </Link>
        
        <div className="glass-card p-6 flex-1 flex flex-col shadow-sm">
          <h2 className="text-xl font-bold mb-5 text-slate-900 flex items-center gap-2">
            <FileText className="text-primary-600 w-5 h-5" />
            Knowledge Base
          </h2>

          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            className="hidden" 
            accept=".pdf,.txt" 
          />
          
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="w-full flex items-center justify-center gap-2 bg-primary-50 hover:bg-primary-100/80 border border-primary-200 text-primary-700 py-3 rounded-xl font-semibold transition-all mb-6 cursor-pointer disabled:opacity-50"
          >
            {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            <span>{isUploading ? "Uploading..." : "Upload Document"}</span>
          </button>

          <div className="flex-1 overflow-y-auto pr-1 space-y-2.5 max-h-[58vh]">
            <AnimatePresence>
              {documents.length === 0 ? (
                <div className="text-slate-400 text-center py-8 text-sm">No documents uploaded yet.</div>
              ) : (
                documents.map(doc => (
                  <motion.div 
                    key={doc.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between group hover:bg-indigo-50/40 hover:border-indigo-200 transition-all"
                  >
                    <div className="flex items-center gap-2.5 overflow-hidden">
                      {getStatusIcon(doc.status)}
                      <span className="truncate text-xs font-semibold text-slate-700">
                        {doc.filename}
                      </span>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
        </div>
      </motion.div>

      {/* Right Panel - Chat */}
      <motion.div 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="w-full md:w-2/3 glass-card flex flex-col h-[85vh] shadow-sm overflow-hidden"
      >
        <div className="p-5 border-b border-slate-100 flex items-center gap-3 bg-white/50">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-600 flex items-center justify-center text-white shadow-sm">
            <MessageSquare className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900">Vitty AI Document Assistant</h2>
            <p className="text-xs text-slate-500">Ask questions grounded in your financial & legal documents</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-[#fafbfd]">
          {chatHistory.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
                <MessageSquare className="w-6 h-6" />
              </div>
              <p className="text-sm">Ask anything about your uploaded documents.</p>
            </div>
          )}
          
          {chatHistory.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[82%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-primary-600 text-white rounded-br-xs shadow-xs' : 'bg-white border border-slate-200 text-slate-800 rounded-bl-xs shadow-xs'}`}>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>
                
                {/* Render Citations if AI */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-3.5 pt-3 border-t border-slate-100">
                    <p className="text-xs font-semibold text-primary-700 mb-2">Sources Context Used:</p>
                    <div className="flex flex-col gap-1.5">
                      {msg.sources.map((s, i) => (
                        <div key={i} className="text-[11px] bg-slate-50 border border-slate-200/70 p-2.5 rounded-lg text-slate-600 leading-snug">
                          {s.text_snippet}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 text-slate-700 p-3.5 rounded-2xl rounded-bl-xs flex items-center gap-1.5 shadow-xs">
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="p-4 border-t border-slate-100 bg-white">
          <form onSubmit={handleAsk} className="relative flex items-center">
            <input 
              type="text" 
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Ask a question about your documents..."
              className="w-full bg-slate-50 border border-slate-200 focus:bg-white focus:border-primary-500 rounded-full pl-5 pr-13 py-3 text-sm text-slate-900 outline-none transition-all placeholder:text-slate-400 shadow-2xs"
            />
            <button 
              type="submit" 
              disabled={isTyping || !query.trim()}
              className="absolute right-1.5 p-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-40 rounded-full text-white transition-all cursor-pointer shadow-xs"
            >
              <Send className="w-4 h-4 ml-0.5" />
            </button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
