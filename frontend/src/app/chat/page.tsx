"use client";

import { useState, useRef, useEffect } from "react";
import { Menu, X } from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { ChatInput } from "@/components/chat-input";
import { ChatMessage, Message } from "@/components/chat-message";
import { StatusIndicator } from "@/components/status-indicator";

function generateId() {
  return Math.random().toString(36).slice(2, 11);
}

function formatTime() {
  return new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (content: string) => {
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
        body: JSON.stringify({ message: content }),
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
          <StatusIndicator />
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                <span className="text-xl">💬</span>
              </div>
              <h2 className="mb-1 text-sm font-semibold">Ask NotebookLM anything</h2>
              <p className="max-w-sm text-xs text-muted-foreground">
                Type your question in English, Roman Urdu, or any language.
                Hermes will refine the prompt and NotebookLM will respond.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {[
                  "Python seekhne ka tarika",
                  "Explain quantum computing",
                  "https://example.com — summarize this",
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
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <ChatInput onSend={handleSend} disabled={loading} />
      </main>
    </div>
  );
}
