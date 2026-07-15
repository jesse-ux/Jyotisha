"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

type CodeRecord = {
  id: string;
  mask: string;
  credits: number;
  expiresAt: string | null;
  redeemedBy: string | null;
  redeemedEmail: string | null;
  redeemedAt: string | null;
  note: string | null;
  createdAt: string;
};
type GeneratedCode = { code: string; credits: number; expiresAt: string | null };

function apiMessage(payload: unknown, fallback: string) {
  if (!payload || typeof payload !== "object") return fallback;
  const data = payload as Record<string, unknown>;
  return [data.message, data.error].find((value) => typeof value === "string") as string || fallback;
}

function redirectForAuth(response: Response) {
  if (response.status === 401) window.location.assign("/login");
  if (response.status === 403) window.location.assign("/");
}

function codeStatus(code: CodeRecord) {
  if (code.redeemedAt) return "已兑换";
  if (code.expiresAt && new Date(code.expiresAt).getTime() <= Date.now()) return "已过期";
  return "可用";
}

function formatDate(value: string | null) {
  return value ? new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";
}

export default function AdminCodesPage() {
  const [codes, setCodes] = useState<CodeRecord[]>([]);
  const [generated, setGenerated] = useState<GeneratedCode[]>([]);
  const [credits, setCredits] = useState(10);
  const [count, setCount] = useState(1);
  const [expiresAt, setExpiresAt] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [copyNotice, setCopyNotice] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    void fetch("/api/admin/codes", { signal: controller.signal, cache: "no-store" })
      .then(async (response) => {
        redirectForAuth(response);
        const payload = await response.json().catch(() => null);
        if (!response.ok) throw new Error(apiMessage(payload, "暂时无法读取兑换码"));
        setCodes((payload as { codes: CodeRecord[] }).codes);
      })
      .catch((caught) => {
        if ((caught as Error).name !== "AbortError") setError(caught instanceof Error ? caught.message : "暂时无法读取兑换码");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  async function reloadCodes() {
    const response = await fetch("/api/admin/codes", { cache: "no-store" });
    redirectForAuth(response);
    const payload = await response.json().catch(() => null);
    if (!response.ok) throw new Error(apiMessage(payload, "暂时无法刷新兑换码"));
    setCodes((payload as { codes: CodeRecord[] }).codes);
  }

  async function createCodes(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (creating) return;
    setCreating(true);
    setError("");
    setGenerated([]);
    setCopyNotice("");
    try {
      const response = await fetch("/api/admin/codes", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          credits,
          count,
          ...(expiresAt ? { expiresAt: new Date(expiresAt).toISOString() } : {}),
          ...(note.trim() ? { note: note.trim() } : {}),
        }),
      });
      redirectForAuth(response);
      const payload = await response.json().catch(() => null);
      if (!response.ok) throw new Error(apiMessage(payload, "生成兑换码失败"));
      setGenerated((payload as { codes: GeneratedCode[] }).codes);
      await reloadCodes();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "生成兑换码失败");
    } finally {
      setCreating(false);
    }
  }

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopyNotice("已复制到剪贴板");
    } catch {
      setCopyNotice("无法自动复制，请手动选择兑换码");
    }
  }

  return (
    <main className="standalone-page admin-page">
      <header className="admin-header">
        <div><p className="page-eyebrow">管理员</p><h1>兑换码</h1></div>
        <Link className="button-secondary" href="/">返回对话</Link>
      </header>

      <div className="admin-scroll">
        <section className="admin-section" aria-labelledby="create-codes-title">
          <div className="section-title"><div><h2 id="create-codes-title">生成兑换码</h2><p>完整兑换码只在本次生成结果中显示，请立即复制保存。</p></div></div>
          <form className="code-form" onSubmit={createCodes}>
            <label><span>每个点数</span><input type="number" min={1} required value={credits} onChange={(event) => setCredits(Number(event.target.value))} /></label>
            <label><span>生成数量</span><input type="number" min={1} max={100} required value={count} onChange={(event) => setCount(Number(event.target.value))} /></label>
            <label><span>有效期 <em>可选</em></span><input type="datetime-local" value={expiresAt} onChange={(event) => setExpiresAt(event.target.value)} /></label>
            <label className="note-field"><span>备注 <em>可选</em></span><input maxLength={200} value={note} onChange={(event) => setNote(event.target.value)} placeholder="例如：7 月活动" /></label>
            <button className="button-primary" type="submit" disabled={creating || credits < 1 || count < 1 || count > 100}>{creating ? "生成中" : "生成"}</button>
          </form>
          {error && <p className="form-error" role="alert">{error}</p>}
        </section>

        {generated.length > 0 && (
          <section className="admin-section generated-section" aria-labelledby="generated-title">
            <div className="section-title">
              <div><h2 id="generated-title">本次生成的完整码</h2><p>离开或刷新页面后将不再显示。</p></div>
              <button className="button-secondary" type="button" onClick={() => void copy(generated.map((item) => item.code).join("\n"))}>复制全部</button>
            </div>
            <div className="generated-list">
              {generated.map((item) => (
                <div key={item.code}><code>{item.code}</code><span>{item.credits} 点</span><button type="button" onClick={() => void copy(item.code)}>复制</button></div>
              ))}
            </div>
            {copyNotice && <p className="form-success" role="status">{copyNotice}</p>}
          </section>
        )}

        <section className="admin-section" aria-labelledby="codes-list-title">
          <div className="section-title"><div><h2 id="codes-list-title">兑换码状态</h2><p>{loading ? "正在读取…" : `${codes.length} 条记录`}</p></div></div>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead><tr><th>兑换码</th><th>点数</th><th>状态</th><th>有效期</th><th>兑换账户</th><th>兑换时间</th><th>备注</th><th>创建时间</th></tr></thead>
              <tbody>
                {codes.map((code) => (
                  <tr key={code.id}>
                    <td><code>{code.mask}</code></td><td>{code.credits}</td><td><span className={`code-status status-${codeStatus(code)}`}>{codeStatus(code)}</span></td><td>{formatDate(code.expiresAt)}</td><td>{code.redeemedEmail || code.redeemedBy || "—"}</td><td>{formatDate(code.redeemedAt)}</td><td>{code.note || "—"}</td><td>{formatDate(code.createdAt)}</td>
                  </tr>
                ))}
                {!loading && codes.length === 0 && <tr><td colSpan={8} className="empty-cell">尚未生成兑换码</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  );
}
