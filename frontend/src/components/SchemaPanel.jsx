import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Database, Table, Sparkles } from "lucide-react";
import { fetchSchemas } from '../api/client';

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
    <Card className="h-full flex flex-col bg-neutral-900 border-neutral-800 rounded-xl overflow-hidden shadow-xl">
      <CardHeader className="border-b border-neutral-800 bg-neutral-900/50 py-3 flex flex-row items-center justify-between">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          Enterprise Relational DB
        </CardTitle>
        <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-mono flex items-center gap-1">
          <Table className="w-3 h-3" />
          4 Tables Active
        </span>
      </CardHeader>
      
      <CardContent className="p-0 flex-1 flex flex-col overflow-hidden">
        {/* Table summary badge bar */}
        <div className="px-3 py-2 bg-neutral-950/70 border-b border-neutral-800 flex items-center gap-2 overflow-x-auto text-[11px] font-mono text-neutral-400">
          <span className="bg-neutral-900 px-2 py-0.5 rounded border border-neutral-800">departments</span>
          <span className="bg-neutral-900 px-2 py-0.5 rounded border border-neutral-800">employees</span>
          <span className="bg-neutral-900 px-2 py-0.5 rounded border border-neutral-800">customers</span>
          <span className="bg-neutral-900 px-2 py-0.5 rounded border border-neutral-800">orders</span>
        </div>

        {/* DDL Editor */}
        <div className="flex-1 flex flex-col min-h-0 relative">
          <Textarea 
            value={schemaDDL}
            onChange={(e) => setSchemaDDL(e.target.value)}
            className="flex-1 bg-transparent border-0 rounded-none focus-visible:ring-0 text-xs font-mono text-emerald-300/90 p-3 resize-none leading-relaxed overflow-y-auto"
            placeholder="CREATE TABLE..."
          />
        </div>

        {/* Suggested Queries Chips */}
        {sampleQueries && sampleQueries.length > 0 && (
          <div className="border-t border-neutral-800 bg-neutral-950/90 p-3 flex flex-col gap-2 max-h-52 overflow-y-auto">
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
  )
}
