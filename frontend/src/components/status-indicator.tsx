"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export function StatusIndicator() {
  const [status, setStatus] = useState<"loading" | "connected" | "error">(
    "loading"
  );

  useEffect(() => {
    async function checkStatus() {
      try {
        const res = await fetch("/api/status");
        const data = await res.json();
        setStatus(data.session_valid ? "connected" : "error");
      } catch {
        setStatus("error");
      }
    }
    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <div
        className={cn(
          "h-2 w-2 rounded-full",
          status === "connected" && "bg-success animate-pulse",
          status === "error" && "bg-destructive",
          status === "loading" && "bg-warning animate-pulse"
        )}
      />
      <span>
        {status === "connected" && "NotebookLM Connected"}
        {status === "error" && "NotebookLM Disconnected"}
        {status === "loading" && "Checking..."}
      </span>
    </div>
  );
}
