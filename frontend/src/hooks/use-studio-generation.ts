"use client";

import { useState, useEffect, useCallback } from "react";

export type FeatureType = "audio-overview" | "video-overview" | "mind-map" | "briefing-doc";

export interface GenerationOptions {
  format?: string;
  style?: string;
  customPrompt?: string;
}

export interface GenerationResult {
  type: FeatureType;
  url: string;
  title: string;
}

const LOADING_MESSAGES = [
  "we are cooking your file",
  "sabr ka phal metha hota hai ( Team B ;) )",
  "bss hogaya yr ghussa mt krna",
];

function getMockResult(type: FeatureType): GenerationResult {
  switch (type) {
    case "audio-overview":
      return { type, url: "#", title: "Audio Overview" };
    case "video-overview":
      return { type, url: "#", title: "Video Overview" };
    case "mind-map":
      return { type, url: "#", title: "Mind Map" };
    case "briefing-doc":
      return { type, url: "#", title: "Briefing Doc" };
  }
}

export async function runStudioFeature(
  type: FeatureType,
  _fileId: string,
  _options?: GenerationOptions
): Promise<GenerationResult> {
  await new Promise((resolve) => setTimeout(resolve, 15000));
  return getMockResult(type);
}

export function useStudioGeneration() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

  useEffect(() => {
    if (!isGenerating) {
      setCurrentMessageIndex(0);
      return;
    }
    const interval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [isGenerating]);

  const generate = useCallback(
    async (type: FeatureType, fileId: string, options?: GenerationOptions) => {
      setIsGenerating(true);
      setResult(null);
      try {
        const res = await runStudioFeature(type, fileId, options);
        setResult(res);
        return res;
      } finally {
        setIsGenerating(false);
      }
    },
    []
  );

  const reset = useCallback(() => {
    setIsGenerating(false);
    setResult(null);
    setCurrentMessageIndex(0);
  }, []);

  return {
    isGenerating,
    result,
    currentMessage: LOADING_MESSAGES[currentMessageIndex],
    generate,
    reset,
  };
}
