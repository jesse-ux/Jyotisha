import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Jyotisha · 印度占星对话",
  description: "与 Mastra Agent 对话，基于星盘证据讨论事业、关系与时间窗口。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
