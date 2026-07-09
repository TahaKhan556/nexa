"use client";

import { useState, useEffect, useRef } from "react";
import { AudioLines, Video, Map, FileText, X } from "lucide-react";

interface SlashCommandPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (command: string) => void;
  position: { top: number; left: number };
}

const commands = [
  {
    id: "/briefing",
    name: "Briefing Doc",
    description: "Quick audio summary (under 2 min)",
    icon: FileText,
    color: "text-blue-500",
  },
  {
    id: "/audio",
    name: "Audio Overview",
    description: "Podcast-style audio (2-10 min)",
    icon: AudioLines,
    color: "text-green-500",
  },
  {
    id: "/mindmap",
    name: "Mind Map",
    description: "Interactive concept visualization",
    icon: Map,
    color: "text-purple-500",
  },
  {
    id: "/video",
    name: "Video Overview",
    description: "Narrated slides video (30+ min)",
    icon: Video,
    color: "text-red-500",
  },
];

export function SlashCommandPopup({ isOpen, onClose, onSelect, position }: SlashCommandPopupProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [search, setSearch] = useState("");
  const popupRef = useRef<HTMLDivElement>(null);

  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.name.toLowerCase().includes(search.toLowerCase()) ||
      cmd.id.toLowerCase().includes(search.toLowerCase())
  );

  useEffect(() => {
    setSelectedIndex(0);
  }, [search]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % filteredCommands.length);
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % filteredCommands.length);
          break;
        case "Enter":
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            onSelect(filteredCommands[selectedIndex].id);
          }
          break;
        case "Escape":
          e.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, onSelect, onClose]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={popupRef}
      className="fixed z-50 w-80 rounded-xl border border-border bg-card shadow-lg"
      style={{ bottom: position.top + 60, left: position.left }}
    >
      <div className="border-b border-border p-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">Studio Features</span>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted">
            <X className="h-3 w-3 text-muted-foreground" />
          </button>
        </div>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search features..."
          className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          autoFocus
        />
      </div>

      <div className="max-h-64 overflow-y-auto p-2">
        {filteredCommands.map((cmd, index) => {
          const Icon = cmd.icon;
          return (
            <button
              key={cmd.id}
              onClick={() => onSelect(cmd.id)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors ${
                index === selectedIndex ? "bg-primary/10 text-primary" : "hover:bg-muted"
              }`}
            >
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted ${cmd.color}`}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium">{cmd.name}</div>
                <div className="text-xs text-muted-foreground truncate">{cmd.description}</div>
              </div>
              <span className="text-xs text-muted-foreground font-mono">{cmd.id}</span>
            </button>
          );
        })}

        {filteredCommands.length === 0 && (
          <div className="px-3 py-6 text-center text-sm text-muted-foreground">
            No features found
          </div>
        )}
      </div>

      <div className="border-t border-border px-3 py-2">
        <p className="text-[10px] text-muted-foreground">
          Press Enter to select, Esc to close
        </p>
      </div>
    </div>
  );
}
