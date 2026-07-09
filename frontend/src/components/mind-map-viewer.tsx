"use client";

import { useState, useRef, useCallback } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Download } from "lucide-react";

interface MindMapNode {
  id: string;
  label: string;
  x: number;
  y: number;
  children?: string[];
}

interface MindMapEdge {
  from: string;
  to: string;
}

const SAMPLE_NODES: MindMapNode[] = [
  { id: "1", label: "Main Topic", x: 300, y: 30, children: ["2", "3", "4"] },
  { id: "2", label: "Subtopic A", x: 100, y: 130, children: ["5", "6"] },
  { id: "3", label: "Subtopic B", x: 300, y: 150, children: ["7"] },
  { id: "4", label: "Subtopic C", x: 500, y: 130, children: ["8"] },
  { id: "5", label: "Detail 1", x: 30, y: 240 },
  { id: "6", label: "Detail 2", x: 170, y: 240 },
  { id: "7", label: "Detail 3", x: 300, y: 260 },
  { id: "8", label: "Detail 4", x: 500, y: 240 },
];

const SAMPLE_EDGES: MindMapEdge[] = [
  { from: "1", to: "2" },
  { from: "1", to: "3" },
  { from: "1", to: "4" },
  { from: "2", to: "5" },
  { from: "2", to: "6" },
  { from: "3", to: "7" },
  { from: "4", to: "8" },
];

interface MindMapViewerProps {
  data?: { nodes: MindMapNode[]; edges: MindMapEdge[] };
  onDownload?: () => void;
}

export function MindMapViewer({
  data,
  onDownload,
}: MindMapViewerProps) {
  const nodes = data?.nodes ?? SAMPLE_NODES;
  const edges = data?.edges ?? SAMPLE_EDGES;

  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selected, setSelected] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      setDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    },
    [pan]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!dragging) return;
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    },
    [dragging, dragStart]
  );

  const handleMouseUp = useCallback(() => {
    setDragging(false);
  }, []);

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelected(null);
  };

  const downloadPng = () => {
    if (!svgRef.current) return;
    const svg = svgRef.current;
    const rect = svg.getBoundingClientRect();
    const canvas = document.createElement("canvas");
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(2, 2);
    const xml = new XMLSerializer().serializeToString(svg);
    const img = new Image();
    img.onload = () => {
      ctx.drawImage(img, 0, 0, rect.width, rect.height);
      const a = document.createElement("a");
      a.download = "mind-map.png";
      a.href = canvas.toDataURL("image/png");
      a.click();
    };
    img.src = "data:image/svg+xml;base64," + btoa(xml);
  };

  const width = 600;
  const height = 350;

  return (
    <div className="mx-auto w-full max-w-4xl">
      <div className="rounded-2xl border border-border bg-card p-4">
        {/* Toolbar */}
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">Mind Map</h3>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <ZoomOut className="h-4 w-4" />
            </button>
            <span className="w-10 text-center text-xs text-muted-foreground">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={() => setZoom((z) => Math.min(2, z + 0.1))}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <ZoomIn className="h-4 w-4" />
            </button>
            <button
              onClick={resetView}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
            <button
              onClick={onDownload ?? downloadPng}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <Download className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* SVG canvas */}
        <div className="aspect-[4/3] w-full overflow-hidden rounded-xl bg-muted/30">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${width} ${height}`}
            width="100%"
            height="100%"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: "center",
              cursor: dragging ? "grabbing" : "grab",
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {/* Edges */}
            {edges.map((edge) => {
              const from = nodes.find((n) => n.id === edge.from);
              const to = nodes.find((n) => n.id === edge.to);
              if (!from || !to) return null;
              return (
                <line
                  key={`${edge.from}-${edge.to}`}
                  x1={from.x}
                  y1={from.y}
                  x2={to.x}
                  y2={to.y}
                  stroke="oklch(0.55 0.18 25 / 0.4)"
                  strokeWidth={2}
                />
              );
            })}

            {/* Nodes */}
            {nodes.map((node) => (
              <g
                key={node.id}
                onClick={() =>
                  setSelected(selected === node.id ? null : node.id)
                }
                style={{ cursor: "pointer" }}
              >
                <rect
                  x={node.x - 60}
                  y={node.y - 16}
                  width={120}
                  height={32}
                  rx={16}
                  fill={
                    selected === node.id
                      ? "oklch(0.55 0.18 25)"
                      : "oklch(0.22 0 0)"
                  }
                  stroke={
                    selected === node.id
                      ? "oklch(0.55 0.18 25)"
                      : "oklch(0.35 0 0)"
                  }
                  strokeWidth={2}
                />
                <text
                  x={node.x}
                  y={node.y + 4}
                  textAnchor="middle"
                  fill="oklch(0.985 0 0)"
                  fontSize={11}
                  fontWeight={500}
                >
                  {node.label}
                </text>
              </g>
            ))}
          </svg>
        </div>

        {selected && (
          <p className="mt-3 text-center text-xs text-muted-foreground">
            Selected: {nodes.find((n) => n.id === selected)?.label}
          </p>
        )}
      </div>
    </div>
  );
}
