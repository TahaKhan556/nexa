"use client";

import Link from "next/link";
import {
  Zap,
  Brain,
  Globe,
  MessageSquare,
  ChevronRight,
  Languages,
  History,
  Shield,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "AI Prompt Refinement",
    description:
      "Hermes (MiMo v2.5) automatically refines your prompts for optimal NotebookLM inference quality.",
  },
  {
    icon: Languages,
    title: "Multi-Language Support",
    description:
      "Type in Roman Urdu, Hindi, English, or any language — AI normalizes your query before execution.",
  },
  {
    icon: Globe,
    title: "Browser Automation",
    description:
      "Playwright-powered headless browser navigates NotebookLM, types prompts, and extracts responses.",
  },
  {
    icon: History,
    title: "Chat History",
    description:
      "All conversations saved locally. Browse past queries and responses anytime.",
  },
  {
    icon: Shield,
    title: "Single Account Access",
    description:
      "One managed Google account powers all requests. No individual auth needed.",
  },
  {
    icon: MessageSquare,
    title: "Real-time Status",
    description:
      "Live NotebookLM connection status. Know instantly if the system is ready.",
  },
];

const steps = [
  {
    step: "01",
    title: "Type your query",
    desc: "Write in any language — English, Roman Urdu, or mixed. Add source URLs if needed.",
  },
  {
    step: "02",
    title: "Hermes refines it",
    desc: "AI analyzes your intent, structures the prompt, and adds context for better results.",
  },
  {
    step: "03",
    title: "NotebookLM responds",
    desc: "Browser agent executes on NotebookLM, captures the response, and delivers it to you.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
              <Zap className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-mono text-sm font-bold tracking-tight">
              Nexa
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/chat"
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              Open Chat
            </Link>
            <Link
              href="/chat"
              className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative border-b border-border">
        <div className="mx-auto max-w-6xl px-4 py-24 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-3 py-1 text-xs text-muted-foreground">
            <Zap className="h-3 w-3 text-warning" />
            NotebookLM without the login
          </div>
          <h1 className="mb-4 text-4xl font-bold tracking-tight md:text-6xl">
            NotebookLM
            <br />
            <span className="text-primary">Proxy Portal</span>
          </h1>
          <p className="mx-auto mb-8 max-w-2xl text-muted-foreground">
            One portal. One account. Every user gets NotebookLM power without
            touching their own Google account. AI-refined prompts, browser
            automation, instant results.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              href="/chat"
              className="rounded-md bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              Start Chatting
            </Link>
            <Link
              href="#features"
              className="rounded-md border border-border px-6 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted"
            >
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-b border-border bg-muted/10">
        <div className="mx-auto max-w-6xl px-4 py-20">
          <div className="mb-12">
            <h2 className="mb-2 text-2xl font-bold">How it works</h2>
            <p className="text-sm text-muted-foreground">
              Three steps to NotebookLM access.
            </p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {steps.map((item) => (
              <div key={item.step} className="relative">
                <div className="mb-3 font-mono text-xs text-primary">
                  Step {item.step}
                </div>
                <h3 className="mb-1 text-sm font-semibold">{item.title}</h3>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-b border-border">
        <div className="mx-auto max-w-6xl px-4 py-20">
          <div className="mb-12">
            <h2 className="mb-2 text-2xl font-bold">Everything you need</h2>
            <p className="text-sm text-muted-foreground">
              Built for quick access to NotebookLM&apos;s AI capabilities.
            </p>
          </div>
          <div className="grid gap-px bg-border md:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="bg-background p-6 transition-colors hover:bg-muted/30"
              >
                <feature.icon className="mb-3 h-5 w-5 text-primary" />
                <h3 className="mb-1 text-sm font-semibold">{feature.title}</h3>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-b border-border">
        <div className="mx-auto max-w-6xl px-4 py-20 text-center">
          <h2 className="mb-2 text-2xl font-bold">Ready to get started?</h2>
          <p className="mb-6 text-sm text-muted-foreground">
            No signup. No auth. Just open the chat and start asking.
          </p>
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Open Nexa
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-muted/20">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-6">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-muted-foreground" />
            <span className="font-mono text-xs text-muted-foreground">
              Nexa
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            &copy; 2026 Nexa. Hobby project.
          </div>
        </div>
      </footer>
    </div>
  );
}
