import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { Table, Key, Link2 } from 'lucide-react';

export default function TableNode({ data }) {
  const { tableName, rowCount, columns, color = "indigo" } = data;

  const headerColors = {
    indigo: "from-indigo-600/30 to-indigo-900/10 border-indigo-500/40 text-indigo-300",
    emerald: "from-emerald-600/30 to-emerald-900/10 border-emerald-500/40 text-emerald-300",
    amber: "from-amber-600/30 to-amber-900/10 border-amber-500/40 text-amber-300",
    sky: "from-sky-600/30 to-sky-900/10 border-sky-500/40 text-sky-300",
  };

  const activeHeaderStyle = headerColors[color] || headerColors.indigo;

  return (
    <div className="bg-neutral-900/95 border border-neutral-700/80 rounded-xl shadow-2xl backdrop-blur-md min-w-[240px] overflow-hidden text-neutral-200 font-sans transition-all hover:border-neutral-500/80 hover:shadow-indigo-500/10">
      
      {/* Node Header */}
      <div className={`px-3.5 py-2.5 border-b bg-gradient-to-r ${activeHeaderStyle} flex items-center justify-between`}>
        <div className="flex items-center gap-2">
          <Table className="w-4 h-4 opacity-80" />
          <span className="font-semibold text-xs tracking-wide uppercase font-mono">{tableName}</span>
        </div>
        {rowCount !== undefined && (
          <span className="text-[10px] bg-neutral-950/60 border border-neutral-700/50 px-2 py-0.5 rounded-full font-mono text-neutral-400">
            {rowCount} rows
          </span>
        )}
      </div>

      {/* Column Rows */}
      <div className="py-1 divide-y divide-neutral-800/60 bg-neutral-950/40">
        {columns.map((col, idx) => (
          <div 
            key={idx} 
            className="relative px-3.5 py-1.5 flex items-center justify-between text-xs hover:bg-neutral-800/40 transition-colors group"
          >
            {/* Left Connection Target Handle */}
            <Handle
              type="target"
              position={Position.Left}
              id={`${tableName}-${col.name}-target`}
              className="!w-2 !h-2 !bg-indigo-400 !border-2 !border-neutral-900 hover:!scale-125 transition-transform"
            />

            {/* Column Name & Key Badges */}
            <div className="flex items-center gap-1.5 pr-2">
              {col.pk && (
                <span className="flex items-center gap-0.5 text-[9px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40 px-1 rounded font-mono" title="Primary Key">
                  <Key className="w-2.5 h-2.5" />
                  PK
                </span>
              )}
              {col.fk && (
                <span className="flex items-center gap-0.5 text-[9px] font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/40 px-1 rounded font-mono" title={`Foreign Key: references ${col.fk}`}>
                  <Link2 className="w-2.5 h-2.5" />
                  FK
                </span>
              )}
              <span className={`font-mono text-xs ${col.pk ? 'text-amber-200 font-semibold' : col.fk ? 'text-indigo-200' : 'text-neutral-300'}`}>
                {col.name}
              </span>
            </div>

            {/* Type Badge */}
            <span className="text-[10px] font-mono text-neutral-500 group-hover:text-neutral-400 transition-colors">
              {col.type}
            </span>

            {/* Right Connection Source Handle */}
            <Handle
              type="source"
              position={Position.Right}
              id={`${tableName}-${col.name}-source`}
              className="!w-2 !h-2 !bg-indigo-400 !border-2 !border-neutral-900 hover:!scale-125 transition-transform"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
