"use client";

import { useState } from "react";
import { ArrowLeft, Sparkles } from "lucide-react";
import type { FeatureType, GenerationOptions } from "@/hooks/use-studio-generation";

interface StudioOptionsProps {
  featureType: FeatureType;
  fileName: string;
  onBack: () => void;
  onGenerate: (options: GenerationOptions) => void;
  generating: boolean;
}

export function StudioOptions({
  featureType,
  fileName,
  onBack,
  onGenerate,
  generating,
}: StudioOptionsProps) {
  const [format, setFormat] = useState("deep-dive");
  const [style, setStyle] = useState("professional");
  const [customPrompt, setCustomPrompt] = useState("");

  const isAudio = featureType === "audio-overview";
  const isVideo = featureType === "video-overview";
  const isMindMap = featureType === "mind-map";
  const isBriefing = featureType === "briefing-doc";

  const formatOptions =
    isAudio
      ? [
          { value: "deep-dive", label: "Deep Dive" },
          { value: "the-brief", label: "The Brief" },
        ]
      : [
          { value: "explainer", label: "Explainer" },
          { value: "cinematic", label: "Cinematic" },
        ];

  const styleOptions = ["Professional", "Casual", "Educational"];

  const handleGenerate = () => {
    const options: GenerationOptions = {};
    if (isAudio || isVideo) options.format = format;
    if (isVideo) options.style = style;
    if (customPrompt.trim()) options.customPrompt = customPrompt.trim();
    onGenerate(options);
  };

  return (
    <div className="mx-auto max-w-2xl">
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="mb-6 flex items-center gap-3">
          <button
            onClick={onBack}
            disabled={generating}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h2 className="text-sm font-semibold text-foreground capitalize">
              {featureType.replace("-", " ")}
            </h2>
            <p className="text-xs text-muted-foreground">{fileName}</p>
          </div>
        </div>

        <div className="space-y-5">
          {(isAudio || isVideo) && (
            <div>
              <label className="mb-2 block text-xs font-medium text-foreground">
                Format
              </label>
              <div className="flex gap-1 rounded-lg bg-muted p-1">
                {formatOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setFormat(opt.value)}
                    className={`flex-1 rounded-md px-3 py-2 text-xs font-medium transition-colors ${
                      format === opt.value
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {isVideo && (
            <div>
              <label className="mb-2 block text-xs font-medium text-foreground">
                Style
              </label>
              <div className="flex gap-2">
                {styleOptions.map((opt) => (
                  <button
                    key={opt}
                    onClick={() => setStyle(opt.toLowerCase())}
                    className={`flex-1 rounded-lg border px-3 py-2 text-xs font-medium transition-colors ${
                      style === opt.toLowerCase()
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border text-muted-foreground hover:bg-muted"
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {(isAudio || isVideo || isBriefing) && (
            <div>
              <label className="mb-2 block text-xs font-medium text-foreground">
                Custom prompt{" "}
                <span className="text-muted-foreground">(optional)</span>
              </label>
              <textarea
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Add any specific instructions..."
                rows={3}
                className="w-full resize-none rounded-lg border border-border bg-background px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
          )}

          {isMindMap && (
            <p className="text-sm text-muted-foreground">
              A mind map will be generated based on{" "}
              <span className="font-medium text-foreground">{fileName}</span>.
            </p>
          )}

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Sparkles className="h-4 w-4" />
            {generating ? "Generating..." : "Generate"}
          </button>
        </div>
      </div>
    </div>
  );
}
