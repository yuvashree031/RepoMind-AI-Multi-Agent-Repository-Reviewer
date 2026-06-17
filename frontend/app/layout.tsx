import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RepoMind AI – Multi-Agent Repository Reviewer",
  description: "Automated AI-powered code auditing, security scanning, system design mapping, and DevOps reviews orchestrated by LangGraph.",
};

import Header from "./Header";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#09090b] text-[#fafafa] min-h-screen flex flex-col`}
      >
        
        <div className="ambient-glow top-[-200px] left-[-200px]" />
        <div className="ambient-glow bottom-[-200px] right-[-200px] bg-indigo-500/10" />

        
        <Header />

        
        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative">
          {children}
        </main>

        
        <footer className="border-t border-zinc-900 bg-[#09090b] py-8 text-center text-xs text-zinc-500">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              &copy; 2026 RepoMind AI. Yuvashree R
            </div>
            <div className="flex items-center gap-3">
              <span className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded">Next.js 15</span>
              <span className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded">FastAPI</span>
              <span className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded">LangGraph</span>
              <span className="px-2 py-1 bg-zinc-900 border border-zinc-800 rounded">Gemini API</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
