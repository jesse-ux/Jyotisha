"use client";

import Image from "next/image";
import { FormEvent, useState } from "react";

import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { selfHostedAuthActions } from "@/modules/identity/client";

type AuthProvider = "supabase" | "self-hosted";
type AuthMode = "otp" | "password" | "register" | "forgot";
type AuthStep = "email" | "otp" | "set-password" | "existing";

function authMessage(caught: unknown) {
  const message = caught instanceof Error ? caught.message : "暂时无法登录";
  const lower = message.toLowerCase();
  if (
    message.includes("Supabase") ||
    message.includes("environment") ||
    message.includes("URL")
  )
    return "Supabase 尚未配置";
  if (lower.includes("expired") || lower.includes("invalid"))
    return "验证码错误或已过期，请重新获取";
  if (lower.includes("rate limit")) return "发送过于频繁，请稍后再试";
  return message;
}

function passwordError(password: string, confirmation: string): string {
  if (password.length < 8 || password.length > 128) {
    return "密码长度须为 8–128 位";
  }
  if (password !== confirmation) return "两次输入的密码不一致";
  return "";
}

export function EmailOtpLogin({
  provider,
  passwordEnabled = false,
}: {
  provider: AuthProvider;
  passwordEnabled?: boolean;
}) {
  const [mode, setMode] = useState<AuthMode>("otp");
  const [step, setStep] = useState<AuthStep>("email");
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const canUsePassword = provider === "self-hosted" && passwordEnabled;
  const showLoginNavigation =
    canUsePassword && (mode === "otp" || mode === "password");
  const showBackToLogin =
    canUsePassword && (mode === "register" || mode === "forgot");

  function chooseMode(nextMode: AuthMode, nextNotice = "") {
    setMode(nextMode);
    setStep("email");
    setToken("");
    setPassword("");
    setConfirmation("");
    setError("");
    setNotice(nextNotice);
  }

  async function sendOtp(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const normalizedEmail = email.trim();
    if (!normalizedEmail || busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      if (provider === "self-hosted") {
        if (mode === "forgot") {
          await selfHostedAuthActions.requestPasswordReset(normalizedEmail);
        } else {
          await selfHostedAuthActions.send(normalizedEmail);
        }
      } else {
        const { error: otpError } =
          await createBrowserSupabaseClient().auth.signInWithOtp({
            email: normalizedEmail,
            options: { shouldCreateUser: true },
          });
        if (otpError) throw otpError;
      }
      setStep("otp");
      setNotice(
        mode === "forgot"
          ? "如果该邮箱可用，验证码已发送，请检查收件箱"
          : `验证码已发送至 ${normalizedEmail}`,
      );
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
      if (provider === "self-hosted") {
        await selfHostedAuthActions.verify(email, token);
        const hasPassword = await selfHostedAuthActions.hasPassword();
        if (!hasPassword) {
          setStep("set-password");
          setNotice("邮箱验证成功，请设置登录密码");
          return;
        }
        if (mode === "register") {
          setStep("existing");
          setNotice("此邮箱已有账户，您已登录；原密码未被更改");
          return;
        }
      } else {
        const { error: otpError } =
          await createBrowserSupabaseClient().auth.verifyOtp({
            email: email.trim(),
            token,
            type: "email",
          });
        if (otpError) throw otpError;
      }
      window.location.assign("/");
    } catch (caught) {
      if (!(caught instanceof Error)) throw caught;
      setError(authMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  async function signInWithPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim() || !password || busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await selfHostedAuthActions.signInWithPassword(email, password);
      window.location.assign("/");
    } catch (caught) {
      if (!(caught instanceof Error)) throw caught;
      setError(authMessage(caught));
      setBusy(false);
    }
  }

  async function saveFirstPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationError = passwordError(password, confirmation);
    if (validationError) {
      setError(validationError);
      return;
    }
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await selfHostedAuthActions.setPassword(password);
      window.location.assign("/");
    } catch (caught) {
      if (!(caught instanceof Error)) throw caught;
      const message = authMessage(caught);
      if (message.includes("原密码未被更改")) {
        setStep("existing");
        setNotice(message);
      } else {
        setError(message);
      }
      setBusy(false);
    }
  }

  async function resetPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationError = passwordError(password, confirmation);
    if (validationError) {
      setError(validationError);
      return;
    }
    if (!token || busy) return;
    setBusy(true);
    setError("");
    try {
      await selfHostedAuthActions.resetPassword(email, token, password);
      chooseMode("password", "密码已重置，请使用新密码登录");
    } catch (caught) {
      if (!(caught instanceof Error)) throw caught;
      setError(authMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  function changeEmail() {
    setStep("email");
    setToken("");
    setPassword("");
    setConfirmation("");
    setError("");
    setNotice("");
  }

  const title =
    mode === "register"
      ? "注册账号"
      : mode === "forgot"
        ? "忘记密码"
        : "欢迎回来";
  const intro =
    mode === "password"
      ? "使用邮箱和密码登录。"
      : mode === "register"
        ? "验证邮箱后设置密码，并自动登录。"
        : mode === "forgot"
          ? "通过邮箱验证码设置新密码，旧会话将失效。"
          : "邮箱验证码登录，新邮箱将自动创建账户。";

  return (
    <main className="standalone-page auth-page">
      <div className="auth-shell">
        <aside className="auth-story" aria-label="Jyotisha 简介">
          <div className="auth-story-brand">
            <Image
              src="/jyotish-logo.png"
              alt=""
              width={32}
              height={32}
              sizes="32px"
            />
            <strong>Jyotisha</strong>
          </div>
          <div>
            <p className="auth-kicker">Vedic astrology · 印度占星</p>
            <h2>
              在星图与当下之间，<br />找到可以行动的
              <span className="phrase-nowrap">线索。</span>
            </h2>
            <p>
              以出生资料为起点，讨论事业、关系与时间窗口。每一次解读都保留证据，也保留你的选择。
            </p>
          </div>
          <p className="auth-footnote">私密对话 · 云端同步 · 随时继续</p>
        </aside>

        <section className="auth-panel" aria-labelledby="login-title">
          <div className="auth-brand">
            <span aria-hidden="true" />
            <strong>Jyotisha</strong>
          </div>
          <h1 id="login-title">{title}</h1>
          <p className="page-intro">{intro}</p>

          {showLoginNavigation && (
            <nav className="auth-mode-nav" aria-label="登录方式">
              <div className="auth-mode-tabs">
                <button
                  type="button"
                  aria-pressed={mode === "otp"}
                  onClick={() => chooseMode("otp")}
                >
                  验证码登录
                </button>
                <button
                  type="button"
                  aria-pressed={mode === "password"}
                  onClick={() => chooseMode("password")}
                >
                  密码登录
                </button>
              </div>
              <div className="auth-links">
                <button type="button" onClick={() => chooseMode("register")}>
                  注册账号
                </button>
                <button type="button" onClick={() => chooseMode("forgot")}>
                  忘记密码
                </button>
              </div>
            </nav>
          )}

          {showBackToLogin && (
            <nav className="auth-links" aria-label="返回登录">
              <button type="button" onClick={() => chooseMode("otp")}>
                返回登录
              </button>
            </nav>
          )}

          {mode === "password" && step === "email" ? (
            <form
              key="password-login"
              className="stack-form auth-step"
              onSubmit={signInWithPassword}
            >
              <label htmlFor="password-email">邮箱</label>
              <input
                id="password-email"
                type="email"
                autoComplete="email"
                inputMode="email"
                required
                autoFocus
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setError("");
                }}
                placeholder="you@example.com"
              />
              <label htmlFor="current-password">密码</label>
              <input
                id="current-password"
                type="password"
                autoComplete="current-password"
                required
                minLength={8}
                maxLength={128}
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setError("");
                }}
              />
              <button
                className="button-primary"
                type="submit"
                disabled={!email.trim() || !password || busy}
              >
                {busy ? "登录中" : "密码登录"}
              </button>
            </form>
          ) : step === "email" ? (
            <form key="email" className="stack-form auth-step" onSubmit={sendOtp}>
              <label htmlFor="login-email">邮箱</label>
              <input
                id="login-email"
                type="email"
                autoComplete="email"
                inputMode="email"
                required
                autoFocus
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  setError("");
                  setNotice("");
                }}
                placeholder="you@example.com"
              />
              <button
                className="button-primary"
                type="submit"
                disabled={!email.trim() || busy}
              >
                {busy ? "发送中" : "发送验证码"}
              </button>
            </form>
          ) : step === "otp" && mode === "forgot" ? (
            <form
              key="reset-password"
              className="stack-form auth-step"
              onSubmit={resetPassword}
            >
              <label htmlFor="reset-token">邮箱验证码</label>
              <input
                id="reset-token"
                className="otp-input"
                type="text"
                autoComplete="one-time-code"
                inputMode="numeric"
                pattern="[0-9]*"
                minLength={6}
                maxLength={6}
                required
                autoFocus
                value={token}
                onChange={(event) => {
                  setToken(event.target.value.replace(/\D/g, "").slice(0, 6));
                  setError("");
                }}
              />
              <label htmlFor="reset-password-new">新密码</label>
              <input
                id="reset-password-new"
                type="password"
                autoComplete="new-password"
                minLength={8}
                maxLength={128}
                required
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setError("");
                }}
              />
              <label htmlFor="reset-password-confirm">确认新密码</label>
              <input
                id="reset-password-confirm"
                type="password"
                autoComplete="new-password"
                minLength={8}
                maxLength={128}
                required
                value={confirmation}
                onChange={(event) => {
                  setConfirmation(event.target.value);
                  setError("");
                }}
              />
              <button
                className="button-primary"
                type="submit"
                disabled={!token || !password || !confirmation || busy}
              >
                {busy ? "重置中" : "重置密码"}
              </button>
              <div className="inline-actions">
                <button type="button" disabled={busy} onClick={() => void sendOtp()}>
                  {busy ? "发送中" : "重新发送验证码"}
                </button>
                <button type="button" disabled={busy} onClick={changeEmail}>
                  更换邮箱
                </button>
              </div>
            </form>
          ) : step === "otp" ? (
            <form key="otp" className="stack-form auth-step" onSubmit={verifyOtp}>
              <label htmlFor="login-token">邮箱验证码</label>
              <input
                id="login-token"
                className="otp-input"
                type="text"
                autoComplete="one-time-code"
                inputMode="numeric"
                pattern="[0-9]*"
                minLength={6}
                maxLength={6}
                required
                autoFocus
                value={token}
                onChange={(event) => {
                  setToken(event.target.value.replace(/\D/g, "").slice(0, 6));
                  setError("");
                }}
              />
              <button
                className="button-primary"
                type="submit"
                disabled={!token || busy}
              >
                {busy ? "验证中" : "验证并登录"}
              </button>
              <div className="inline-actions">
                <button type="button" disabled={busy} onClick={() => void sendOtp()}>
                  {busy ? "发送中" : "重新发送验证码"}
                </button>
                <button type="button" disabled={busy} onClick={changeEmail}>
                  更换邮箱
                </button>
              </div>
            </form>
          ) : step === "set-password" ? (
            <form
              key="set-password"
              className="stack-form auth-step"
              onSubmit={saveFirstPassword}
            >
              <label htmlFor="new-password">设置密码</label>
              <input
                id="new-password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                maxLength={128}
                required
                autoFocus
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  setError("");
                }}
              />
              <label htmlFor="confirm-password">确认密码</label>
              <input
                id="confirm-password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                maxLength={128}
                required
                value={confirmation}
                onChange={(event) => {
                  setConfirmation(event.target.value);
                  setError("");
                }}
              />
              <button
                className="button-primary"
                type="submit"
                disabled={!password || !confirmation || busy}
              >
                {busy ? "保存中" : "设置密码并继续"}
              </button>
            </form>
          ) : (
            <div className="stack-form auth-step">
              <button
                className="button-primary"
                type="button"
                onClick={() => window.location.assign("/")}
              >
                进入首页
              </button>
            </div>
          )}

          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          {notice && (
            <p className="form-success" role="status">
              {notice}
            </p>
          )}
        </section>
      </div>
    </main>
  );
}
