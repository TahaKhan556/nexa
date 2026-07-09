"use client";

import { useRef, useState } from "react";
import {
  Play,
  Pause,
  Maximize,
  Minimize,
  Download,
} from "lucide-react";

interface VideoPlayerProps {
  src: string;
  title: string;
  onDownload?: () => void;
}

export function VideoPlayer({ src, title, onDownload }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (playing) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setPlaying(!playing);
  };

  const toggleFullscreen = async () => {
    if (!containerRef.current) return;
    if (isFullscreen) {
      await document.exitFullscreen();
      setIsFullscreen(false);
    } else {
      await containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    }
  };

  return (
    <div className="mx-auto w-full max-w-4xl">
      <div
        ref={containerRef}
        className="group relative overflow-hidden rounded-2xl border border-border bg-black"
      >
        <video
          ref={videoRef}
          src={src}
          className="aspect-video w-full"
          onEnded={() => setPlaying(false)}
          playsInline
        />

        {/* Overlay controls */}
        <div className="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100">
          <div className="flex items-center justify-between px-4 pb-4">
            <div className="flex items-center gap-3">
              <button
                onClick={togglePlay}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-white backdrop-blur transition-colors hover:bg-white/30"
              >
                {playing ? (
                  <Pause className="h-5 w-5" />
                ) : (
                  <Play className="h-5 w-5 translate-x-0.5" />
                )}
              </button>
              <span className="text-sm font-medium text-white drop-shadow">
                {title}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {onDownload && (
                <button
                  onClick={onDownload}
                  className="rounded-md p-2 text-white/80 hover:bg-white/20 hover:text-white"
                >
                  <Download className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={toggleFullscreen}
                className="rounded-md p-2 text-white/80 hover:bg-white/20 hover:text-white"
              >
                {isFullscreen ? (
                  <Minimize className="h-4 w-4" />
                ) : (
                  <Maximize className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Center play button when paused */}
        {!playing && (
          <div className="absolute inset-0 flex items-center justify-center">
            <button
              onClick={togglePlay}
              className="flex h-16 w-16 items-center justify-center rounded-full bg-primary shadow-lg transition-transform hover:scale-105"
            >
              <Play className="h-7 w-7 translate-x-0.5 text-primary-foreground" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
