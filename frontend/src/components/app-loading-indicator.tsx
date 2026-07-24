import type { ReactNode } from "react";

type AppLoadingIndicatorProps = Readonly<{
  title: string;
  detail: ReactNode;
  className?: string;
}>;

export function AppLoadingIndicator({ title, detail, className = "" }: AppLoadingIndicatorProps) {
  return (
    <div className={`app-loading-content${className ? ` ${className}` : ""}`}>
      <div className="app-loading-symbol" aria-hidden="true">
        <span className="app-loading-orbit" />
        <span className="app-loading-mark" />
      </div>
      <strong>{title}</strong>
      <span>{detail}</span>
    </div>
  );
}
