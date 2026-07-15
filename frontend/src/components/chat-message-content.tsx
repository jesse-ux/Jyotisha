import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

const markdownComponents: Components = {
  a: ({ children, href, ...props }) => (
    <a {...props} href={href} rel="noreferrer" target="_blank">
      {children}
    </a>
  ),
  table: ({ children }) => (
    <div className="markdown-table">
      <table>{children}</table>
    </div>
  ),
};

export function ChatMessageContent({ text }: { text: string }) {
  return (
    <div className="message-markdown">
      <ReactMarkdown
        components={markdownComponents}
        remarkPlugins={[remarkGfm]}
        skipHtml
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
