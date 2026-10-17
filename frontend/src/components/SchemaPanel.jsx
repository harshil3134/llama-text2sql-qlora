import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Database, Table, Sparkles, Code2, Network, Maximize2, X, Key, Link2 } from "lucide-react";
import { fetchSchemas } from '../api/client';
import SchemaVisualizer from './erd/SchemaVisualizer';

const DEFAULT_SAMPLE_QUERIES = [
  "Find employees who are Account Executives with a salary under 90000",
  "Who is the highest paid employee and what is their role?",
  "Show the average salary for each department",
  "List all customers who live in San Francisco or Seattle",
  "Find the total amount spent by customer Alice Johnson",
  "List employee names along with their department location and budget",
  "Find all orders with a total amount greater than 500 dollars"
];

export default function SchemaPanel({ schemaDDL, setSchemaDDL, onSelectQuery }) {
  const [sampleQueries, setSampleQueries] = useState(DEFAULT_SAMPLE_QUERIES);
  const [viewMode, setViewMode] = useState('erd'); // 'erd' or 'ddl'
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetchSchemas();
        if (res.sample_queries && res.sample_queries.length > 0) {
          setSampleQueries(res.sample_queries);
        }
      } catch (e) {
        console.error("Failed to load schema queries:", e);
      }
    }
    load();
  }, []);

  return (
    <>
      <Card className="h-full flex flex-col bg-neutral-900 border-neutral-800 rounded-xl overflow-hidden shadow-xl">
        {/* Header with Title and Mode Switcher */}
        <CardHeader className="border-b border-neutral-800 bg-neutral-900/60 py-2.5 px-3 flex flex-row items-center justify-between">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-300 flex items-center gap-2">
            <Database className="w-4 h-4 text-emerald-400" />
            <span>Relational Schema</span>
          </CardTitle>
          
          <div className="flex items-center gap-1.5 bg-neutral-950/80 p-0.5 rounded-lg border border-neutral-800">
            <button
              onClick={() => setViewMode('erd')}
              className={`px-2 py-1 rounded-md text-[11px] font-medium flex items-center gap-1.5 transition-all ${
                viewMode === 'erd'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/60'
              }`}
              title="Interactive ERD Diagram"
            >
              <Network className="w-3 h-3" />
              <span>ERD</span>
            </button>
            <button
              onClick={() => setViewMode('ddl')}
              className={`px-2 py-1 rounded-md text-[11px] font-medium flex items-center gap-1.5 transition-all ${
                viewMode === 'ddl'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/60'
              }`}
              title="Raw SQL DDL Code"
            >
              <Code2 className="w-3 h-3" />
              <span>DDL</span>
            </button>
          </div>
        </CardHeader>
        
        <CardContent className="p-0 flex-1 flex flex-col overflow-hidden">
          {/* Subheader Toolbar */}
          <div className="px-3 py-1.5 bg-neutral-950/70 border-b border-neutral-800 flex items-center justify-between text-[11px] font-mono text-neutral-400">
            <div className="flex items-center gap-1.5 overflow-x-auto">
              <span className="text-[10px] text-neutral-400 bg-neutral-900 px-1.5 py-0.5 rounded border border-neutral-800/80">
                4 Tables (SQLite)
              </span>
            </div>

            {viewMode === 'erd' && (
              <button
                onClick={() => setIsModalOpen(true)}
                className="flex items-center gap-1 text-[10px] bg-neutral-900 hover:bg-neutral-800 text-indigo-300 hover:text-indigo-200 border border-neutral-700/60 px-2 py-0.5 rounded-md transition-colors"
                title="Expand to Fullscreen Explorer"
              >
                <Maximize2 className="w-3 h-3" />
                <span>Expand</span>
              </button>
            )}
          </div>

          {/* Main Visual or Code View */}
          <div className="flex-1 flex flex-col min-h-0 relative">
            {viewMode === 'erd' ? (
              <div className="flex-1 w-full h-full relative">
                <SchemaVisualizer isCompact={true} />
              </div>
            ) : (
              <Textarea 
                value={schemaDDL}
                onChange={(e) => setSchemaDDL(e.target.value)}
                className="flex-1 bg-transparent border-0 rounded-none focus-visible:ring-0 text-xs font-mono text-emerald-300/90 p-3 resize-none leading-relaxed overflow-y-auto"
                placeholder="CREATE TABLE..."
              />
            )}
          </div>

          {/* Suggested Queries Chips */}
          {sampleQueries && sampleQueries.length > 0 && (
            <div className="border-t border-neutral-800 bg-neutral-950/90 p-3 flex flex-col gap-2 max-h-48 overflow-y-auto">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                Click to Run Sample Query:
              </span>
              <div className="flex flex-col gap-1.5">
                {sampleQueries.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSelectQuery && onSelectQuery(q)}
                    className="text-left text-xs bg-neutral-900/80 hover:bg-neutral-800 hover:text-indigo-300 text-neutral-300 px-2.5 py-1.5 rounded-md border border-neutral-800 transition-colors truncate"
                    title={q}
                  >
                    › "{q}"
                  </button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Fullscreen ERD Explorer Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 sm:p-8 animate-in fade-in-0 duration-150">
          <div className="w-full max-w-6xl h-[88vh] bg-neutral-950 border border-neutral-800 rounded-2xl flex flex-col shadow-2xl overflow-hidden relative">
            
            {/* Modal Header */}
            <div className="px-5 py-3.5 border-b border-neutral-800 bg-neutral-900/80 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                  <Network className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-neutral-100 flex items-center gap-2">
                    Database Schema Explorer (Interactive ERD)
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Live SQLite
                    </span>
                  </h2>
                  <p className="text-xs text-neutral-400">
                    Drag tables anywhere, hover over relationships, zoom in/out with scroll
                  </p>
                </div>
              </div>

              {/* Close Button */}
              <button
                onClick={() => setIsModalOpen(false)}
                className="w-8 h-8 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-neutral-100 flex items-center justify-center transition-colors"
                title="Close Explorer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Canvas Body */}
            <div className="flex-1 w-full h-full relative overflow-hidden">
              <SchemaVisualizer height="100%" isCompact={false} />
            </div>

            {/* Modal Footer Legend */}
            <div className="px-5 py-2.5 border-t border-neutral-800 bg-neutral-900/90 flex items-center justify-between text-xs text-neutral-400">
              <div className="flex items-center gap-4">
                <span className="font-semibold text-neutral-300">Legend:</span>
                <div className="flex items-center gap-1.5">
                  <span className="flex items-center gap-0.5 text-[9px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40 px-1 rounded font-mono">
                    <Key className="w-2.5 h-2.5" />
                    PK
                  </span>
                  <span className="text-[11px] text-neutral-300">Primary Key</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="flex items-center gap-0.5 text-[9px] font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/40 px-1 rounded font-mono">
                    <Link2 className="w-2.5 h-2.5" />
                    FK
                  </span>
                  <span className="text-[11px] text-neutral-300">Foreign Key</span>
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-indigo-400">
                  <span className="inline-block w-4 h-0.5 bg-indigo-500"></span>
                  <span>1 : N Foreign Key Relationship</span>
                </div>
              </div>

              <div className="text-[11px] font-mono text-neutral-400">
                Press Esc or click Close to return
              </div>
            </div>

          </div>
        </div>
      )}
    </>
  );
}
