import React, { useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import TableNode from './TableNode';

const nodeTypes = {
  tableNode: TableNode,
};

const initialNodes = [
  {
    id: 'departments',
    type: 'tableNode',
    position: { x: 40, y: 30 },
    data: {
      tableName: 'departments',
      rowCount: 4,
      color: 'emerald',
      columns: [
        { name: 'id', type: 'INT', pk: true },
        { name: 'name', type: 'VARCHAR' },
        { name: 'budget', type: 'INT' },
        { name: 'location', type: 'VARCHAR' }
      ]
    }
  },
  {
    id: 'employees',
    type: 'tableNode',
    position: { x: 380, y: 30 },
    data: {
      tableName: 'employees',
      rowCount: 10,
      color: 'indigo',
      columns: [
        { name: 'id', type: 'INT', pk: true },
        { name: 'name', type: 'VARCHAR' },
        { name: 'department', type: 'VARCHAR' },
        { name: 'department_id', type: 'INT', fk: 'departments.id' },
        { name: 'role', type: 'VARCHAR' },
        { name: 'salary', type: 'INT' },
        { name: 'hire_date', type: 'DATE' }
      ]
    }
  },
  {
    id: 'customers',
    type: 'tableNode',
    position: { x: 40, y: 320 },
    data: {
      tableName: 'customers',
      rowCount: 5,
      color: 'sky',
      columns: [
        { name: 'id', type: 'INT', pk: true },
        { name: 'name', type: 'VARCHAR' },
        { name: 'email', type: 'VARCHAR' },
        { name: 'city', type: 'VARCHAR' }
      ]
    }
  },
  {
    id: 'orders',
    type: 'tableNode',
    position: { x: 380, y: 320 },
    data: {
      tableName: 'orders',
      rowCount: 8,
      color: 'amber',
      columns: [
        { name: 'id', type: 'INT', pk: true },
        { name: 'customer_id', type: 'INT', fk: 'customers.id' },
        { name: 'order_date', type: 'DATE' },
        { name: 'total_amount', type: 'DECIMAL(10,2)' },
        { name: 'status', type: 'VARCHAR' }
      ]
    }
  }
];

const initialEdges = [
  {
    id: 'employees_departments',
    source: 'departments',
    target: 'employees',
    sourceHandle: 'departments-id-source',
    targetHandle: 'employees-department_id-target',
    type: 'smoothstep',
    animated: true,
    label: '1 : N',
    labelStyle: { fill: '#818cf8', fontWeight: 600, fontSize: 11 },
    labelBgStyle: { fill: '#171717', fillOpacity: 0.9, rx: 4, ry: 4 },
    labelBgPadding: [6, 4],
    style: { stroke: '#6366f1', strokeWidth: 2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#6366f1',
      width: 16,
      height: 16,
    }
  },
  {
    id: 'orders_customers',
    source: 'customers',
    target: 'orders',
    sourceHandle: 'customers-id-source',
    targetHandle: 'orders-customer_id-target',
    type: 'smoothstep',
    animated: true,
    label: '1 : N',
    labelStyle: { fill: '#38bdf8', fontWeight: 600, fontSize: 11 },
    labelBgStyle: { fill: '#171717', fillOpacity: 0.9, rx: 4, ry: 4 },
    labelBgPadding: [6, 4],
    style: { stroke: '#0ea5e9', strokeWidth: 2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#0ea5e9',
      width: 16,
      height: 16,
    }
  }
];

export default function SchemaVisualizer({ height = "100%", isCompact = false }) {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div style={{ height }} className="w-full bg-[#0d0d0f] rounded-xl relative overflow-hidden select-none border border-neutral-800">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: isCompact ? 0.2 : 0.3 }}
        minZoom={0.3}
        maxZoom={2.0}
        attributionPosition="bottom-left"
        className="dark"
      >
        <Background 
          color="#33333d" 
          gap={20} 
          size={1.5} 
          variant={BackgroundVariant.Dots} 
        />
        <Controls 
          className="!bg-neutral-900/90 !border !border-neutral-700/80 !rounded-lg !overflow-hidden [&>button]:!bg-neutral-900 [&>button]:!border-b [&>button]:!border-neutral-800 [&>button]:!text-neutral-300 [&>button:hover]:!bg-neutral-800"
          showInteractive={false}
        />
        {!isCompact && (
          <MiniMap 
            nodeStrokeColor="#6366f1"
            nodeColor="#18181b"
            nodeBorderRadius={6}
            className="!bg-neutral-900/90 !border !border-neutral-800 !rounded-lg overflow-hidden !bottom-3 !right-3"
            maskColor="rgba(0, 0, 0, 0.6)"
          />
        )}
      </ReactFlow>

      {/* Floating Canvas Hint */}
      <div className="absolute top-3 left-3 pointer-events-none z-10 bg-neutral-900/80 backdrop-blur border border-neutral-800/80 px-2.5 py-1 rounded-md text-[10px] text-neutral-400 font-mono flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
        Interactive Canvas: Drag tables • Scroll to Zoom
      </div>
    </div>
  );
}
