"use client";

import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/graph3d.html", label: "3D Graph" },
  { href: "/wiki.html", label: "Wiki" },
  { href: "/dashboard.html", label: "Dashboard" },
  { href: "/queue", label: "Queue" },
  { href: "/entry", label: "New Entry" },
];

const EXTERNAL_LINKS = [
  { href: "https://en.wikipedia.org/wiki/Knowledge_graph", label: "Wikipedia", icon: "globe" },
  { href: "https://obsidian.md", label: "Obsidian", icon: "layers" },
  { href: "https://keep.md", label: "keep.md", icon: "bookmark" },
  { href: "https://github.com/turbobeest/beestgraph", label: "GitHub", icon: "github" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: 36,
        display: "flex",
        alignItems: "center",
        zIndex: 150,
        background: "rgba(6,10,19,0.95)",
        borderBottom: "1px solid rgba(100,116,139,0.15)",
        backdropFilter: "blur(12px)",
      }}
    >
      {/* Brand */}
      <div
        style={{
          padding: "0 16px",
          fontSize: 13,
          fontWeight: 700,
          color: "#f1f5f9",
          borderRight: "1px solid rgba(100,116,139,0.15)",
          height: "100%",
          display: "flex",
          alignItems: "center",
          fontFamily: "-apple-system, 'Segoe UI', sans-serif",
        }}
      >
        beestgraph
      </div>

      {/* Nav links */}
      {NAV_LINKS.map((item) => {
        const isActive = pathname === item.href;
        return (
          <a
            key={item.href}
            href={item.href}
            style={{
              padding: "0 14px",
              height: "100%",
              display: "flex",
              alignItems: "center",
              color: isActive ? "#60a5fa" : "#64748b",
              textDecoration: "none",
              fontSize: 10,
              letterSpacing: 0.5,
              textTransform: "uppercase",
              borderBottom: isActive ? "2px solid #3b82f6" : "2px solid transparent",
              fontFamily: "-apple-system, 'Segoe UI', sans-serif",
            }}
          >
            {item.label}
          </a>
        );
      })}

      {/* Right side — external links */}
      <div
        style={{
          marginLeft: "auto",
          display: "flex",
          alignItems: "center",
          height: "100%",
        }}
      >
        {EXTERNAL_LINKS.map((item) => (
          <a
            key={item.href}
            href={item.href}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              padding: "0 10px",
              height: "100%",
              display: "flex",
              alignItems: "center",
              gap: 4,
              color: "#64748b",
              textDecoration: "none",
              fontSize: 9,
              letterSpacing: 0.3,
              fontFamily: "-apple-system, 'Segoe UI', sans-serif",
            }}
          >
            <ExternalIcon type={item.icon} />
            {item.label}
          </a>
        ))}
      </div>
    </nav>
  );
}

function ExternalIcon({ type }: { type: string }) {
  switch (type) {
    case "globe":
      return (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
      );
    case "layers":
      return (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
      );
    case "bookmark":
      return (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
        </svg>
      );
    case "github":
      return (
        <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
        </svg>
      );
    default:
      return null;
  }
}
