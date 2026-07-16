"use client";

import Link from "next/link";
import { ArrowUp, ArrowUpRight, ChevronRight, Menu, Minus, Plus, Sparkles, X } from "lucide-react";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { ChatMessageContent } from "@/components/chat-message-content";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { chinaLocations, type ProvinceNode } from "@/data/china-locations";
import { keepFocusWithin } from "@/lib/focus-trap";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";

type Theme = "career" | "marriage" | "timing" | "general";
type Message = { role: "user" | "assistant"; text: string; suggestions?: string[] };
type Profile = {
  name: string;
  date: string;
  time: string;
  countryCode: "CN";
  provinceCode: string;
  cityCode: string;
  districtCode: string;
};
type ChatSession = { id: string; title: string; theme: Theme; messages: Message[]; updatedAt: number };
type RequestError = { sessionId: string; message: string };
type StreamingReply = { sessionId: string; text: string };
type BirthPlace = { label: string; lat: number; lon: number; tz: number };
type Account = { user: { id: string; email: string | null }; credits: number; isAdmin: boolean };
type OnboardingSuggestion = { theme: Exclude<Theme, "general">; text: string };
type OnboardingContent = { greeting: string; suggestions: OnboardingSuggestion[] };
type OnboardingStep = "name" | "birth" | "place";
type GreetingPeriod = "morning" | "noon" | "afternoon" | "evening" | "late-night";
const china = chinaLocations.country;

const themes: Array<{ id: Exclude<Theme, "general">; label: string; prompt: string }> = [
  { id: "career", label: "事业", prompt: "未来一年，事业和收入该关注什么？" },
  { id: "marriage", label: "关系", prompt: "我的关系模式是什么？" },
  { id: "timing", label: "时运", prompt: "未来哪些阶段值得把握？" },
];

const presetOnboardingMessage = "你好，我是 Jyotisha。\n开始前，我想先认识你。\n请问我该怎么称呼你？";

const greetingVariants: Record<GreetingPeriod, Array<(name: string) => string>> = {
  morning: [
    (name) => `早上好，${name}。今天最想先看什么？`,
    (name) => `${name}，早安。今天最该关注哪件事？`,
    (name) => `早上好，${name}。想从哪个问题开始？`,
  ],
  noon: [
    (name) => `中午好，${name}。现在最想理清哪件事？`,
    (name) => `${name}，中午好。什么问题最需要方向？`,
    (name) => `午间好，${name}。事业、关系或选择，想先聊哪个？`,
  ],
  afternoon: [
    (name) => `${name}，下午好。现在最想推进哪件事？`,
    (name) => `下午好，${name}。今天想先理清什么？`,
    (name) => `${name}，下午好。事业、关系或选择，想先聊哪个？`,
  ],
  evening: [
    (name) => `晚上好，${name}。今天最挂心的是哪件事？`,
    (name) => `${name}，晚上好。此刻最想聊哪件事？`,
    (name) => `晚上好，${name}。把心里的问题告诉我吧。`,
  ],
  "late-night": [
    (name) => `夜深了，${name}。此刻最想问什么？`,
    (name) => `${name}，还没休息吗？想从哪件事说起？`,
    (name) => `这么晚还醒着，${name}。直接说说最在意的问题吧。`,
  ],
};

function greetingPeriod(hour: number): GreetingPeriod {
  if (hour >= 5 && hour < 11) return "morning";
  if (hour >= 11 && hour < 14) return "noon";
  if (hour >= 14 && hour < 18) return "afternoon";
  if (hour >= 18 && hour < 23) return "evening";
  return "late-night";
}

function createStartGreeting(name: string, now = new Date()) {
  const displayName = name.trim() || "你好";
  const variants = greetingVariants[greetingPeriod(now.getHours())];
  return variants[Math.floor(Math.random() * variants.length)](displayName);
}

const emptyProfile: Profile = {
  name: "",
  date: "",
  time: "",
  countryCode: "CN",
  provinceCode: "",
  cityCode: "",
  districtCode: "",
};

function timestamp() {
  return Date.now();
}

function createSession(): ChatSession {
  return {
    id: globalThis.crypto.randomUUID(),
    title: "新对话",
    theme: "general",
    messages: [],
    updatedAt: timestamp(),
  };
}

function findProvince(code: string) {
  return china.provinces.find((province) => province.code === code);
}

function findCity(province: ProvinceNode | undefined, code: string) {
  return province?.cities.find((city) => city.code === code);
}

function selectedBirthPlace(profile: Profile): BirthPlace | null {
  const province = findProvince(profile.provinceCode);
  const city = findCity(province, profile.cityCode);
  if (!province || !city) return null;

  const district = city.districts.find((item) => item.code === profile.districtCode);
  if (city.districts.length > 0 && !district) return null;

  const location = district ?? city;
  const label = [china.name, province.name, city.name, district?.name]
    .filter((name, index, names) => Boolean(name) && names.indexOf(name) === index)
    .join(" · ");

  return { label, lat: location.center[1], lon: location.center[0], tz: china.timezone };
}

function missingProfileStep(profile: Profile): OnboardingStep | null {
  if (!profile.name.trim()) return "name";
  if (!profile.date || !profile.time) return "birth";
  if (!selectedBirthPlace(profile)) return "place";
  return null;
}

function birthQuestion(name: string) {
  return `${name}，你好。接下来请告诉我你的出生日期和时间。时间越准确，后面的判断越可靠。`;
}

function formatBirthMoment(profile: Profile) {
  const [year, month, day] = profile.date.split("-").map(Number);
  return `${year}年${month}月${day}日 ${profile.time}`;
}

function placeQuestion(profile: Profile) {
  return `记下了：${formatBirthMoment(profile)}。最后一个问题，你出生在哪里？`;
}

function completedOnboardingMessage(name: string) {
  return `${name}，我们可以开始了。你可以从下面三个方向选择，也可以直接告诉我现在最想问的事。`;
}

function completedOnboardingTranscript(profile: Profile, greeting: string): Message[] {
  const name = profile.name.trim();
  const birthPlace = selectedBirthPlace(profile);
  if (!name || !profile.date || !profile.time || !birthPlace) return [];

  return [
    { role: "assistant", text: presetOnboardingMessage },
    { role: "user", text: name },
    { role: "assistant", text: birthQuestion(name) },
    { role: "user", text: formatBirthMoment(profile) },
    { role: "assistant", text: placeQuestion(profile) },
    { role: "user", text: birthPlace.label },
    { role: "assistant", text: greeting || completedOnboardingMessage(name) },
  ];
}

function readSuggestions(value: unknown) {
  if (!Array.isArray(value)) return [];
  return [...new Set(value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.replace(/\s+/g, " ").trim().slice(0, 80))
    .filter(Boolean))].slice(0, 3);
}

