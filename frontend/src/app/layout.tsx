import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Todo Manager",
  description: "Figma handoff implementation for Todo Manager"
};

const themeInitScript = `
(function () {
  try {
    var mode = window.localStorage.getItem("todo-manager-theme") || "system";
    if (mode !== "system" && mode !== "light" && mode !== "dark") mode = "system";
    var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    var theme = mode === "system" ? (prefersDark ? "dark" : "light") : mode;
    document.documentElement.dataset.themeMode = mode;
    document.documentElement.dataset.theme = theme;
  } catch (error) {
    document.documentElement.dataset.themeMode = "system";
    document.documentElement.dataset.theme = "light";
  }
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>{children}</body>
    </html>
  );
}
