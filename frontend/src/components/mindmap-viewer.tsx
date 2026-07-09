"use client";

import { useState, useRef, useEffect } from "react";
import { ZoomIn, ZoomOut, Download, RotateCcw, Loader2 } from "lucide-react";

interface MindMapViewerProps {
  svgData?: string;
  imageUrl?: string;
  title?: string;
  onDownload?: () => void;
}

export function MindMapViewer({ svgData, imageUrl, title, onDownload }: MindMapViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(!svgData && !imageUrl);
  }, [svgData, imageUrl]);

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev - 0.2, 0.3));
  };

  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom((prev) => Math.max(0.3, Math.min(3, prev + delta)));
  };

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {title && (
        <div className="px-4 py-2 border-b border-border">
          <div className="text-sm font-medium text-foreground truncate">{title}</div>
        </div>
      )}

      <div className="relative">
        {/* Controls */}
        <div className="absolute top-2 right-2 z-10 flex items-center gap-1 rounded-lg border border-border bg-background/90 p-1">
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded hover:bg-muted"
            title="Zoom In"
          >
            <ZoomIn className="h-4 w-4 text-muted-foreground" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded hover:bg-muted"
            title="Zoom Out"
          >
            <ZoomOut className="h-4 w-4 text-muted-foreground" />
          </button>
          <button
            onClick={handleReset}
            className="p-1.5 rounded hover:bg-muted"
            title="Reset View"
          >
            <RotateCcw className="h-4 w-4 text-muted-foreground" />
          </button>
          {onDownload && (
            <button
              onClick={onDownload}
              className="p-1.5 rounded hover:bg-muted"
              title="Download"
            >
              <Download className="h-4 w-4 text-muted-foreground" />
            </button>
          )}
        </div>

        {/* Zoom level indicator */}
        <div className="absolute bottom-2 left-2 z-10 rounded-lg border border-border bg-background/90 px-2 py-1">
          <span className="text-xs text-muted-foreground">{Math.round(zoom * 100)}%</span>
        </div>

        {/* Content area */}
        <div
          ref={containerRef}
          className="h-96 overflow-hidden bg-muted/20 cursor-grab active:cursor-grabbing"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        >
          {isLoading ? (
            <div className="flex h-full items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : svgData ? (
            <div
              className="w-full h-full flex items-center justify-center"
              style={{
                transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              }}
              dangerouslySetInnerHTML={{ __html: svgData }}
            />
          ) : imageUrl ? (
            <img
              src={imageUrl}
              alt="Mind Map"
              className="w-full h-full object-contain"
              style={{
                transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              }}
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground text-sm">
              No mind map data available
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
