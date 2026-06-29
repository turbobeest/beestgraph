import type { Metadata, Viewport } from "next";

import Sidebar from "@/components/Sidebar";

import "./globals.css";

export const metadata: Metadata = {
  title: "beestgraph",
  description: "AI-augmented personal knowledge graph",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    title: "beestgraph",
    statusBarStyle: "black-translucent",
  },
  icons: {
    apple: "/apple-touch-icon.png",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1.0,
  viewportFit: "cover",
  themeColor: "#101418",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `
  try {
    if (localStorage.getItem('beestgraph-dark-mode') === 'true' ||
        (!localStorage.getItem('beestgraph-dark-mode') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    }
  } catch (e) {}
` }} />
      </head>
      <body className="min-h-screen antialiased">
        <Sidebar />
        <main className="min-h-screen pt-[36px]">
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
