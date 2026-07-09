"use client";

import { useState, useRef, useEffect, forwardRef } from "react";
import { Send, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  onChange?: (value: string) => void;
  value?: string;
  disabled?: boolean;
}

export const ChatInput = forwardRef<HTMLTextAreaElement, ChatInputProps>(
  ({ onSend, onChange, value: externalValue, disabled }, ref) => {
    const [internalMessage, setInternalMessage] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Use external value if provided, otherwise use internal state
    const message = externalValue !== undefined ? externalValue : internalMessage;
    const setMessage = (val: string) => {
      if (externalValue !== undefined) {
        onChange?.(val);
      } else {
        setInternalMessage(val);
      }
    };

    useEffect(() => {
      const textarea = ref instanceof HTMLTextAreaElement ? ref : textareaRef.current;
      if (textarea) {
        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
      }
    }, [message, ref]);

    const handleSubmit = () => {
      if (!message.trim() || disabled) return;
      onSend(message.trim());
      setMessage("");
      const textarea = ref instanceof HTMLTextAreaElement ? ref : textareaRef.current;
      if (textarea) {
        textarea.style.height = "auto";
      }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    };

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setMessage(e.target.value);
    };

    return (
      <div className="border-t border-border bg-background p-4">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-2 rounded-xl border border-border bg-card p-2">
            <textarea
              ref={(node) => {
                textareaRef.current = node;
                if (typeof ref === "function") {
                  ref(node);
                } else if (ref) {
                  ref.current = node;
                }
              }}
              value={message}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask NotebookLM anything... (Use / for studio features)"
              disabled={disabled}
              rows={1}
              className="flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50"
            />
            <button
              onClick={handleSubmit}
              disabled={!message.trim() || disabled}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {disabled ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </div>
          <p className="mt-2 text-center text-[10px] text-muted-foreground">
            Powered by MiMo v2.5 via Hermes + NotebookLM Browser Agent
          </p>
        </div>
      </div>
    );
  }
);

ChatInput.displayName = "ChatInput";