function readOnboarding(value: unknown): OnboardingContent | null {
  if (!value || typeof value !== "object") return null;
  const payload = value as { greeting?: unknown; suggestions?: unknown };
  if (typeof payload.greeting !== "string" || !Array.isArray(payload.suggestions)) return null;

  const expectedThemes: OnboardingSuggestion["theme"][] = ["career", "marriage", "timing"];
  const suggestions = payload.suggestions.flatMap((item, index): OnboardingSuggestion[] => {
    if (!item || typeof item !== "object") return [];
    const suggestion = item as { theme?: unknown; text?: unknown };
    const theme = expectedThemes[index];
    if (!theme || suggestion.theme !== theme || typeof suggestion.text !== "string") return [];
    const text = suggestion.text.replace(/\s+/g, " ").trim().slice(0, 80);
    return text ? [{ theme, text }] : [];
  });

  const greeting = payload.greeting.replace(/\s+/g, " ").trim().slice(0, 180);
  return greeting.length >= 8 && suggestions.length === 3 ? { greeting, suggestions } : null;
}

function fallbackSuggestions(theme: Theme) {
  if (theme === "career") return ["我更适合怎样的职业路径？", "未来一年事业上要避开什么？", "我该如何发挥自己的优势？"];
  if (theme === "marriage") return ["我在关系里容易重复什么模式？", "怎样的伴侣更适合我？", "未来一年关系上要注意什么？"];
  if (theme === "timing") return ["接下来最值得把握的阶段是什么？", "哪些时期更适合主动行动？", "我现在应该优先准备什么？"];
  return themes.map((item) => item.prompt);
}

function parseAgentReply(value: string, theme: Theme) {
  let suggestions: string[] = [];
  const text = value.replace(/<!--AYANAM_SUGGESTIONS:(\[[\s\S]*?\])-->/g, (_, json: string) => {
    try {
      suggestions = readSuggestions(JSON.parse(json));
    } catch {
      suggestions = [];
    }
    return "";
  }).trim();
  return { text, suggestions: suggestions.length === 3 ? suggestions : fallbackSuggestions(theme) };
}

function readProfile(value: unknown): Profile {
  if (!value || typeof value !== "object") return emptyProfile;
  const profile = value as Partial<Profile> & {
    birth_date?: unknown;
    birth_time?: unknown;
    country_code?: unknown;
    province_code?: unknown;
    city_code?: unknown;
    district_code?: unknown;
  };
  const date = typeof profile.birth_date === "string" ? profile.birth_date : profile.date;
  const time = typeof profile.birth_time === "string" ? profile.birth_time.slice(0, 5) : profile.time;
  const provinceCode = typeof profile.province_code === "string" ? profile.province_code : profile.provinceCode;
  const cityCode = typeof profile.city_code === "string" ? profile.city_code : profile.cityCode;
  const districtCode = typeof profile.district_code === "string" ? profile.district_code : profile.districtCode;

  return {
    name: typeof profile.name === "string" ? profile.name.slice(0, 80) : "",
    date: typeof date === "string" ? date : "",
    time: typeof time === "string" ? time : "",
    countryCode: "CN",
    provinceCode: typeof provinceCode === "string" ? provinceCode : "",
    cityCode: typeof cityCode === "string" ? cityCode : "",
    districtCode: typeof districtCode === "string" ? districtCode : "",
  };
}

function readSessions(value: unknown): ChatSession[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const session = item as Partial<ChatSession> & { updated_at?: unknown };
    const messages = Array.isArray(session.messages)
      ? session.messages.flatMap((message) => (
        message && typeof message === "object"
          && ((message as Message).role === "user" || (message as Message).role === "assistant")
          && typeof (message as Message).text === "string"
          ? [{
            role: (message as Message).role,
            text: (message as Message).text.slice(0, 12000),
            suggestions: readSuggestions((message as Message).suggestions),
          }]
          : []
      ))
      : [];

    return typeof session.id === "string"
      ? [{
        id: session.id,
        title: typeof session.title === "string" ? session.title.slice(0, 36) : "新对话",
        theme: session.theme === "career" || session.theme === "marriage" || session.theme === "timing" ? session.theme : "general",
        messages,
        updatedAt: typeof session.updatedAt === "number"
          ? session.updatedAt
          : typeof session.updated_at === "string"
            ? Date.parse(session.updated_at)
            : timestamp(),
      }]
      : [];
  });
}

function BirthMomentFields({ value, onChange }: { value: Profile; onChange: (profile: Profile) => void }) {
  return (
    <div className="profile-grid">
      <label><span>出生日期</span><input required type="date" value={value.date} onChange={(event) => onChange({ ...value, date: event.target.value })} /></label>
      <label><span>出生时间</span><input required type="time" value={value.time} onChange={(event) => onChange({ ...value, time: event.target.value })} /></label>
    </div>
  );
}

