import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Code2, Table2, TerminalSquare } from "lucide-react";
import Editor from "@monaco-editor/react";

export default function ResultsPanel({ latestResult, activeQuery }) {
  
  if (activeQuery) {
    return (
      <Card className="h-full flex items-center justify-center bg-neutral-900 border-neutral-800 shadow-xl">
        <div className="flex flex-col items-center gap-4 animate-pulse">
          <TerminalSquare className="w-12 h-12 text-neutral-700" />
          <p className="text-sm text-neutral-500 font-mono">Generating SQL & executing query...</p>
        </div>
      </Card>
    )
  }

  if (!latestResult) {
    return (
      <Card className="h-full flex items-center justify-center bg-neutral-900 border-neutral-800 shadow-xl">
        <div className="text-center">
          <Table2 className="w-12 h-12 text-neutral-800 mx-auto mb-3" />
          <p className="text-sm text-neutral-500">Execution results will appear here</p>
        </div>
      </Card>
    )
  }

  const { sql, data, error } = latestResult;
  
  const headers = data && data.length > 0 ? Object.keys(data[0]) : [];

  return (
    <Card className="h-full flex flex-col bg-neutral-900 border-neutral-800 shadow-xl overflow-hidden rounded-xl">
      <CardHeader className="border-b border-neutral-800 bg-neutral-900/50 py-3">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
          <Code2 className="w-4 h-4 text-sky-400" />
          Generated SQL
        </CardTitle>
      </CardHeader>


      
      <div className="h-[200px] border-b border-neutral-800 bg-[#1e1e1e]">
        <Editor
          height="100%"
          defaultLanguage="sql"
          theme="vs-dark"
          value={sql || ""}
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: "JetBrains Mono, monospace",
            padding: { top: 16 }
          }}
        />
      </div>

      <CardHeader className="border-b border-neutral-800 bg-neutral-900/50 py-3">
        <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
          <Table2 className="w-4 h-4 text-rose-400" />
          Execution Results
        </CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 p-0 overflow-auto bg-neutral-950">
        {error ? (
          <div className="p-6 text-red-400 font-mono text-sm">
            {error}
          </div>
        ) : data && data.length > 0 ? (
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-neutral-400 uppercase bg-neutral-900 sticky top-0">
              <tr>
                {headers.map((h, i) => (
                  <th key={i} className="px-6 py-3 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i} className="border-b border-neutral-800/50 hover:bg-neutral-800/50 text-neutral-300">
                  {headers.map((h, j) => (
                    <td key={j} className="px-6 py-3 whitespace-nowrap">{row[h]?.toString()}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-6 text-neutral-500 italic text-sm">
            Query returned 0 rows.
          </div>
        )}
      </CardContent>
    </Card>
  )
}
