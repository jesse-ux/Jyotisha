import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import "./birth-time-choice.css";

export const metadata: Metadata = {
  title: "Jyotisha · 印度占星",
  description: "与 Mastra Agent 对话，基于星盘证据讨论事业、关系与时间窗口。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const enableReactDevTools = process.env.NODE_ENV === "development"
    && process.env.NEXT_PUBLIC_ENABLE_REACT_DEVTOOLS === "1";

  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        {enableReactDevTools && (
          <>
            <Script
              crossOrigin="anonymous"
              src="https://unpkg.com/react-grab/dist/index.global.js"
              strategy="lazyOnload"
            />
            <Script
              crossOrigin="anonymous"
              src="https://unpkg.com/react-scan/dist/auto.global.js"
              strategy="lazyOnload"
            />
          </>
        )}
      </head>
      <body>{children}</body>
    </html>
  );
}
