"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Menu, X, Loader2 } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { ChatInput } from "@/components/chat-input";
import { ChatMessage, Message } from "@/components/chat-message";
import { StatusIndicator } from "@/components/status-indicator";
import { SlashCommandPopup } from "@/components/slash-command-popup";
import { AudioPlayer } from "@/components/audio-player";
import { VideoPlayer } from "@/components/video-player";
import { MindMapViewer } from "@/components/mindmap-viewer";
import { NotebookSelector } from "@/components/notebook-selector";

function generateId() {
  return Math.random().toString(36).slice(2, 11);
}

function formatTime() {
  return new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

interface StudioJob {
  id: string;
  feature_type: string;
  status: string;
  content_url?: string;
  error?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [slashOpen, setSlashOpen] = useState(false);
  const [slashPosition, setSlashPosition] = useState({ top: 0, left: 0 });
  const [currentInput, setCurrentInput] = useState("");
  const [selectedNotebook, setSelectedNotebook] = useState<string | null>(null);
  const [studioJobs, setStudioJobs] = useState<StudioJob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, studioJobs]);

  // Poll for studio job status
  useEffect(() => {
    const pendingJobs = studioJobs.filter((job) => job.status === "generating" || job.status === "pending");
    if (pendingJobs.length === 0) return;

    const interval = setInterval(async () => {
      for (const job of pendingJobs) {
        try {
          const res = await fetch(`/api/studio/status/${job.id}`);
          const data = await res.json();

          setStudioJobs((prev) =>
            prev.map((j) =>
              j.id === job.id
                ? { ...j, status: data.status, content_url: data.content_url, error: data.error }
                : j
            )
          );

          // Add notification message when job completes
          if (data.status === "ready" || data.status === "failed") {
            const notificationMsg: Message = {
              id: generateId(),
              role: "assistant",
              content:
                data.status === "ready"
                  ? `✅ ${job.feature_type} is ready!`
                  : `❌ ${job.feature_type} failed: ${data.error || "Unknown error"}`,
              timestamp: formatTime(),
            };
            setMessages((prev) => [...prev, notificationMsg]);
          }
        } catch (err) {
          console.error("Failed to check job status:", err);
        }
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [studioJobs]);

  const handleSlashCommand = useCallback(
    async (command: string) => {
      setSlashOpen(false);

      // If we have a selected notebook, append it to the command
      const fullCommand = selectedNotebook ? `${command} ${selectedNotebook}` : command;

      const userMsg: Message = {
        id: generateId(),
        role: "user",
        content: fullCommand,
        timestamp: formatTime(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);

      const botMsg: Message = {
        id: generateId(),
        role: "assistant",
        content: "",
        timestamp: formatTime(),
        loading: true,
      };
      setMessages((prev) => [...prev, botMsg]);

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: fullCommand, notebook_id: selectedNotebook }),
        });
        const data = await res.json();

        // Handle studio jobs
        if (data.job_id) {
          const newJob: StudioJob = {
            id: data.job_id,
            feature_type: data.feature_type,
            status: "generating",
          };
          setStudioJobs((prev) => [...prev, newJob]);

          setMessages((prev) =>
            prev.map((m) =>
              m.id === botMsg.id
                ? {
                    ...m,
                    content: data.response || "Starting generation...",
                    loading: false,
                  }
                : m
            )
          );
        } else {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === botMsg.id
                ? {
                    ...m,
                    content: data.response || data.error || "No response received.",
                    loading: false,
                  }
                : m
            )
          );
        }
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botMsg.id
              ? {
                  ...m,
                  content: `Error: ${err instanceof Error ? err.message : "Failed to connect to backend."}`,
                  loading: false,
                }
              : m
          )
        );
      } finally {
        setLoading(false);
        setCurrentInput("");
      }
    },
    [selectedNotebook]
  );

  const handleSend = async (content: string) => {
    // Check for slash commands
    if (content.startsWith("/")) {
      const parts = content.split(" ");
      const command = parts[0].toLowerCase();

      if (["/briefing", "/audio", "/mindmap", "/video"].includes(command)) {
        return handleSlashCommand(content);
      }
    }

    const userMsg: Message = {
      id: generateId(),
      role: "user",
      content,
      timestamp: formatTime(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    const botMsg: Message = {
      id: generateId(),
      role: "assistant",
      content: "",
      timestamp: formatTime(),
      loading: true,
    };
    setMessages((prev) => [...prev, botMsg]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content, notebook_id: selectedNotebook }),
      });
      const data = await res.json();

      setMessages((prev) =>
        prev.map((m) =>
          m.id === botMsg.id
            ? {
                ...m,
                content: data.response || data.error || "No response received.",
                loading: false,
              }
            : m
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === botMsg.id
            ? {
                ...m,
                content: `Error: ${err instanceof Error ? err.message : "Failed to connect to backend."}`,
                loading: false,
              }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (value: string) => {
    setCurrentInput(value);

    // Check for slash command trigger
    if (value === "/" && !slashOpen) {
      const rect = inputRef.current?.getBoundingClientRect();
      if (rect) {
        setSlashPosition({ top: window.innerHeight - rect.top, left: rect.left });
      }
      setSlashOpen(true);
    } else if (value !== "/" && slashOpen && !value.startsWith("/")) {
      setSlashOpen(false);
    }
  };

  const handleSlashSelect = (command: string) => {
    // Set the command in input and add topic prompt examples
    const featureName = command.replace("/", "").replace("briefing", "Briefing Doc").replace("audio", "Audio Overview").replace("mindmap", "Mind Map").replace("video", "Video Overview");
    const promptMessage = `${command} What topic would you like to generate?\n\nExamples:\n• ${command} quantum computing basics\n• ${command} history of world wars\n• ${command} machine learning fundamentals`;
    
    // Add a system message with examples
    const exampleMsg: Message = {
      id: generateId(),
      role: "assistant",
      content: promptMessage,
      timestamp: formatTime(),
    };
    setMessages((prev) => [...prev, exampleMsg]);
    
    // Set input to just the command
    setCurrentInput(command + " ");
    setSlashOpen(false);
  };

  const renderStudioContent = (job: StudioJob) => {
    if (job.status !== "ready" || !job.content_url) return null;

    switch (job.feature_type) {
      case "briefing":
      case "audio":
        // Handle case where audio was generated but URL not extractable
        if (job.content_url === "audio_generated") {
          return (
            <div className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500/10">
                  <span className="text-green-500">✓</span>
                </div>
                <div>
                  <div className="text-sm font-medium">
                    {job.feature_type === "briefing" ? "Briefing Doc" : "Audio Overview"} Generated
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Audio has been generated in NotebookLM. Check the Studio panel to listen.
                  </div>
                </div>
              </div>
            </div>
          );
        }
        return (
          <AudioPlayer
            src={job.content_url}
            title={job.feature_type === "briefing" ? "Briefing Doc" : "Audio Overview"}
            onDownload={() => window.open(job.content_url, "_blank")}
          />
        );
      case "video":
        return (
          <VideoPlayer
            src={job.content_url}
            title="Video Overview"
            onDownload={() => window.open(job.content_url, "_blank")}
          />
        );
      case "mindmap":
        return (
          <MindMapViewer
            svgData={job.content_url.startsWith("<svg") ? job.content_url : undefined}
            imageUrl={!job.content_url.startsWith("<svg") ? job.content_url : undefined}
            title="Mind Map"
            onDownload={() => {
              const link = document.createElement("a");
              link.href = job.content_url!;
              link.download = "mindmap.png";
              link.click();
            }}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />

      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-12 items-center justify-between border-b border-border bg-background px-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-muted md:hidden"
            >
              {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
            <h1 className="text-sm font-semibold">Nexa Chat</h1>
          </div>
          <div className="flex items-center gap-3">
            <NotebookSelector selectedNotebook={selectedNotebook} onSelect={setSelectedNotebook} />
            <StatusIndicator />
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 && studioJobs.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                <span className="text-xl">💬</span>
              </div>
              <h2 className="mb-1 text-sm font-semibold">Ask NotebookLM anything</h2>
              <p className="max-w-sm text-xs text-muted-foreground">
                Type your question in English, Roman Urdu, or any language.
                Use <code className="bg-muted px-1 py-0.5 rounded">/</code> for studio features.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {[
                  "Python seekhne ka tarika",
                  "Explain quantum computing",
                  "/briefing",
                  "/audio",
                  "/mindmap",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => handleSend(suggestion)}
                    className="rounded-lg border border-border bg-muted/50 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="py-4">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}

              {/* Render studio content */}
              {studioJobs.map((job) => (
                <div key={job.id} className="px-4 py-2">
                  {job.status === "generating" && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Generating {job.feature_type}...</span>
                    </div>
                  )}
                  {renderStudioContent(job)}
                </div>
              ))}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="relative">
          <ChatInput
            ref={inputRef}
            onSend={handleSend}
            onChange={handleInputChange}
            value={currentInput}
            disabled={loading}
          />

          <SlashCommandPopup
            isOpen={slashOpen}
            onClose={() => setSlashOpen(false)}
            onSelect={handleSlashSelect}
            position={slashPosition}
          />
        </div>
      </main>
    </div>
  );
}
