"use client";

import Image from "next/image";
import { FormEvent, useState } from "react";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";

function authMessage(caught: unknown) {
  const message = caught instanceof Error ? caught.message : "暂时无法登录";
  const lower = message.toLowerCase();
  if (message.includes("Supabase") || message.includes("environment") || message.includes("URL")) return "Supabase 尚未配置";
  if (lower.includes("expired") || lower.includes("invalid")) return "验证码错误或已过期，请重新获取";
  if (lower.includes("rate limit")) return "发送过于频繁，请稍后再试";
  return message;
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function sendOtp(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const normalizedEmail = email.trim();
    if (!normalizedEmail || busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const { error: otpError } = await createBrowserSupabaseClient().auth.signInWithOtp({
        email: normalizedEmail,
        options: { shouldCreateUser: true },
      });
      if (otpError) throw otpError;
      setSent(true);
      setNotice(`验证码已发送至 ${normalizedEmail}`);
    } catch (caught) {
      if (!(caught instanceof Error)) throw caught;
      setError(authMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function verifyOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || busy) return;
    setBusy(true);
    setError("");
    try {
      const { error: otpError } = await createBrowserSupabaseClient().auth.verifyOtp({
        email: email.trim(),
        token,
        type: "email",
      });
      if (otpError) throw otpError;
      window.location.assign("/");
    } catch (caught) {
      if (!(caught instanceof Error)) throw caught;
      setError(authMessage(caught));
      setBusy(false);
    }
  }

  function changeEmail() {
    setSent(false);
    setToken("");
    setError("");
    setNotice("");
  }

  return (
    <main className="standalone-page auth-page">
      <div className="auth-shell">
        <aside className="auth-story" aria-label="Jyotisha 简介">
          <div className="auth-story-brand">
            <Image src="/jyotish-logo.png" alt="" width={32} height={32} sizes="32px" />
            <strong>Jyotisha</strong>
          </div>
          <div>
            <p className="auth-kicker">Vedic astrology · 印度占星</p>
            <h2>在星图与当下之间，<br />找到可以行动的<span className="phrase-nowrap">线索。</span></h2>
            <p>以出生资料为起点，讨论事业、关系与时间窗口。每一次解读都保留证据，也保留你的选择。</p>
          </div>
          <p className="auth-footnote">私密对话 · 云端同步 · 随时继续</p>
        </aside>

        <section className="auth-panel" aria-labelledby="login-title">
          <div className="auth-brand"><span aria-hidden="true" /><strong>Jyotisha</strong></div>
          <h1 id="login-title">欢迎回来</h1>
          <p className="page-intro">邮箱验证码登录，<span className="phrase-nowrap">新邮箱将自动创建账户。</span></p>

          {!sent ? (
            <form key="email" className="stack-form auth-step" onSubmit={sendOtp}>
              <label htmlFor="login-email">邮箱</label>
              <input id="login-email" type="email" autoComplete="email" inputMode="email" required autoFocus value={email} onChange={(event) => { setEmail(event.target.value); setError(""); setNotice(""); }} placeholder="you@example.com" />
              <button className="button-primary" type="submit" disabled={!email.trim() || busy}>{busy ? "发送中" : "发送验证码"}</button>
            </form>
          ) : (
            <form key="otp" className="stack-form auth-step" onSubmit={verifyOtp}>
              <label htmlFor="login-token">邮箱验证码</label>
              <input id="login-token" className="otp-input" type="text" autoComplete="one-time-code" inputMode="numeric" pattern="[0-9]*" minLength={6} maxLength={6} required autoFocus value={token} onChange={(event) => { setToken(event.target.value.replace(/\D/g, "").slice(0, 6)); setError(""); }} />
              <button className="button-primary" type="submit" disabled={!token || busy}>{busy ? "验证中" : "验证并登录"}</button>
              <div className="inline-actions">
                <button type="button" disabled={busy} onClick={() => void sendOtp()}>{busy ? "发送中" : "重新发送验证码"}</button>
                <button type="button" disabled={busy} onClick={changeEmail}>更换邮箱</button>
              </div>
            </form>
          )}
          {error && <p className="form-error" role="alert">{error}</p>}
          {notice && <p className="form-success" role="status">{notice}</p>}
        </section>
      </div>
    </main>
  );
}
