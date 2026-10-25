"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Upload, FileText, ChevronRight, MessageSquare, Sparkles, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function Home() {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 md:p-24 relative overflow-hidden bg-[#f8fafc]">
      
      {/* Background Decorative Soft Blooms */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-200/40 rounded-full blur-[110px] -z-10 animate-float" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-200/40 rounded-full blur-[110px] -z-10 animate-float" style={{ animationDelay: "3s" }} />

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="z-10 flex flex-col items-center text-center max-w-4xl w-full"
      >
        <motion.div 
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="mb-6 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-slate-200 shadow-xs text-primary-700 text-xs sm:text-sm font-semibold"
        >
          <Sparkles className="w-4 h-4 text-primary-600" />
          <span>Vitty AI • Document Intelligence & CA Workflow Engine</span>
        </motion.div>

        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 text-slate-900">
          Chat with your <br className="hidden md:block" />
          <span className="text-gradient">Documents</span> Instantly.
        </h1>
        
        <p className="text-lg md:text-xl text-slate-600 mb-12 max-w-2xl leading-relaxed">
          Secure, private, and lightning-fast. Upload your financial statements, tax reports, and invoices. Let local AI models extract insights and verify discrepancies with precision.
        </p>

        <div className="flex flex-col sm:flex-row gap-5 w-full max-w-2xl mx-auto">
          <Link href="/documents" className="w-full">
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onHoverStart={() => setIsHovered(true)}
              onHoverEnd={() => setIsHovered(false)}
              className="group relative flex items-center justify-center gap-3 w-full bg-primary-600 hover:bg-primary-500 text-white px-8 py-4 rounded-xl font-semibold shadow-md shadow-primary-500/25 transition-all overflow-hidden cursor-pointer"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
              <Upload className="w-5 h-5" />
              <span>Get Started</span>
              <motion.div
                animate={{ x: isHovered ? 4 : 0 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <ChevronRight className="w-5 h-5" />
              </motion.div>
            </motion.div>
          </Link>

          <Link href="/workflows" className="w-full">
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="group relative flex items-center justify-center gap-3 w-full bg-white hover:bg-slate-50 text-slate-800 px-8 py-4 rounded-xl font-semibold border border-slate-200 shadow-xs transition-all overflow-hidden cursor-pointer"
            >
              <FileText className="w-5 h-5 text-primary-600" />
              <span>Invoice Verification</span>
            </motion.div>
          </Link>
        </div>

      </motion.div>

      {/* Feature Grid */}
      <motion.div 
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6, duration: 0.8 }}
        className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl z-10"
      >
        <div className="glass-card p-8 flex flex-col items-start text-left glass-hover">
          <div className="w-12 h-12 rounded-xl bg-primary-50 border border-primary-100 flex items-center justify-center mb-5 text-primary-600 shadow-2xs">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold mb-2 text-slate-900">Smart Ingestion</h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            Upload PDFs or text files. Our engine automatically parses tables, chunks text intelligently, and stores dense vector embeddings.
          </p>
        </div>

        <div className="glass-card p-8 flex flex-col items-start text-left glass-hover">
          <div className="w-12 h-12 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center mb-5 text-purple-600 shadow-2xs">
            <MessageSquare className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold mb-2 text-slate-900">Contextual RAG Chat</h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            Ask complex accounting and audit questions. The AI retrieves semantic chunks and generates concise answers with exact citations.
          </p>
        </div>
      </motion.div>
    </main>
  );
}
