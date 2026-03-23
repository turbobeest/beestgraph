import type { Metadata } from "next";

import Sidebar from "@/components/Sidebar";

import "./globals.css";

export const metadata: Metadata = {
  title: "beestgraph",
  description: "AI-augmented personal knowledge graph",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen antialiased">
        <Sidebar />
        <main className="min-h-screen pl-0 pt-14 md:pl-64 md:pt-0">
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