function BirthLocationFields({ value, onChange }: { value: Profile; onChange: (profile: Profile) => void }) {
  const province = findProvince(value.provinceCode);
  const cities = province?.cities ?? [];
  const city = findCity(province, value.cityCode);
  const districts = city?.districts ?? [];

  return (
    <fieldset className="location-fieldset">
      <legend>出生地点</legend>
      <div className="location-grid">
        <label><span>国家 / 地区</span><select value={value.countryCode} onChange={() => onChange({ ...value, countryCode: "CN", provinceCode: "", cityCode: "", districtCode: "" })}><option value="CN">中国</option></select></label>
        <label><span>省 / 自治区</span><select required value={value.provinceCode} onChange={(event) => onChange({ ...value, provinceCode: event.target.value, cityCode: "", districtCode: "" })}><option value="" disabled>请选择省 / 自治区</option>{china.provinces.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
        <label><span>市 / 州</span><select required disabled={!province} value={value.cityCode} onChange={(event) => onChange({ ...value, cityCode: event.target.value, districtCode: "" })}><option value="" disabled>{province ? "请选择市 / 州" : "请先选择省 / 自治区"}</option>{cities.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
        <label><span>县 / 区</span><select required={districts.length > 0} disabled={!city || districts.length === 0} value={value.districtCode} onChange={(event) => onChange({ ...value, districtCode: event.target.value })}><option value="" disabled>{districts.length > 0 ? "请选择县 / 区" : "该地区无需继续选择"}</option>{districts.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
      </div>
    </fieldset>
  );
}

function ProfileFields({ value, onChange }: { value: Profile; onChange: (profile: Profile) => void }) {
  return (
    <>
      <label>
        <span>如何称呼你</span>
        <input required autoComplete="name" maxLength={80} placeholder="例如：林遥" value={value.name} onChange={(event) => onChange({ ...value, name: event.target.value })} />
      </label>
      <BirthMomentFields value={value} onChange={onChange} />
      <BirthLocationFields value={value} onChange={onChange} />
    </>
  );
}

function AgentAvatar() {
  return <span className="agent-avatar" aria-hidden="true" />;
}

function OnboardingChatMessage({ role, text, streaming = false, length = text.length }: { role: Message["role"]; text: string; streaming?: boolean; length?: number }) {
  const visibleText = streaming ? text.slice(0, length) : text;
  return (
    <article className={`message message-${role} onboarding-message`} aria-label={role === "assistant" ? "Jyotisha" : "你"}>
      {role === "assistant" && <AgentAvatar />}
      <div className="message-content">
        <div className="message-bubble">
          {role === "assistant" ? (
            streaming ? (
              <>
                <div className={`onboarding-stream ${length >= text.length ? "is-complete" : ""}`} aria-hidden="true"><ChatMessageContent text={visibleText} /></div>
                <span className="sr-only" aria-live="polite">{length >= text.length ? text : ""}</span>
              </>
            ) : <ChatMessageContent text={text} />
          ) : <p>{text}</p>}
        </div>
      </div>
    </article>
  );
}

function sessionTitle(question: string) {
  const normalized = question.replace(/\s+/g, " ").trim();
  return normalized.length > 22 ? `${normalized.slice(0, 22)}…` : normalized;
}

function isProfileComplete(profile: Profile) {
  return missingProfileStep(profile) === null;
}

function friendlyError(message: string) {
  return message.includes("Supabase") && (message.includes("配置") || message.includes("environment") || message.includes("URL"))
    ? "Supabase 尚未配置"
    : message;
}

function payloadMessage(payload: unknown, fallback: string) {
  if (!payload || typeof payload !== "object") return fallback;
  const data = payload as Record<string, unknown>;
  const message = [data.recovery, data.message, data.error].find((value) => typeof value === "string") as string | undefined;
  return friendlyError(message || fallback);
}

async function fetchAccount(signal?: AbortSignal): Promise<Account> {
  const response = await fetch("/api/account", { signal, cache: "no-store" });
  if (response.status === 401) {
    window.location.assign("/login");
    throw new Error("请先登录");
  }
  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new Error(payloadMessage(payload, "暂时无法读取账户信息"));
  return payload as Account;
}

export default function Home() {
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [profileDraft, setProfileDraft] = useState<Profile>(emptyProfile);
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [profileNotice, setProfileNotice] = useState("");
  const [account, setAccount] = useState<Account | null>(null);
  const [accountError, setAccountError] = useState("");
  const [redeemOpen, setRedeemOpen] = useState(false);
  const [redeemCode, setRedeemCode] = useState("");
  const [redeemError, setRedeemError] = useState("");
  const [redeemMessage, setRedeemMessage] = useState("");
  const [redeeming, setRedeeming] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState("");
  const [draft, setDraft] = useState("");
  const [pendingSessionId, setPendingSessionId] = useState<string | null>(null);
  const [streamingReply, setStreamingReply] = useState<StreamingReply | null>(null);
  const [requestError, setRequestError] = useState<RequestError | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [creatingSession, setCreatingSession] = useState(false);
  const [onboarding, setOnboarding] = useState<OnboardingContent | null>(null);
  const [onboardingError, setOnboardingError] = useState("");
  const [onboardingStep, setOnboardingStep] = useState<OnboardingStep>("name");
  const [onboardingJustCompleted, setOnboardingJustCompleted] = useState(false);
  const [startGreeting, setStartGreeting] = useState("");
  const [presetMessageLength, setPresetMessageLength] = useState(0);
  const conversationEnd = useRef<HTMLDivElement>(null);
  const accountTrigger = useRef<HTMLButtonElement>(null);
  const mobileMenuTrigger = useRef<HTMLButtonElement>(null);
  const sidebar = useRef<HTMLElement>(null);
  const sidebarCloseButton = useRef<HTMLButtonElement>(null);
  const profileDialog = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const redeemInput = useRef<HTMLInputElement>(null);
  const composerInput = useRef<HTMLTextAreaElement>(null);
  const uiPreview = useRef(false);

  const activeSession = sessions.find((session) => session.id === activeSessionId) ?? sessions[0];
  const activeError = requestError && requestError.sessionId === activeSession?.id ? requestError.message : "";
  const isLoading = pendingSessionId === activeSession?.id;
  const activeStreamingText = streamingReply && streamingReply.sessionId === activeSession?.id ? streamingReply.text : "";
  const activeSuggestions = activeSession?.messages.reduce((latest, message) => message.role === "assistant" && message.suggestions?.length ? message.suggestions : latest, [] as string[]) ?? [];
  const accountId = account?.user.id;
  const profileComplete = isProfileComplete(profile);
  const onboardingPending = profileComplete && !onboarding && !onboardingError;
  const currentOnboardingMessage = onboardingJustCompleted
    ? startGreeting || completedOnboardingMessage(profileDraft.name.trim())
    : onboardingStep === "birth"
      ? birthQuestion(profileDraft.name.trim())
      : onboardingStep === "place"
        ? placeQuestion(profileDraft)
        : presetOnboardingMessage;
  const shouldStreamOnboarding = !profileComplete || onboardingJustCompleted;
  const presetMessageFinished = !shouldStreamOnboarding || presetMessageLength >= currentOnboardingMessage.length;

  useEffect(() => {
    const controller = new AbortController();
    const bootstrapTimeout = window.setTimeout(() => {
      if (controller.signal.aborted) return;
      controller.abort();
      setAccountError("连接云端服务超时。请检查网络后重试，或返回登录页重新建立会话。");
      setHydrated(true);
    }, 8000);

    async function loadCloudData() {
      try {
        const previewMode = process.env.NODE_ENV === "development"
          ? new URLSearchParams(window.location.search).get("preview")
          : null;
        if (previewMode) {
          uiPreview.current = true;
          if (previewMode === "error") {
            setAccountError("连接云端服务超时。请检查网络后重试，或返回登录页重新建立会话。");
            setHydrated(true);
            return;
          }
          const previewProfile: Profile = previewMode === "onboarding"
            ? emptyProfile
            : {
              name: "林遥",
              date: "1990-06-15",
              time: "12:30",
              countryCode: "CN",
              provinceCode: "110000",
              cityCode: "110000-city",
              districtCode: "110101",
            };
          const previewMessages: Message[] = previewMode === "conversation"
            ? [
              { role: "user", text: "未来半年是否适合换工作？" },
              { role: "assistant", text: "可以先看职业方向、关键时间。\n同时评估现实风险。\n此处只展示本地预览，\n不调用真实星盘。", suggestions: ["先看事业方向", "再看关键时间", "评估现实风险"] },
            ]
            : [];
          const previewSession: ChatSession = {
            id: "preview-session",
            title: previewMessages.length > 0 ? "未来半年是否适合换工作" : "新对话",
            theme: "career",
            messages: previewMessages,
            updatedAt: timestamp(),
          };
          setAccount({ user: { id: "preview-user", email: "preview@local.test" }, credits: 8, isAdmin: false });
          setProfile(previewProfile);
          setProfileDraft(previewProfile);
          setOnboardingStep(missingProfileStep(previewProfile) ?? "name");
          setSessions([previewSession]);
          setActiveSessionId(previewSession.id);
          const previewGreeting = previewProfile.name.trim() ? createStartGreeting(previewProfile.name) : "";
          setStartGreeting(previewGreeting);
          setOnboarding(previewMode === "onboarding"
            ? null
            : { greeting: previewGreeting, suggestions: themes.map(({ id, prompt }) => ({ theme: id, text: prompt })) });
          setHydrated(true);
          return;
        }

        const supabase = createBrowserSupabaseClient();
        const { data: authData, error: authError } = await supabase.auth.getSession();
        if (authError) throw authError;
        if (controller.signal.aborted) return;
        if (!authData.session) {
          window.location.assign("/login");
          return;
        }

        const nextAccount = await fetchAccount(controller.signal);
        const [profileResult, sessionsResult] = await Promise.all([
          supabase
            .from("profiles")
            .select("name,birth_date,birth_time,country_code,province_code,city_code,district_code")
            .eq("id", nextAccount.user.id)
            .abortSignal(controller.signal)
            .maybeSingle(),
          supabase
            .from("chat_sessions")
            .select("id,title,theme,messages,updated_at")
            .abortSignal(controller.signal)
            .order("updated_at", { ascending: false }),
        ]);

        if (profileResult.error) throw profileResult.error;
        if (sessionsResult.error) throw sessionsResult.error;

        let nextSessions = readSessions(sessionsResult.data);
        if (nextSessions.length === 0) {
          if (controller.signal.aborted) return;
          const initialSession = createSession();
          const { error } = await supabase
            .from("chat_sessions")
            .insert({
              id: initialSession.id,
              user_id: nextAccount.user.id,
              title: initialSession.title,
              theme: initialSession.theme,
              messages: initialSession.messages,
              updated_at: new Date(initialSession.updatedAt).toISOString(),
            })
            .abortSignal(controller.signal);
          if (error) throw error;
          nextSessions = [initialSession];
        }

        if (controller.signal.aborted) return;
        const nextProfile = readProfile(profileResult.data);
        setAccount(nextAccount);
        setProfile(nextProfile);
        setProfileDraft(nextProfile);
        setStartGreeting(nextProfile.name.trim() ? createStartGreeting(nextProfile.name) : "");
        setOnboardingStep(missingProfileStep(nextProfile) ?? "name");
        setSessions(nextSessions);
        setActiveSessionId(nextSessions[0].id);
        setAccountError("");
      } catch (caught) {
        if ((caught as Error).name !== "AbortError" && !controller.signal.aborted) {
          setAccountError(friendlyError(caught instanceof Error ? caught.message : "暂时无法读取云端数据"));
        }
      } finally {
        window.clearTimeout(bootstrapTimeout);
        if (!controller.signal.aborted) setHydrated(true);
      }
    }

    void loadCloudData();
    return () => {
      window.clearTimeout(bootstrapTimeout);
      controller.abort();
    };
  }, []);

  useEffect(() => {
    if (!hydrated || !shouldStreamOnboarding) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      const frame = window.requestAnimationFrame(() => setPresetMessageLength(currentOnboardingMessage.length));
      return () => window.cancelAnimationFrame(frame);
    }

    const timer = window.setInterval(() => {
      setPresetMessageLength((current) => {
        const next = Math.min(current + 1, currentOnboardingMessage.length);
        if (next === currentOnboardingMessage.length) window.clearInterval(timer);
        return next;
      });
    }, 26);
    return () => window.clearInterval(timer);
  }, [currentOnboardingMessage, hydrated, shouldStreamOnboarding]);

  useEffect(() => {
    if (!hydrated || !accountId || !profileComplete || onboarding || onboardingError) return;
    const controller = new AbortController();
    const onboardingTimeout = window.setTimeout(() => {
      if (controller.signal.aborted) return;
      controller.abort();
      setOnboardingError("个性化入门问题准备超时");
    }, 12000);

    async function loadOnboarding() {
      try {
        const response = await fetch("/api/onboarding", {
          method: "POST",
          cache: "no-store",
          signal: controller.signal,
        });
        const payload = await response.json().catch(() => null);
        if (response.status === 401) {
          window.location.assign("/login");
          return;
        }
        if (!response.ok) throw new Error(payloadMessage(payload, "暂时无法准备初始问题"));
        const content = readOnboarding(payload);
        if (!content) throw new Error("Agent 返回的初始问题格式不正确");
        setOnboarding({ ...content, greeting: startGreeting || createStartGreeting(profile.name) });
        setOnboardingError("");
      } catch (caught) {
        if ((caught as Error).name !== "AbortError") {
          setOnboardingError(caught instanceof Error ? caught.message : "暂时无法准备初始问题");
        }
      }
    }

    void loadOnboarding();
    return () => {
      window.clearTimeout(onboardingTimeout);
      controller.abort();
    };
  }, [accountId, hydrated, onboarding, onboardingError, profile.name, profileComplete, startGreeting]);

  useEffect(() => {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    conversationEnd.current?.scrollIntoView({ behavior: isLoading || reduceMotion ? "auto" : "smooth", block: "end" });
  }, [activeSessionId, activeSession?.messages.length, activeStreamingText, isLoading, onboardingPending, onboardingStep, presetMessageFinished, profileComplete]);

  useEffect(() => {
    if (hydrated && accountId && !profileComplete && onboardingStep === "name" && presetMessageFinished && !profileOpen) {
      composerInput.current?.focus();
    }
  }, [accountId, hydrated, onboardingStep, presetMessageFinished, profileComplete, profileOpen]);

  useEffect(() => {
    if (!mobileSidebarOpen) return;
    window.requestAnimationFrame(() => sidebarCloseButton.current?.focus());
    const closeOnEscape = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileSidebarOpen(false);
        window.requestAnimationFrame(() => mobileMenuTrigger.current?.focus());
        return;
      }
      const container = sidebar.current;
      if (container) keepFocusWithin(event, container);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [mobileSidebarOpen]);

  useEffect(() => {
    if (!profileOpen) return;
    (redeemOpen ? redeemInput.current : closeButton.current)?.focus();
    const closeOnEscape = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        closeAccount();
        return;
      }
      const container = profileDialog.current;
      if (container) keepFocusWithin(event, container);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [profileOpen, redeemOpen]);

  async function refreshAccount() {
    try {
      setAccount(await fetchAccount());
      setAccountError("");
    } catch (caught) {
      setAccountError(caught instanceof Error ? caught.message : "暂时无法读取账户信息");
    }
  }

  function updateSession(sessionId: string, change: (session: ChatSession) => ChatSession) {
    setSessions((current) => current.map((session) => (session.id === sessionId ? change(session) : session)));
  }

  async function persistSession(session: ChatSession) {
    if (!account) throw new Error("账户尚未加载完成");
    if (process.env.NODE_ENV === "development" && uiPreview.current) return;
    const supabase = createBrowserSupabaseClient();
    const values = {
      title: session.title,
      theme: session.theme,
      messages: session.messages,
      updated_at: new Date(session.updatedAt).toISOString(),
    };
    const { data, error } = await supabase
      .from("chat_sessions")
      .update(values)
      .eq("id", session.id)
      .eq("user_id", account.user.id)
      .select("id")
      .maybeSingle();
    if (error) throw new Error(`云端同步失败：${error.message}`);
    if (data) return;

    const { error: insertError } = await supabase.from("chat_sessions").insert({
      id: session.id,
      user_id: account.user.id,
      ...values,
    });
    if (insertError) throw new Error(`云端同步失败：${insertError.message}`);
  }

  async function startNewChat() {
    if (!account || creatingSession) return;
    setMobileSidebarOpen(false);
    const nextSession = createSession();
    const previousSessionId = activeSession?.id ?? "";
    setCreatingSession(true);
    setSessions((current) => [nextSession, ...current]);
    setActiveSessionId(nextSession.id);
    setDraft("");
    setRequestError(null);
    try {
      await persistSession(nextSession);
    } catch (caught) {
      setSessions((current) => current.filter((session) => session.id !== nextSession.id));
      setActiveSessionId(previousSessionId);
      setRequestError({
        sessionId: previousSessionId,
        message: caught instanceof Error ? caught.message : "新对话未能保存到云端。",
      });
    } finally {
      setCreatingSession(false);
    }
  }

  function openAccount(showRedeem = false) {
    setMobileSidebarOpen(false);
    if (profileComplete) setProfileDraft(profile);
    setProfileNotice("");
    setRedeemOpen(showRedeem);
    setRedeemError("");
    setRedeemMessage("");
    setProfileOpen(true);
  }

  function closeAccount() {
    setProfileOpen(false);
    const returnTarget = window.matchMedia("(max-width: 767px)").matches
      ? mobileMenuTrigger.current
      : accountTrigger.current;
    window.requestAnimationFrame(() => returnTarget?.focus());
  }

  async function persistProfile(nextProfile: Profile) {
    if (!account) throw new Error("账户尚未加载完成");
    if (process.env.NODE_ENV === "development" && uiPreview.current) return;
    const birthPlace = selectedBirthPlace(nextProfile);
    const { data, error } = await createBrowserSupabaseClient()
      .from("profiles")
      .update({
        name: nextProfile.name.trim() || null,
        birth_date: nextProfile.date || null,
        birth_time: nextProfile.time || null,
        country_code: nextProfile.countryCode,
        province_code: nextProfile.provinceCode || null,
        city_code: nextProfile.cityCode || null,
        district_code: nextProfile.districtCode || null,
        latitude: birthPlace?.lat ?? null,
        longitude: birthPlace?.lon ?? null,
        timezone_offset: birthPlace?.tz ?? null,
        updated_at: new Date().toISOString(),
      })
      .eq("id", account.user.id)
      .select("id")
      .maybeSingle();
    if (error) throw error;
    if (!data) throw new Error("账户档案不存在，请重新登录后再试。");
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isProfileComplete(profileDraft) || !account || profileSaving) return;
    setProfileSaving(true);
    setProfileNotice("");
    setAccountError("");
    try {
      await persistProfile(profileDraft);
      setProfile(profileDraft);
      setProfileNotice("出生资料已保存到云端，可在同一账号的其他设备使用。");
    } catch (caught) {
      setAccountError(friendlyError(caught instanceof Error ? caught.message : "出生资料保存失败"));
    } finally {
      setProfileSaving(false);
    }
  }

  async function saveOnboardingName() {
    const name = draft.replace(/\s+/g, " ").trim().slice(0, 80);
    if (!name || !account || profileSaving) return;
    const nextProfile = { ...profileDraft, name };
    setProfileSaving(true);
    setAccountError("");
    try {
      await persistProfile(nextProfile);
      setProfile(nextProfile);
      setProfileDraft(nextProfile);
      setStartGreeting(createStartGreeting(nextProfile.name));
      setDraft("");
      setPresetMessageLength(0);
      const nextStep = missingProfileStep(nextProfile);
      if (nextStep) setOnboardingStep(nextStep);
      else setOnboardingJustCompleted(true);
    } catch (caught) {
      setAccountError(friendlyError(caught instanceof Error ? caught.message : "称呼保存失败"));
    } finally {
      setProfileSaving(false);
    }
  }

  async function saveOnboardingBirth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profileDraft.date || !profileDraft.time || !account || profileSaving) return;
    setProfileSaving(true);
    setAccountError("");
    try {
      await persistProfile(profileDraft);
      setProfile(profileDraft);
      setPresetMessageLength(0);
      const nextStep = missingProfileStep(profileDraft);
      if (nextStep) setOnboardingStep(nextStep);
      else setOnboardingJustCompleted(true);
    } catch (caught) {
      setAccountError(friendlyError(caught instanceof Error ? caught.message : "出生时间保存失败"));
    } finally {
      setProfileSaving(false);
    }
  }

  async function saveOnboardingPlace(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedBirthPlace(profileDraft) || !account || profileSaving) return;
    setProfileSaving(true);
    setAccountError("");
    try {
      await persistProfile(profileDraft);
      setProfile(profileDraft);
      setPresetMessageLength(0);
      setOnboardingJustCompleted(true);
    } catch (caught) {
      setAccountError(friendlyError(caught instanceof Error ? caught.message : "出生地点保存失败"));
    } finally {
      setProfileSaving(false);
    }
  }

  async function redeem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const code = redeemCode.trim();
    if (!code || redeeming) return;
    setRedeeming(true);
    setRedeemError("");
    setRedeemMessage("");
    try {
      const response = await fetch("/api/redeem", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ code }),
      });
      const payload = await response.json().catch(() => null);
      if (response.status === 401) {
        window.location.assign("/login");
        return;
      }
      if (!response.ok) throw new Error(payloadMessage(payload, "兑换码无效或已使用"));
      const result = payload as { credits: number; message?: string };
      setAccount((current) => current ? { ...current, credits: result.credits } : current);
      setRedeemCode("");
      setRedeemMessage(result.message || `兑换成功，当前余额 ${result.credits} 点。`);
    } catch (caught) {
      setRedeemError(caught instanceof Error ? caught.message : "兑换失败，请稍后重试");
    } finally {
      setRedeeming(false);
    }
  }

  async function signOut() {
    if (signingOut) return;
    setSigningOut(true);
    setAccountError("");
    try {
      const { error } = await createBrowserSupabaseClient().auth.signOut();
      if (error) throw error;
      window.location.assign("/login");
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "退出失败";
      setAccountError(friendlyError(message));
      setSigningOut(false);
    }
  }

  async function send(text: string, requestedTheme?: Theme) {
    const question = text.trim();
    if (!question || !activeSession || pendingSessionId || !account) return;

    if (account.credits <= 0) {
      openAccount(true);
      return;
    }

    if (!isProfileComplete(profile)) {
      setProfileDraft(profile);
      setProfileNotice("请先补充出生资料，才能进行星盘计算。");
      setRedeemOpen(false);
      setProfileOpen(true);
      return;
    }

    const birthPlace = selectedBirthPlace(profile);
    if (!birthPlace) return;

    const currentSession = activeSession;
    const theme = requestedTheme ?? currentSession.theme;
    const sessionId = currentSession.id;
    const [year, month, day] = profile.date.split("-").map(Number);
    const [hour, minute] = profile.time.split(":").map(Number);

    const preservedMessages = onboardingJustCompleted && currentSession.messages.length === 0
      ? completedOnboardingTranscript(profile, startGreeting)
      : currentSession.messages;
    const userSession: ChatSession = {
      ...currentSession,
      title: currentSession.messages.length === 0 ? sessionTitle(question) : currentSession.title,
      theme,
      messages: [...preservedMessages, { role: "user", text: question }],
      updatedAt: timestamp(),
    };
    setRequestError(null);
    setPendingSessionId(sessionId);

    if (process.env.NODE_ENV === "development" && uiPreview.current) {
      const previewSession: ChatSession = {
        ...userSession,
        messages: [...userSession.messages, {
          role: "assistant",
          text: "这是本地交互预览。正式对话会结合你的星盘证据继续分析。",
          suggestions: ["继续梳理方向", "查看时间窗口", "评估现实行动"],
        }],
        updatedAt: timestamp(),
      };
      updateSession(sessionId, () => previewSession);
      setDraft("");
      setPendingSessionId(null);
      return;
    }

    try {
      await persistSession(userSession);
    } catch (caught) {
      setRequestError({
        sessionId,
        message: `${caught instanceof Error ? caught.message : "消息未能保存到云端。"} 输入内容已保留，可直接重新发送。`,
      });
      setPendingSessionId(null);
      return;
    }

    setOnboardingJustCompleted(false);
    updateSession(sessionId, () => userSession);
    setDraft("");
    setStreamingReply({ sessionId, text: "" });
    try {
      const response = await fetch("/api/consult", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name: profile.name,
          year,
          month,
          day,
          hour,
          minute,
          city: birthPlace.label,
          lat: birthPlace.lat,
          lon: birthPlace.lon,
          tz: birthPlace.tz,
          theme,
          question,
          history: currentSession.messages.slice(-12).map((message) => ({
            role: message.role,
            text: message.text.slice(0, 4000),
          })),
        }),
      });
      if (!response.ok) {
        const contentType = response.headers.get("content-type") ?? "";
        const errorPayload = contentType.includes("application/json") ? await response.json() : { message: await response.text() };
        if (response.status === 401) window.location.assign("/login");
        if (response.status === 402) openAccount(true);
        throw new Error(payloadMessage(errorPayload, "服务暂时不可用"));
      }
      if (!response.body) throw new Error("浏览器未收到可读取的回答流");

      setAccount((current) => current ? { ...current, credits: Math.max(0, current.credits - 1) } : current);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let answer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        answer += decoder.decode(value, { stream: true });
        setStreamingReply({ sessionId, text: answer.split("<!--AYANAM_SUGGESTIONS:", 1)[0] });
      }
      answer += decoder.decode();
      if (!answer.trim()) throw new Error("Agent 没有返回内容，请重试。");
      const reply = parseAgentReply(answer, theme);
      if (!reply.text) throw new Error("Agent 没有返回可显示的回答，请重试。");

      const completedSession: ChatSession = {
        ...userSession,
        messages: [...userSession.messages, { role: "assistant", text: reply.text, suggestions: reply.suggestions }],
        updatedAt: timestamp(),
      };
      updateSession(sessionId, () => completedSession);
      try {
        await persistSession(completedSession);
      } catch (caught) {
        setRequestError({
          sessionId,
          message: `${caught instanceof Error ? caught.message : "云端同步失败"} 回答仍保留在当前页面，请复制保存后重试。`,
        });
      }
      void refreshAccount();
    } catch (caught) {
      setRequestError({
        sessionId,
        message: `${caught instanceof Error ? caught.message : "服务暂时不可用，请稍后重试。"} 本次提问已保留在对话中，可稍后重新提问。`,
      });
      void refreshAccount();
    } finally {
      setStreamingReply(null);
      setPendingSessionId(null);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profileComplete) {
      if (onboardingStep === "name" && presetMessageFinished) void saveOnboardingName();
      return;
    }
    void send(draft);
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  if (!hydrated || (!account && !accountError)) {
    return (
      <main className="app-loading" aria-busy="true" aria-live="polite">
        <div className="app-loading-content">
          <div className="app-loading-symbol" aria-hidden="true">
            <span className="app-loading-orbit" />
            <span className="app-loading-mark" />
          </div>
          <strong>正在和星星对口供</strong>
          <span>顺便同步你的账户与对话记录</span>
        </div>
      </main>
    );
  }

  if (!account) {
    return (
      <main className="app-loading app-loading-error" aria-live="assertive">
        <div className="app-loading-content">
          <strong>暂时无法进入 Jyotisha</strong>
          <span>{accountError}</span>
          <div className="app-loading-actions">
            <button className="button-primary" type="button" onClick={() => window.location.reload()}>重试</button>
            <Link className="button-secondary" href="/login">返回登录</Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className={`chat-app ${mobileSidebarOpen ? "sidebar-open" : ""}`}>
      <button className="sidebar-backdrop" tabIndex={-1} aria-label="关闭聊天记录" type="button" onClick={() => setMobileSidebarOpen(false)} />
      <aside className="sidebar" ref={sidebar} id="chat-sidebar" aria-label="对话导航" inert={profileOpen}>
        <div className="brand-row"><span className="brand-mark" aria-hidden="true" /><strong>Jyotisha</strong><button className="sidebar-close" ref={sidebarCloseButton} aria-label="关闭聊天记录" type="button" onClick={() => setMobileSidebarOpen(false)}><X aria-hidden="true" /></button></div>
        <button className="new-chat" type="button" onClick={() => void startNewChat()} disabled={!hydrated || !account || creatingSession || Boolean(pendingSessionId)}><Plus aria-hidden="true" /> {creatingSession ? "正在创建" : "新对话"}</button>
        <nav className="session-nav" aria-label="聊天记录">
          <span className="sidebar-label">聊天记录</span>
          <div className="session-list">
            {sessions.map((session) => (
              <button
                className={session.id === activeSession?.id ? "is-active" : ""}
                key={session.id}
                type="button"
                onClick={() => { setActiveSessionId(session.id); setDraft(""); setMobileSidebarOpen(false); }}
                aria-current={session.id === activeSession?.id ? "page" : undefined}
              >
                <span>{session.title}</span>
                {session.messages.length > 0 && <small>{session.messages.length} 条消息</small>}
              </button>
            ))}
          </div>
        </nav>
        <div className="sidebar-footer">
          <button className="profile-trigger" ref={accountTrigger} type="button" onClick={() => openAccount()}>
            <span className="profile-initial" aria-hidden="true">{profile.name.trim().slice(0, 1) || account?.user.email?.slice(0, 1).toUpperCase() || "你"}</span>
            <span><b>{profile.name.trim() || account?.user.email || "账户"}</b></span>
            <ChevronRight className="chevron" aria-hidden="true" />
          </button>
        </div>
      </aside>

      <section className="chat-panel" inert={profileOpen || mobileSidebarOpen}>
        <header className="chat-header">
          <button className="mobile-menu" ref={mobileMenuTrigger} aria-label="打开聊天记录" aria-controls="chat-sidebar" aria-expanded={mobileSidebarOpen} type="button" onClick={() => setMobileSidebarOpen(true)}><Menu aria-hidden="true" /></button>
          <div>
            <strong>{activeSession?.title || "新对话"}</strong>
            <span><i className={`status ${isLoading ? "status-loading" : "status-idle"}`} />{isLoading ? (activeStreamingText ? "正在回答" : "正在核对星盘信息") : "基于星盘证据回答"}</span>
          </div>
          <button className="credit-button" type="button" onClick={() => openAccount(account?.credits === 0)} aria-label={account ? `余额 ${account.credits} 点，打开账户与兑换码` : accountError || "读取余额中"}>
            <Sparkles className="credit-icon" aria-hidden="true" />
            <span>{account ? account.credits : "—"}</span>
          </button>
        </header>

        <div className={`conversation ${activeSession?.messages.length ? "" : "is-empty"}`}>
          {!activeSession?.messages.length ? (
            <div className="welcome">
              {!profileComplete || onboardingJustCompleted ? (
                <>
                  <OnboardingChatMessage role="assistant" text={presetOnboardingMessage} streaming={onboardingStep === "name" && !profileComplete} length={presetMessageLength} />
                  {(onboardingStep !== "name" || profileComplete) && <OnboardingChatMessage role="user" text={profileDraft.name.trim()} />}
                  {(onboardingStep !== "name" || profileComplete) && <OnboardingChatMessage role="assistant" text={birthQuestion(profileDraft.name.trim())} streaming={onboardingStep === "birth" && !profileComplete} length={presetMessageLength} />}
                  {(onboardingStep === "place" || profileComplete) && <OnboardingChatMessage role="user" text={formatBirthMoment(profileDraft)} />}
                  {(onboardingStep === "place" || profileComplete) && <OnboardingChatMessage role="assistant" text={placeQuestion(profileDraft)} streaming={onboardingStep === "place" && !profileComplete} length={presetMessageLength} />}
                  {profileComplete && onboardingJustCompleted && selectedBirthPlace(profileDraft) && <OnboardingChatMessage role="user" text={selectedBirthPlace(profileDraft)?.label ?? ""} />}
                  {profileComplete && onboardingJustCompleted && <OnboardingChatMessage role="assistant" text={currentOnboardingMessage} streaming length={presetMessageLength} />}
                </>
              ) : (
                <OnboardingChatMessage role="assistant" text={onboarding?.greeting
                  || (onboardingPending
                    ? `${profile.name.trim()}，稍等一下，我正在准备几个适合开始的问题。`
                    : startGreeting || `${profile.name.trim()}，从你此刻最关心的问题开始吧。`)} />
              )}

              {!profileComplete && onboardingStep === "birth" && presetMessageFinished && (
                <div className="onboarding-card-reveal">
                  <div className="onboarding-card-reveal-inner">
                    <form className="profile-form onboarding-card onboarding-step-card" onSubmit={saveOnboardingBirth}>
                      <div className="onboarding-card-heading"><b>出生时间</b><small>请选择日期和尽量准确的时间</small></div>
                      <BirthMomentFields value={profileDraft} onChange={setProfileDraft} />
                      {accountError && <p className="form-error" role="alert">{accountError}</p>}
                      <div className="onboarding-card-actions"><button className="button-primary" type="submit" disabled={profileSaving || !profileDraft.date || !profileDraft.time}>{profileSaving ? "保存中" : "确定"}</button></div>
                    </form>
                  </div>
                </div>
              )}

              {!profileComplete && onboardingStep === "place" && presetMessageFinished && (
                <div className="onboarding-card-reveal">
                  <div className="onboarding-card-reveal-inner">
                    <form className="profile-form onboarding-card onboarding-step-card" onSubmit={saveOnboardingPlace}>
                      <div className="onboarding-card-heading"><b>出生地点</b><small>目前先支持中国大陆地区</small></div>
                      <BirthLocationFields value={profileDraft} onChange={setProfileDraft} />
                      {accountError && <p className="form-error" role="alert">{accountError}</p>}
                      <div className="onboarding-card-actions"><button className="button-primary" type="submit" disabled={profileSaving || !selectedBirthPlace(profileDraft)}>{profileSaving ? "保存中" : "确定"}</button></div>
                    </form>
                  </div>
                </div>
              )}

              {!profileComplete && onboardingStep === "name" && accountError && <p className="form-error onboarding-inline-error" role="alert">{accountError}</p>}

              {profileComplete && presetMessageFinished && (onboardingPending ? (
                <div className="starter-loading" role="status">正在准备三个入门问题…</div>
              ) : (
                <div className="starter-list" aria-label="Jyotisha 推荐的初始问题">
                  {(onboarding?.suggestions ?? themes.map((item) => ({ theme: item.id, text: item.prompt }))).map((item) => {
                    const theme = themes.find((candidate) => candidate.id === item.theme);
                    return (
                      <button key={`${item.theme}-${item.text}`} type="button" disabled={!hydrated || Boolean(pendingSessionId) || !account} onClick={() => void send(item.text, item.theme)}>
                        <span className="starter-content"><b>{theme?.label || "开始"}</b><span>{item.text}</span></span>
                        <ArrowUpRight className="starter-arrow" aria-hidden="true" />
                      </button>
                    );
                  })}
                  {onboardingError && <p className="starter-note">Agent 的个性化入门问题暂时不可用，已显示安全的默认问题。</p>}
                </div>
              ))}
              <div ref={conversationEnd} />
            </div>
          ) : (
            <div className="message-list" aria-busy={isLoading}>
              <span className="sr-only" aria-live="polite">{isLoading ? "Jyotisha 正在回答" : ""}</span>
              {activeSession.messages.map((message, index) => (
                <article className={`message message-${message.role}`} key={`${message.role}-${index}`} aria-label={message.role === "assistant" ? "Jyotisha" : "你"}>
                  {message.role === "assistant" && <AgentAvatar />}
                  <div className="message-content">
                    <div className="message-bubble">
                      {message.role === "assistant" ? <ChatMessageContent text={message.text} /> : <p>{message.text}</p>}
                    </div>
                  </div>
                </article>
              ))}
              {isLoading && (
                <article className="message message-assistant" aria-label={activeStreamingText ? "Jyotisha 正在回答" : "Jyotisha 正在分析"}>
                  <AgentAvatar />
                  <div className="message-content">
                    <div className="message-bubble">
                      {activeStreamingText ? <ChatMessageContent text={activeStreamingText} /> : <div className="thinking"><i /><i /><i /></div>}
                    </div>
                  </div>
                </article>
              )}
              {activeError && <p className="error-message">{activeError}</p>}
              <div ref={conversationEnd} />
            </div>
          )}
        </div>

        <div className="composer-wrap">
          {activeSuggestions.length > 0 && (
            <div className="composer-suggestions" aria-label="推荐继续提问">
              {activeSuggestions.map((question) => (
                <button key={question} type="button" disabled={Boolean(pendingSessionId) || !account} onClick={() => void send(question)}>{question}</button>
              ))}
            </div>
          )}
          <form className="composer" onSubmit={submit}>
            <Textarea
              ref={composerInput}
              aria-label={!profileComplete && onboardingStep === "name" ? "输入你的称呼" : "输入你的问题"}
              placeholder={!account
                ? "正在读取账户…"
                : !profileComplete
                  ? onboardingStep === "name"
                    ? presetMessageFinished ? "输入你的称呼" : "Jyotisha 正在输入…"
                    : "请先完成上方资料"
                  : account.credits === 0
                    ? "余额不足，发送时将打开兑换码"
                    : "例如：未来半年是否适合换工作？"}
              rows={1}
              maxLength={!profileComplete && onboardingStep === "name" ? 80 : 500}
              disabled={!profileComplete && (onboardingStep !== "name" || !presetMessageFinished || profileSaving)}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleComposerKeyDown}
            />
            <Button aria-label={!profileComplete ? "确认称呼" : "发送"} disabled={!draft.trim() || Boolean(pendingSessionId) || !account || (!profileComplete && (onboardingStep !== "name" || !presetMessageFinished || profileSaving))} size="icon" type="submit">
              <ArrowUp aria-hidden="true" />
            </Button>
          </form>
          <p>{!profileComplete && onboardingStep === "name" ? "Enter 确认称呼" : "Enter 发送 · Shift + Enter 换行"}</p>
        </div>
      </section>

      <div className={`profile-overlay ${profileOpen ? "is-open" : ""}`} aria-hidden={!profileOpen} inert={!profileOpen} onMouseDown={closeAccount}>
        <section className="profile-dialog" ref={profileDialog} role="dialog" aria-modal="true" aria-labelledby="profile-title" onMouseDown={(event) => event.stopPropagation()}>
          <header>
            <h2 id="profile-title">账户与出生资料</h2>
            <button className="dialog-close" ref={closeButton} aria-label="关闭" type="button" onClick={closeAccount}><X aria-hidden="true" /></button>
          </header>

          <section className="account-summary" aria-label="账户信息">
            <div><span>邮箱</span><strong>{account?.user.email || "尚未读取"}</strong></div>
            <div><span>剩余点数</span><strong>{account?.credits ?? "—"}</strong></div>
          </section>
          {accountError && <p className="form-error" role="alert">{accountError}</p>}

          <section className="sheet-section">
            <button className="section-toggle" type="button" aria-expanded={redeemOpen} onClick={() => setRedeemOpen((current) => !current)}>
              <span><b>兑换点数</b><small>输入兑换码后余额会立即更新</small></span>{redeemOpen ? <Minus aria-hidden="true" /> : <Plus aria-hidden="true" />}
            </button>
            {redeemOpen && (
              <form className="redeem-form" onSubmit={redeem}>
                <label htmlFor="redeem-code">兑换码</label>
                <div>
                  <input id="redeem-code" ref={redeemInput} autoComplete="off" value={redeemCode} onChange={(event) => { setRedeemCode(event.target.value); setRedeemError(""); setRedeemMessage(""); }} placeholder="输入完整兑换码" />
                  <button className="button-primary" type="submit" disabled={!redeemCode.trim() || redeeming}>{redeeming ? "兑换中" : "兑换"}</button>
                </div>
                {redeemError && <p className="form-error" role="alert">{redeemError}</p>}
                {redeemMessage && <p className="form-success" role="status">{redeemMessage}</p>}
              </form>
            )}
          </section>

          <section className="sheet-section birth-section">
            <div className="section-heading"><b>出生资料</b><small>加密传输并保存到云端，用于此账号的所有对话</small></div>
            {profileNotice && <p className="form-success" role="status">{profileNotice}</p>}
            <form className="profile-form" onSubmit={saveProfile}>
              <ProfileFields value={profileDraft} onChange={setProfileDraft} />
              <button className="button-primary save-profile" type="submit" disabled={profileSaving || !account}>{profileSaving ? "保存中" : "保存出生资料"}</button>
            </form>
          </section>

          <footer className="account-actions">
            {account?.isAdmin && <Link className="button-secondary" href="/admin/codes">管理兑换码</Link>}
            <button className="button-secondary danger-button" type="button" onClick={() => void signOut()} disabled={signingOut}>{signingOut ? "正在退出" : "退出登录"}</button>
          </footer>
        </section>
      </div>
    </main>
  );
}
