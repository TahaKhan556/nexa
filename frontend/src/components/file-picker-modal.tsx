"use client";

import { useState, useRef } from "react";
import { Upload, FileText, X } from "lucide-react";

interface UploadedFile {
  id: string;
  name: string;
  size: string;
}

interface FilePickerModalProps {
  onClose: () => void;
  featureType: string;
  onConfirm: (fileId: string, fileName: string) => void;
}

const DEMO_FILES: UploadedFile[] = [
  { id: "demo-1", name: "project-proposal.pdf", size: "245.3 KB" },
  { id: "demo-2", name: "research-paper.txt", size: "89.7 KB" },
  { id: "demo-3", name: "meeting-notes.md", size: "12.4 KB" },
];

export function FilePickerModal({
  onClose,
  featureType,
  onConfirm,
}: FilePickerModalProps) {
  const [files, setFiles] = useState<UploadedFile[]>(DEMO_FILES);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploaded = e.target.files?.[0];
    if (!uploaded) return;
    const newFile: UploadedFile = {
      id: `file-${Date.now()}`,
      name: uploaded.name,
      size: `${(uploaded.size / 1024).toFixed(1)} KB`,
    };
    setFiles((prev) => [...prev, newFile]);
    setSelectedId(newFile.id);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleConfirm = () => {
    const file = files.find((f) => f.id === selectedId);
    if (file) onConfirm(file.id, file.name);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-sm font-semibold text-foreground">
            Select a file
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-6">
          {files.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-8">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Upload className="h-5 w-5 text-primary" />
              </div>
              <p className="text-sm text-muted-foreground">
                No files uploaded yet
              </p>
            </div>
          ) : (
            <div className="mb-4 space-y-2">
              {files.map((file) => (
                <button
                  key={file.id}
                  onClick={() => setSelectedId(file.id)}
                  className={`flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left text-sm transition-colors ${
                    selectedId === file.id
                      ? "border-primary bg-primary/5 text-foreground"
                      : "border-border text-muted-foreground hover:bg-muted"
                  }`}
                >
                  <FileText className="h-4 w-4 shrink-0" />
                  <span className="flex-1 truncate">{file.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {file.size}
                  </span>
                </button>
              ))}
            </div>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.doc,.docx,.md"
            onChange={handleUpload}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="mb-6 flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-border px-4 py-3 text-sm text-muted-foreground transition-colors hover:border-primary/50 hover:text-primary"
          >
            <Upload className="h-4 w-4" />
            Upload new file
          </button>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={!selectedId}
              className="flex-1 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Generate
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
