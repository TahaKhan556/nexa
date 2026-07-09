"use client";

import { useState, useEffect } from "react";
import { ChevronDown, BookOpen } from "lucide-react";

interface Notebook {
  id: string;
  name: string;
  description: string;
}

interface NotebookSelectorProps {
  selectedNotebook: string | null;
  onSelect: (notebookId: string | null) => void;
}

const defaultNotebooks: Notebook[] = [
  {
    id: "a96f0015-76d6-40a9-afbb-3613ecf080ce",
    name: "Science & Technology",
    description: "Physics, CS, AI, engineering",
  },
  {
    id: "9bfb6427-6813-4ffc-9b24-33991ad2bc92",
    name: "History & World Events",
    description: "World history, civilizations",
  },
  {
    id: "206230a1-94f5-4049-899e-cf6a4ae030f5",
    name: "Mathematics & Logic",
    description: "Algebra, calculus, statistics",
  },
  {
    id: "a9c8b9eb-29bf-4514-9287-bb5d9972b695",
    name: "Language & Literature",
    description: "Writing, grammar, literature",
  },
  {
    id: "36c984fa-2589-4e1c-998e-92657a72daec",
    name: "Business & Economics",
    description: "Finance, marketing, economics",
  },
];

export function NotebookSelector({ selectedNotebook, onSelect }: NotebookSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [notebooks, setNotebooks] = useState<Notebook[]>(defaultNotebooks);

  const selectedNotebookData = notebooks.find((nb) => nb.id === selectedNotebook);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm hover:bg-muted transition-colors"
      >
        <BookOpen className="h-4 w-4 text-muted-foreground" />
        <span className="truncate max-w-[150px]">
          {selectedNotebookData ? selectedNotebookData.name : "Select Notebook"}
        </span>
        <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-72 rounded-xl border border-border bg-card shadow-lg z-50">
          <div className="p-2">
            <button
              onClick={() => {
                onSelect(null);
                setIsOpen(false);
              }}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors ${
                !selectedNotebook ? "bg-primary/10 text-primary" : "hover:bg-muted"
              }`}
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <BookOpen className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium">All Notebooks</div>
                <div className="text-xs text-muted-foreground">Let AI choose the best one</div>
              </div>
            </button>

            {notebooks.map((notebook) => (
              <button
                key={notebook.id}
                onClick={() => {
                  onSelect(notebook.id);
                  setIsOpen(false);
                }}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors ${
                  selectedNotebook === notebook.id ? "bg-primary/10 text-primary" : "hover:bg-muted"
                }`}
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                  <BookOpen className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{notebook.name}</div>
                  <div className="text-xs text-muted-foreground truncate">{notebook.description}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
