import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, Sparkles, Loader2, Send, ChevronDown, ChevronRight } from "lucide-react";

export default function ChatPanel({ onAsk, isLoading, activeQuery, chatHistory, externalPrompt }) {
  const [prompt, setPrompt] = useState("");
  const [expandedSteps, setExpandedSteps] = useState({});

  useEffect(() => {
    if (externalPrompt) {
      setPrompt(externalPrompt);
    }
  }, [externalPrompt]);

  const toggleSteps = (id) => {
    setExpandedSteps(prev => ({
      ...prev,
      [id]: !(prev[id] ?? false)
    }));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.metaKey) {
      e.preventDefault();
      if (prompt.trim() && !isLoading) {
        onAsk(prompt);
        setPrompt("");
      }
    }
  };

  return (
    <Card className="h-full flex flex-col bg-neutral-900 border-neutral-800 rounded-xl overflow-hidden shadow-xl">
      <CardHeader className="border-b border-neutral-800 bg-neutral-900/50 py-3">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-indigo-400" />
          Query Assistant
        </CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 p-0 flex flex-col overflow-hidden bg-neutral-900/50">
        {/* Chat Feed */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 bg-neutral-950/60">
          
          {activeQuery && (
            <div className="bg-neutral-900/90 border border-indigo-500/30 rounded-xl p-4 flex flex-col gap-3 shadow-lg shadow-indigo-950/20">
              <div className="text-sm font-medium text-neutral-100">"{activeQuery.question}"</div>
              
              <div className="border-t border-neutral-800/80 pt-3 flex flex-col gap-2">
                <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-indigo-400">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                    <span>Live Thought Stream (SSE)</span>
                  </div>
                  <span className="text-[10px] text-neutral-400 font-mono font-normal lowercase">{activeQuery.task_id}</span>
                </div>

                <div className="flex flex-col gap-1.5 pl-2.5 border-l-2 border-indigo-500/40 ml-1.5 mt-1 max-h-40 overflow-y-auto">
                  {activeQuery.steps && activeQuery.steps.length > 0 ? (
                    activeQuery.steps.map((step, idx) => (
                      <div key={idx} className="text-xs text-neutral-300 flex items-start gap-2">
                        <span className="text-indigo-400 font-mono">›</span>
                        <span className="leading-relaxed">{step}</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-neutral-400 italic">
                      Connecting to agent event stream...
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {chatHistory.map((msg, i) => {
            const isExpanded = Boolean(expandedSteps[msg.id || i] ?? (i === 0));
            return (
              <div key={i} className="group relative bg-neutral-800/60 hover:bg-neutral-800/90 border border-neutral-800 rounded-lg p-4 transition-colors">
                <div className="text-sm font-medium text-neutral-100 mb-2">"{msg.question}"</div>
              
              <div className="flex items-center gap-2 mt-3">
                {msg.cached ? (
                  <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 text-[10px]">
                    ⚡ Cache Hit (&lt;5ms)
                  </Badge>
                ) : (
                  <Badge variant="outline" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20 text-[10px]">
                    🤖 Llama 3 Agent
                  </Badge>
                )}
                {msg.retries > 0 && (
                   <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[10px]">
                     ⚠️ Self-Corrected ({msg.retries} {msg.retries === 1 ? 'retry' : 'retries'})
                   </Badge>
                )}
              </div>

              {msg.steps && msg.steps.length > 0 && (
                <div className="mt-3 pt-2.5 border-t border-neutral-800">
                  <button
                    type="button"
                    onClick={() => toggleSteps(msg.id || i)}
                    className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-indigo-400 transition-colors py-0.5 group/btn"
                  >
                    {isExpanded ? (
                      <ChevronDown className="w-3.5 h-3.5 text-indigo-400 transition-transform" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5 text-neutral-500 group-hover/btn:text-indigo-400 transition-transform" />
                    )}
                    <span className="font-medium text-[11px] tracking-wide">
                      {isExpanded ? "Hide Reasoning Steps" : `View ${msg.steps.length} Agent Reasoning Steps`}
                    </span>
                  </button>

                  {isExpanded && (
                    <div className="mt-2 pl-2.5 border-l-2 border-indigo-500/40 flex flex-col gap-1.5 py-1">
                      {msg.steps.map((st, idx) => (
                        <div key={idx} className="text-xs text-neutral-300 flex items-start gap-2 font-mono">
                          <span className="text-emerald-400 text-[11px] font-bold">✓</span>
                          <span className="leading-relaxed">{st}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )})}
          
          {chatHistory.length === 0 && !activeQuery && (
            <div className="h-full flex flex-col items-center justify-center text-center p-6 text-neutral-500">
              <Sparkles className="w-8 h-8 mb-3 opacity-20 text-indigo-400" />
              <p className="text-sm font-medium text-neutral-300">Ask a question to generate SQL.</p>
              <p className="text-xs text-neutral-400 mt-1">Try "Who is the highest paid employee?"</p>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-neutral-950 border-t border-neutral-800">
          <div className="relative group">
            <Textarea 
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Ask a question about your data... (Cmd + Enter to submit)"
              className="w-full bg-neutral-900 border-neutral-700 text-neutral-100 placeholder:text-neutral-500 focus-visible:ring-indigo-500/50 resize-none pr-12 min-h-[80px]"
            />
            <button 
              onClick={() => { onAsk(prompt); setPrompt(""); }}
              disabled={isLoading || !prompt.trim()}
              className="absolute right-3 bottom-3 p-2 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 disabled:hover:bg-indigo-500 rounded-md transition-colors"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
