import React, { useState, useEffect, useRef } from 'react'
import { submitQuery, pollTaskStatus, subscribeTaskEvents } from './api/client'
import { TooltipProvider } from "@/components/ui/tooltip"

import SchemaPanel from './components/SchemaPanel'
import ChatPanel from './components/ChatPanel'
import ResultsPanel from './components/ResultsPanel'

const DEFAULT_SCHEMA = `CREATE TABLE departments (
  id INT PRIMARY KEY,
  name VARCHAR,
  budget INT,
  location VARCHAR
);

CREATE TABLE employees (
  id INT PRIMARY KEY,
  name VARCHAR,
  department VARCHAR,
  department_id INT,
  role VARCHAR,
  salary INT,
  hire_date DATE
);

CREATE TABLE customers (
  id INT PRIMARY KEY,
  name VARCHAR,
  email VARCHAR,
  city VARCHAR
);

CREATE TABLE orders (
  id INT PRIMARY KEY,
  customer_id INT,
  order_date DATE,
  total_amount DECIMAL(10, 2),
  status VARCHAR
);`;


function App() {
  const [schemaDDL, setSchemaDDL] = useState(DEFAULT_SCHEMA);
  const [chatHistory, setChatHistory] = useState([]);
  const [activeQuery, setActiveQuery] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [prefilledPrompt, setPrefilledPrompt] = useState("");
  const stepsRef = useRef([]);

  // Subscribe to live SSE thoughts stream whenever there is an active query
  useEffect(() => {
    if (!activeQuery || !activeQuery.task_id) return;

    let isFinished = false;

    // Connect to SSE stream
    const unsubscribe = subscribeTaskEvents(
      activeQuery.task_id,
      (eventPayload) => {
        const { event, data } = eventPayload;
        
        if (event === 'completed' || event === 'failed') {
          isFinished = true;
          const isSuccess = event === 'completed';
          const resultData = data || {};
          const finalMessage = isSuccess 
            ? "Query generation & execution finished successfully." 
            : `Failed: ${resultData.error || 'Execution error'}`;

          if (!stepsRef.current.includes(finalMessage)) {
            stepsRef.current = [...stepsRef.current, finalMessage];
          }

          setActiveQuery(prev => prev ? { ...prev, steps: [...stepsRef.current] } : null);

          // Grace period so human eye can see the complete checkmark
          setTimeout(() => {
            const finalSteps = [...stepsRef.current];
            setChatHistory(prev => [{
              id: activeQuery.id,
              question: activeQuery.question,
              sql: resultData.sql || "",
              data: resultData.data || [],
              error: resultData.error || null,
              status: isSuccess ? 'completed' : 'failed',
              cached: Boolean(resultData.cached),
              retries: resultData.retries || 0,
              steps: finalSteps
            }, ...prev]);

            setActiveQuery(null);
            setIsLoading(false);
          }, 350);
        } else {
          // Live milestone thought step
          const stepMsg = data?.message || event;
          if (!stepsRef.current.includes(stepMsg)) {
            stepsRef.current = [...stepsRef.current, stepMsg];
          }
          setActiveQuery(prev => prev ? { ...prev, steps: [...stepsRef.current] } : null);
        }
      },
      // Error fallback: if SSE disconnects, fall back to polling
      async () => {
        if (isFinished) return;
        try {
          const status = await pollTaskStatus(activeQuery.task_id);
          if (status.status === 'completed' || status.status === 'failed') {
            const finalSteps = stepsRef.current.length > 0 
              ? [...stepsRef.current] 
              : ["Task completed via API response."];

            setChatHistory(prev => [{
              id: activeQuery.id,
              question: activeQuery.question,
              sql: status.sql,
              data: status.data,
              error: status.error,
              status: status.status,
              cached: activeQuery.cached,
              retries: status.retries,
              steps: finalSteps
            }, ...prev]);
            setActiveQuery(null);
            setIsLoading(false);
          }
        } catch (e) {
          console.error("Polling fallback error", e);
        }
      }
    );

    return () => {
      unsubscribe();
    };
  }, [activeQuery?.task_id]);

  const handleAskQuestion = async (question) => {
    setIsLoading(true);
    const id = Date.now().toString();
    const initialSteps = ["Task received. Checking exact-match cache..."];
    stepsRef.current = initialSteps;
    
    try {
      const res = await submitQuery(question, schemaDDL);
      if (res.cached) {
        // Fast path for cache hit
        const status = await pollTaskStatus(res.task_id);
        const cacheSteps = [
          "⚡ Deterministic SHA-256 match found in Redis cache (<5ms)",
          "⚡ Skipped LLM generation & AST validation",
          "⚡ Returned pre-computed SQL & database results instantly"
        ];
        stepsRef.current = cacheSteps;

        setChatHistory(prev => [{
          id,
          question,
          sql: status.sql,
          data: status.data,
          error: status.error,
          status: 'completed',
          cached: true,
          retries: 0,
          steps: cacheSteps
        }, ...prev]);
        setIsLoading(false);
      } else {
        // Cache miss: initiate live thought stream
        const queuedSteps = [
          ...initialSteps,
          "Cache miss. Enqueued to ARQ sequential worker..."
        ];
        stepsRef.current = queuedSteps;

        setActiveQuery({
          id,
          task_id: res.task_id,
          question,
          status: 'queued',
          cached: false,
          steps: queuedSteps
        });
      }
    } catch (e) {
      console.error(e);
      setIsLoading(false);
    }
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-neutral-950 text-neutral-50 flex flex-col font-sans selection:bg-indigo-500/30">
        
        {/* Top Navigation */}
        <header className="h-14 border-b border-neutral-800 flex items-center justify-between px-6 bg-neutral-900/50 backdrop-blur supports-[backdrop-filter]:bg-neutral-900/20">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
              <span className="text-indigo-400 font-bold tracking-tighter">AGY</span>
            </div>
            <h1 className="font-medium text-sm text-neutral-200">Text-to-SQL Dashboard</h1>
          </div>
          <div className="flex items-center gap-4 text-xs text-neutral-400">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              FastAPI Connected
            </div>
          </div>
        </header>

        {/* 3-Column Layout */}
        <main className="flex-1 grid grid-cols-12 gap-4 p-4 overflow-hidden h-[calc(100vh-3.5rem)]">
          
          <div className="col-span-3 flex flex-col gap-4 overflow-hidden">
            <SchemaPanel 
              schemaDDL={schemaDDL} 
              setSchemaDDL={setSchemaDDL} 
              onSelectQuery={(q) => setPrefilledPrompt(q)}
            />
          </div>

          <div className="col-span-4 flex flex-col gap-4 overflow-hidden">
            <ChatPanel 
              onAsk={handleAskQuestion} 
              isLoading={isLoading} 
              activeQuery={activeQuery}
              chatHistory={chatHistory} 
              externalPrompt={prefilledPrompt}
            />
          </div>

          <div className="col-span-5 flex flex-col gap-4 overflow-hidden">
            <ResultsPanel 
              latestResult={chatHistory[0]} 
              activeQuery={activeQuery}
            />
          </div>

        </main>
      </div>
    </TooltipProvider>
  )
}

export default App
