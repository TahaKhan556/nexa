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
    id: "34e9d568-5ca8-4844-892c-0c56a5949bfd",
    name: "Science & Technology",
    description: "Physics, CS, AI, engineering",
  },
  {
    id: "daaea9d6-8166-46ed-a600-b02319587762",
    name: "History & World Events",
    description: "World history, civilizations",
  },
  {
    id: "81befdb2-9a82-45dd-90db-487f9935dcea",
    name: "Mathematics & Logic",
    description: "Algebra, calculus, statistics",
  },
  {
    id: "0dc6371b-5b5d-4056-a2d4-e0693c4abdbf",
    name: "Language & Literature",
    description: "Writing, grammar, literature",
  },
  {
    id: "3e266742-5bcd-4412-9aba-5d0e0afde3ba",
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
