"use client";

import { useState } from "react";
import {
  Headphones,
  Video,
  GitBranch,
  FileText,
  Menu,
  X,
  Loader2,
  Sparkles,
} from "lucide-react";
import { Sidebar } from "@/components/sidebar";
import { StatusIndicator } from "@/components/status-indicator";
import { FilePickerModal } from "@/components/file-picker-modal";
import { StudioOptions } from "@/components/studio-options";
import { AudioPlayer } from "@/components/audio-player";
import { VideoPlayer } from "@/components/video-player";
import { MindMapViewer } from "@/components/mind-map-viewer";
import {
  useStudioGeneration,
  type FeatureType,
  type GenerationOptions,
} from "@/hooks/use-studio-generation";

interface StudioFeature {
  type: FeatureType;
  label: string;
  description: string;
  icon: typeof Headphones;
}

const features: StudioFeature[] = [
  {
    type: "audio-overview",
    label: "Audio Overview",
    description: "Generate podcast-style audio summaries of your content",
    icon: Headphones,
  },
  {
    type: "video-overview",
    label: "Video Overview",
    description: "Create AI-powered video overviews from your files",
    icon: Video,
  },
  {
    type: "mind-map",
    label: "Mind Map",
    description: "Visualize connections as interactive mind maps",
    icon: GitBranch,
  },
  {
    type: "briefing-doc",
    label: "Briefing Doc",
    description: "Get concise AI-generated briefing documents",
    icon: FileText,
  },
];

export default function StudioPage() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState<FeatureType | null>(
    null
  );
  const [showFilePicker, setShowFilePicker] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const [selectedFile, setSelectedFile] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [showResult, setShowResult] = useState(false);

  const { isGenerating, result, currentMessage, generate, reset } =
    useStudioGeneration();

  const handleFeatureClick = (type: FeatureType) => {
    setSelectedFeature(type);
    setShowFilePicker(true);
    setShowOptions(false);
    setShowResult(false);
    reset();
  };

  const handleFileConfirm = (fileId: string, fileName: string) => {
    setSelectedFile({ id: fileId, name: fileName });
    setShowFilePicker(false);
    setShowOptions(true);
  };

  const handleGenerate = async (options: GenerationOptions) => {
    if (!selectedFeature || !selectedFile) return;
    setShowOptions(false);
    await generate(selectedFeature, selectedFile.id, options);
    setShowResult(true);
  };

  const handleBackToFeatures = () => {
    setSelectedFeature(null);
    setShowFilePicker(false);
    setShowOptions(false);
    setShowResult(false);
    setSelectedFile(null);
    reset();
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-12 items-center justify-between border-b border-border bg-background px-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-muted md:hidden"
            >
              {mobileOpen ? (
                <X className="h-4 w-4" />
              ) : (
                <Menu className="h-4 w-4" />
              )}
            </button>
            <h1 className="text-sm font-semibold text-foreground">
              Nexa Studio
            </h1>
          </div>
          <StatusIndicator />
        </header>

        <div className="flex-1 overflow-y-auto">
          {/* Feature cards grid */}
          {!selectedFeature && !showResult && (
            <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8">
              <div className="mb-10 text-center">
                <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-3 py-1 text-xs text-muted-foreground">
                  <Sparkles className="h-3 w-3 text-primary" />
                  AI-Powered Studio
                </div>
                <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                  Create something with Studio
                </h2>
                <p className="mx-auto mt-2 max-w-xl text-sm text-muted-foreground">
                  Select a feature, pick your file, and let AI do the rest
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {features.map((feature) => {
                  const Icon = feature.icon;
                  return (
                    <button
                      key={feature.type}
                      onClick={() => handleFeatureClick(feature.type)}
                      className="group relative overflow-hidden rounded-2xl border border-border bg-card p-6 text-left transition-all hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5"
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                      <div className="relative">
                        <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                          <Icon className="h-5 w-5" />
                        </div>
                        <h3 className="mb-1 text-sm font-semibold text-foreground">
                          {feature.label}
                        </h3>
                        <p className="text-xs leading-relaxed text-muted-foreground">
                          {feature.description}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Generating state */}
          {isGenerating && (
            <div className="flex flex-col items-center justify-center py-24">
              <Loader2 className="mb-4 h-8 w-8 animate-spin text-primary" />
              <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-5 py-2.5 text-sm text-primary">
                {currentMessage}
              </div>
              <p className="mt-4 text-xs text-muted-foreground">
                Generating {selectedFeature?.replace("-", " ")}...
              </p>
            </div>
          )}

          {/* Result viewer */}
          {showResult && result && !isGenerating && (
            <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
              <div className="mb-6">
                <button
                  onClick={handleBackToFeatures}
                  className="mb-4 text-sm text-muted-foreground hover:text-foreground"
                >
                  &larr; Back to Studio
                </button>
                <h2 className="text-lg font-semibold text-foreground">
                  {result.title}
                </h2>
                {selectedFile && (
                  <p className="text-xs text-muted-foreground">
                    Source: {selectedFile.name}
                  </p>
                )}
              </div>

              <div className="flex items-center justify-center">
                {(result.type === "audio-overview" ||
                  result.type === "briefing-doc") && (
                  <AudioPlayer
                    src={result.url}
                    title={
                      result.type === "briefing-doc"
                        ? "Briefing Doc"
                        : "Audio Overview"
                    }
                  />
                )}
                {result.type === "video-overview" && (
                  <VideoPlayer
                    src={result.url}
                    title="Video Overview"
                  />
                )}
                {result.type === "mind-map" && <MindMapViewer />}
              </div>
            </div>
          )}

          {/* Back button during options flow */}
          {showOptions && !isGenerating && !showResult && (
            <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
              <button
                onClick={handleBackToFeatures}
                className="mb-6 text-sm text-muted-foreground hover:text-foreground"
              >
                &larr; Back to Studio
              </button>
            </div>
          )}
        </div>
      </main>

      {/* File picker modal */}
      {selectedFeature && showFilePicker && (
        <FilePickerModal
          onClose={() => {
            setShowFilePicker(false);
            setSelectedFeature(null);
          }}
          featureType={selectedFeature}
          onConfirm={handleFileConfirm}
        />
      )}

      {/* Generation options */}
      {selectedFeature && selectedFile && showOptions && !isGenerating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg">
            <StudioOptions
              featureType={selectedFeature}
              fileName={selectedFile.name}
              onBack={() => {
                setShowOptions(false);
                setShowFilePicker(true);
              }}
              onGenerate={handleGenerate}
              generating={isGenerating}
            />
          </div>
        </div>
      )}
    </div>
  );
}
