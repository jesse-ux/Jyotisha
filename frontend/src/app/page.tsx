"use client";

import Link from "next/link";
import { ArrowUp, ArrowUpRight, ChevronRight, Menu, Minus, Plus, Sparkles, Square, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { ChatMessageContent } from "@/components/chat-message-content";
import { ModelSelector } from "@/components/model-selector";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { chinaLocations, type ProvinceNode } from "@/data/china-locations";
import { parseAgentReply, type ReplyTheme } from "@/lib/agent-reply";
import { keepFocusWithin } from "@/lib/focus-trap";
import {
  SessionModelPersistenceQueue,
  persistSessionModelSelection,
} from "@/lib/session-model-persistence";
import {
  parsePublicModelCatalog,
  resolveSessionModelId,
  type PublicLanguageModelCatalog,
} from "@/lib/public-models";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";

type Theme = ReplyTheme;
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
type ChartLibraryRecord = {
  id: string;
  role: "self" | "other";
  profile: Profile;
  updatedAt: number;
};
type ChartLibraryApiRecord = {
  id: string;
  role: "self" | "other";
  profile: Profile;
  updated_at?: string;
};
type SynastryReportCard = {
  id: string;
  partnerName: string;
  score?: number;
  maxScore?: number;
  assessment?: string;
  headline?: string;
  scoreBand?: string;
  strengths?: string[];
  risks?: string[];
  nextEvidence?: string[];
  createdAt: number;
};
type SynastryReportApiRecord = {
  id: string;
  partner_name?: string;
  report?: SynastryReportCard;
  created_at?: string;
};
type ChatSession = { id: string; title: string; theme: Theme; modelId: string; messages: Message[]; updatedAt: number };
type RequestError = { sessionId: string; message: string };
type StreamingReply = { sessionId: string; text: string };
type BirthPlace = { label: string; lat: number; lon: number; tz: number };
type Account = { user: { id: string; email: string | null }; credits: number; isAdmin: boolean };
type OnboardingSuggestion = { theme: Exclude<Theme, "general">; text: string };
type OnboardingContent = { greeting: string; suggestions: OnboardingSuggestion[] };
type OnboardingStep = "name" | "birth" | "place";
type GreetingPeriod = "morning" | "noon" | "afternoon" | "evening" | "late-night";
type SessionReadResult = { readonly sessions: ChatSession[]; readonly fallbackSessionIds: string[] };
type PendingConsultation = {
  readonly requestId: string;
  readonly sessionId: string;
  readonly question: string;
  readonly theme: Theme;
  readonly previousSession: ChatSession;
  readonly optimisticSession: ChatSession;
  readonly previousOnboardingState: boolean;
  readonly controller: AbortController;
  readonly cancelled: boolean;
  readonly phase: "undo" | "streaming";
  readonly partialReply: string;
};
const undoWindowMs = 2_500;
const china = chinaLocations.country;

const themes: Array<{ id: Exclude<Theme, "general">; label: string; prompt: string }> = [
  { id: "career", label: "事业", prompt: "未来一年，事业和收入该关注什么？" },
  { id: "marriage", label: "关系", prompt: "我的关系模式是什么？" },
  { id: "timing", label: "时运", prompt: "未来哪些阶段值得把握？" },
];

const previewModelCatalog = parsePublicModelCatalog({
  defaultModelId: "deepseek-pro",
  models: [
    { id: "deepseek-pro", label: "DeepSeek V4 Pro", description: "更适合复杂分析", creditCost: 1, isDefault: true },
    { id: "gpt-5-mini", label: "ChatGPT 5 Mini", description: "响应稳定、速度均衡", creditCost: 1, isDefault: false },
  ],
});

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

function createSession(modelId: string): ChatSession {
  return {
    id: globalThis.crypto.randomUUID(),
    title: "新对话",
    theme: "general",
    modelId,
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

function chartLibraryStorageKey(accountId: string) {
  return `jyotisha_chart_library:${accountId}`;
}
function synastryHistoryStorageKey(accountId: string) {
  return `jyotisha_synastry_history:${accountId}`;
}

function profileReadyForLibrary(profile: Profile) {
  return !missingProfileStep(profile);
}

function buildSelfChartRecord(profile: Profile): ChartLibraryRecord {
  return { id: "self", role: "self", profile, updatedAt: timestamp() };
}

function upsertSelfChart(library: ChartLibraryRecord[], profile: Profile) {
  if (!profileReadyForLibrary(profile)) return library.filter((record) => record.role !== "self");
  const others = library.filter((record) => record.role !== "self");
  return [buildSelfChartRecord(profile), ...others];
}

function readChartLibrary(accountId: string): ChartLibraryRecord[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(chartLibraryStorageKey(accountId)) || "[]") as ChartLibraryRecord[];
    return Array.isArray(parsed) ? parsed.filter((record) => record?.id && record?.profile) : [];
  } catch {
    return [];
  }
}
function readSynastryHistory(accountId: string): SynastryReportCard[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(synastryHistoryStorageKey(accountId)) || "[]") as SynastryReportCard[];
    return Array.isArray(parsed) ? parsed.filter((record) => record?.id && record?.partnerName).slice(0, 10) : [];
  } catch {
    return [];
  }
}

function writeSynastryHistory(accountId: string, history: SynastryReportCard[]) {
  localStorage.setItem(synastryHistoryStorageKey(accountId), JSON.stringify(history.slice(0, 10)));
}

function normalizeSynastryReportApiRecord(record: SynastryReportApiRecord): SynastryReportCard | null {
  if (!record.report || typeof record.report !== "object") return null;
  return {
    ...record.report,
    id: record.id,
    partnerName: record.partner_name || record.report.partnerName || "对方",
    createdAt: Date.parse(record.created_at || "") || record.report.createdAt || timestamp(),
  };
}

async function fetchCloudSynastryHistory() {
  const response = await fetch("/api/synastry-reports", { cache: "no-store" });
  if (!response.ok) throw new Error("cloud_synastry_history_unavailable");
  const payload = await response.json().catch(() => null) as { reports?: SynastryReportApiRecord[] } | null;
  return (payload?.reports || []).map(normalizeSynastryReportApiRecord).filter(Boolean) as SynastryReportCard[];
}

async function saveCloudSynastryReport(report: SynastryReportCard) {
  const response = await fetch("/api/synastry-reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ partnerName: report.partnerName, report }),
  });
  if (!response.ok) throw new Error("cloud_synastry_report_save_failed");
  const payload = await response.json().catch(() => null) as { report?: SynastryReportApiRecord } | null;
  return payload?.report ? normalizeSynastryReportApiRecord(payload.report) || report : report;
}

function normalizeChartLibraryApiRecord(record: ChartLibraryApiRecord): ChartLibraryRecord {
  return {
    id: record.role === "self" ? "self" : record.id,
    role: record.role,
    profile: record.profile,
    updatedAt: Date.parse(record.updated_at || "") || timestamp(),
  };
}

async function fetchCloudChartLibrary() {
  const response = await fetch("/api/chart-profiles", { cache: "no-store" });
  if (!response.ok) throw new Error("cloud_chart_library_unavailable");
  const payload = await response.json().catch(() => null) as { profiles?: ChartLibraryApiRecord[] } | null;
  return (payload?.profiles || []).map(normalizeChartLibraryApiRecord);
}

async function saveCloudChartProfile(record: ChartLibraryRecord) {
  const response = await fetch("/api/chart-profiles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: record.role === "self" ? undefined : record.id,
      role: record.role,
      profile: record.profile,
    }),
  });
  if (!response.ok) throw new Error("cloud_chart_profile_save_failed");
  const payload = await response.json().catch(() => null) as { profile?: ChartLibraryApiRecord } | null;
  return payload?.profile ? normalizeChartLibraryApiRecord(payload.profile) : record;
}

async function deleteCloudChartProfile(recordId: string) {
  const response = await fetch(`/api/chart-profiles/${encodeURIComponent(recordId)}`, { method: "DELETE" });
  if (!response.ok) throw new Error("cloud_chart_profile_delete_failed");
}

function profilePlaceLabel(profile: Profile) {
  return selectedBirthPlace(profile)?.label || "地点未完整";
}

function buildSynastryQuestion(selfProfile: Profile, partnerProfile: Profile) {
  return [
    `请用印度占星合盘分析我和${partnerProfile.name || "对方"}的关系。`,
    `我的资料：${selfProfile.name || "本人"}，${selfProfile.date} ${selfProfile.time}，${profilePlaceLabel(selfProfile)}。`,
    `对方资料：${partnerProfile.name || "对方"}，${partnerProfile.date} ${partnerProfile.time}，${profilePlaceLabel(partnerProfile)}。`,
    "请先说明会使用哪些证据层，再分析关系模式、冲突点、适合发展的方式和需要谨慎的时间窗口。",
  ].join("\n");
}

function buildDailyStarlanguageQuestion(profile: Profile) {
  const today = new Date().toISOString().slice(0, 10);
  return [
    `请生成今日星语：${today}，对象是${profile.name || "我"}。`,
    `出生资料：${profile.date} ${profile.time}，${profilePlaceLabel(profile)}。`,
    "请输出今日趋势、适合推进的事、需要避开的事、一个行动建议。",
    "边界：这是探索性日提示，不是确定预测；若涉及精确事件日期，请标为候选触发，不要包装成必然结论。",
  ].join("\n");
}

function buildBirthTimeRectificationQuestion(profile: Profile) {
  return [
    `请为${profile.name || "我"}做生时校正辅助。`,
    `当前记录：${profile.date} ${profile.time || "时间不确定"}，${profilePlaceLabel(profile)}。`,
    "请先列出需要我补充的关键人生事件，再给候选出生时间段、每段会影响的 Lagna/分盘/大运差异。",
    "边界：候选出生时间段必须标为待验证，不能直接改写默认星盘；没有事件证据前不要声称校正完成。",
  ].join("\n");
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

function readSessions(value: unknown, catalog: PublicLanguageModelCatalog | null): SessionReadResult {
  if (!Array.isArray(value)) return { sessions: [], fallbackSessionIds: [] };
  const fallbackSessionIds: string[] = [];
  const sessions = value.flatMap((item): ChatSession[] => {
    if (!item || typeof item !== "object") return [];
    const session = item as Partial<ChatSession> & { model_id?: unknown; updated_at?: unknown };
    const messages: Message[] = Array.isArray(session.messages)
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

    if (typeof session.id !== "string") return [];
    const savedModelId = session.model_id ?? session.modelId;
    const selection = catalog
      ? resolveSessionModelId(savedModelId, catalog)
      : { modelId: typeof savedModelId === "string" ? savedModelId : "", fellBack: false };
    if (catalog && selection.fellBack) fallbackSessionIds.push(session.id);
    return [{
        id: session.id,
        title: typeof session.title === "string" ? session.title.slice(0, 36) : "新对话",
        theme: session.theme === "career" || session.theme === "marriage" || session.theme === "timing" ? session.theme : "general",
        modelId: selection.modelId,
        messages,
        updatedAt: typeof session.updatedAt === "number"
          ? session.updatedAt
          : typeof session.updated_at === "string"
            ? Date.parse(session.updated_at)
            : timestamp(),
      }];
  });
  return { sessions, fallbackSessionIds };
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

function ProfileFields({ value, onChange, nameInputId }: { value: Profile; onChange: (profile: Profile) => void; nameInputId?: string }) {
  return (
    <>
      <label>
        <span>如何称呼你</span>
        <input id={nameInputId} required autoComplete="name" maxLength={80} placeholder="例如：林遥" value={value.name} onChange={(event) => onChange({ ...value, name: event.target.value })} />
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

class CancellationResponseError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "CancellationResponseError";
    this.status = status;
  }
}

function waitForUndoWindow(signal: AbortSignal) {
  return new Promise<void>((resolve) => {
    const finish = () => {
      window.clearTimeout(timer);
      signal.removeEventListener("abort", finish);
      resolve();
    };
    const timer = window.setTimeout(finish, undoWindowMs);
    signal.addEventListener("abort", finish, { once: true });
  });
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

async function fetchModelCatalog(signal?: AbortSignal) {
  const response = await fetch("/api/models", { signal, cache: "no-store" });
  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new Error(payloadMessage(payload, "暂时无法读取可用模型"));
  return parsePublicModelCatalog(payload);
}

export default function Home() {
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [profileDraft, setProfileDraft] = useState<Profile>(emptyProfile);
  const [chartLibrary, setChartLibrary] = useState<ChartLibraryRecord[]>([]);
  const [chartLibraryOpen, setChartLibraryOpen] = useState(false);
  const [otherProfileDraft, setOtherProfileDraft] = useState<Profile>(emptyProfile);
  const [synastryReportCard, setSynastryReportCard] = useState<SynastryReportCard | null>(null);
  const [synastryHistory, setSynastryHistory] = useState<SynastryReportCard[]>([]);
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
  const [modelCatalog, setModelCatalog] = useState<PublicLanguageModelCatalog | null>(null);
  const [activeSessionId, setActiveSessionId] = useState("");
  const [draft, setDraft] = useState("");
  const [draftTheme, setDraftTheme] = useState<Theme | null>(null);
  const [composerNotice, setComposerNotice] = useState("");
  const [consultationPhase, setConsultationPhase] = useState<"undo" | "streaming" | null>(null);
  const [cancellationPending, setCancellationPending] = useState(false);
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
  const pendingConsultation = useRef<PendingConsultation | null>(null);
  const cancellationRequests = useRef(new Map<string, Promise<void>>());
  const cancellationFeedbackRequest = useRef<string | null>(null);
  const cancellationInFlight = useRef(false);
  const stoppedRequestAwaitingSettlement = useRef<string | null>(null);
  const stoppedSessionPersistence = useRef(new Map<string, Promise<void>>());
  const modelPersistence = useRef(new SessionModelPersistenceQueue());
  const modelSyncFailures = useRef(new Set<string>());
  const modelSelectionVersions = useRef(new Map<string, number>());
  const activeSessionIdRef = useRef("");
  const chartLibraryLoadedAccount = useRef("");
  const uiPreview = useRef(false);
  const uiPreviewMode = useRef<string | null>(null);

  const activeSession = sessions.find((session) => session.id === activeSessionId) ?? sessions[0];
  const activeError = requestError && requestError.sessionId === activeSession?.id ? requestError.message : "";
  const isLoading = pendingSessionId === activeSession?.id;
  const activeStreamingText = streamingReply && streamingReply.sessionId === activeSession?.id ? streamingReply.text : "";

  useEffect(() => {
    activeSessionIdRef.current = activeSessionId;
  }, [activeSessionId]);
  const activeSuggestions = activeSession?.messages.reduce((latest, message) => message.role === "assistant" && message.suggestions?.length ? message.suggestions : latest, [] as string[]) ?? [];
  const accountId = account?.user.id;

  useEffect(() => {
    if (!accountId) {
      setChartLibrary([]);
      setSynastryHistory([]);
      chartLibraryLoadedAccount.current = "";
      return;
    }
    if (chartLibraryLoadedAccount.current === accountId) return;
    chartLibraryLoadedAccount.current = accountId;
    setChartLibrary(upsertSelfChart(readChartLibrary(accountId), profile));
    setSynastryHistory(readSynastryHistory(accountId));
    void fetchCloudChartLibrary()
      .then((cloudLibrary) => {
        setChartLibrary((current) => {
          const otherById = new Map([
            ...current.filter((record) => record.role === "other").map((record) => [record.id, record] as const),
            ...cloudLibrary.filter((record) => record.role === "other").map((record) => [record.id, record] as const),
          ]);
          const next = upsertSelfChart([...otherById.values()], profile);
          localStorage.setItem(chartLibraryStorageKey(accountId), JSON.stringify(next));
          return next;
        });
      })
      .catch(() => {
        // Cloud chart library is best-effort; local library remains usable.
      });
    void fetchCloudSynastryHistory()
      .then((cloudHistory) => {
        setSynastryHistory((current) => {
          const byId = new Map([...current, ...cloudHistory].map((record) => [record.id, record] as const));
          const next = [...byId.values()].sort((a, b) => b.createdAt - a.createdAt).slice(0, 10);
          writeSynastryHistory(accountId, next);
          return next;
        });
      })
      .catch(() => {
        // Cloud synastry history is best-effort; local history remains usable.
      });
  }, [accountId, profile]);

  useEffect(() => {
    if (!accountId) return;
    setChartLibrary((current) => {
      const next = upsertSelfChart(current, profile);
      localStorage.setItem(chartLibraryStorageKey(accountId), JSON.stringify(next));
      return next;
    });
  }, [accountId, profile]);

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
          uiPreviewMode.current = previewMode;
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
          const previewMessages: Message[] = previewMode === "conversation" || previewMode === "streaming" || previewMode === "partial"
            ? [
              { role: "user", text: "未来半年是否适合换工作？" },
              { role: "assistant", text: "可以先看职业方向、关键时间。\n同时评估现实风险。\n此处只展示本地预览，\n不调用真实星盘。", suggestions: ["先看事业方向", "再看关键时间", "评估现实风险"] },
            ]
            : [];
          const previewSession: ChatSession = {
            id: "preview-session",
            title: previewMessages.length > 0 ? "未来半年是否适合换工作" : "新对话",
            theme: "career",
            modelId: previewModelCatalog.defaultModelId,
            messages: previewMessages,
            updatedAt: timestamp(),
          };
          setAccount({ user: { id: "preview-user", email: "preview@local.test" }, credits: 8, isAdmin: false });
          setModelCatalog(previewModelCatalog);
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

        const [nextAccount, modelCatalogResult] = await Promise.all([
          fetchAccount(controller.signal),
          fetchModelCatalog(controller.signal)
            .then((catalog) => ({ catalog, unavailable: false }))
            .catch((caught: unknown) => {
              if (caught instanceof Error && caught.name === "AbortError") throw caught;
              return { catalog: null, unavailable: true };
            }),
        ]);
        const nextModelCatalog = modelCatalogResult.catalog;
        const [profileResult, sessionsResult] = await Promise.all([
          supabase
            .from("profiles")
            .select("name,birth_date,birth_time,country_code,province_code,city_code,district_code")
            .eq("id", nextAccount.user.id)
            .abortSignal(controller.signal)
            .maybeSingle(),
          supabase
            .from("chat_sessions")
            .select("id,title,theme,model_id,messages,updated_at")
            .abortSignal(controller.signal)
            .order("updated_at", { ascending: false }),
        ]);

        if (profileResult.error) throw profileResult.error;
        if (sessionsResult.error) throw sessionsResult.error;

        const parsedSessions = readSessions(sessionsResult.data, nextModelCatalog);
        let nextSessions = parsedSessions.sessions;
        if (nextSessions.length === 0) {
          if (controller.signal.aborted) return;
          const initialSession = createSession(nextModelCatalog?.defaultModelId ?? "");
          const { error } = await supabase
            .from("chat_sessions")
            .insert({
              id: initialSession.id,
              user_id: nextAccount.user.id,
              title: initialSession.title,
              theme: initialSession.theme,
              model_id: initialSession.modelId || null,
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
        setModelCatalog(nextModelCatalog);
        setProfile(nextProfile);
        setProfileDraft(nextProfile);
        setStartGreeting(nextProfile.name.trim() ? createStartGreeting(nextProfile.name) : "");
        setOnboardingStep(missingProfileStep(nextProfile) ?? "name");
        setSessions(nextSessions);
        setActiveSessionId(nextSessions[0].id);
        if (modelCatalogResult.unavailable) {
          setComposerNotice("模型服务暂时不可用，当前无法发送问题。");
        } else if (parsedSessions.fallbackSessionIds.length > 0) {
          setComposerNotice("此前选择的模型已下线，已切换为默认模型。");
        }
        setAccountError("");

        if (nextModelCatalog && parsedSessions.fallbackSessionIds.length > 0) {
          const { error } = await supabase
            .from("chat_sessions")
            .update({ model_id: nextModelCatalog.defaultModelId })
            .eq("user_id", nextAccount.user.id)
            .in("id", parsedSessions.fallbackSessionIds)
            .abortSignal(controller.signal);
          if (error && !controller.signal.aborted) {
            setComposerNotice("已在当前页面切换为默认模型，但云端同步失败；刷新后可能需要重新选择。");
          }
        }
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
      model_id: session.modelId,
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
    if (!account || !modelCatalog || creatingSession) return;
    setMobileSidebarOpen(false);
    const nextSession = createSession(modelCatalog.defaultModelId);
    const previousSessionId = activeSession?.id ?? "";
    setCreatingSession(true);
    setSessions((current) => [nextSession, ...current]);
    setActiveSessionId(nextSession.id);
    setDraft("");
    setDraftTheme(null);
    setComposerNotice("");
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

  async function selectSessionModel(modelId: string) {
    const userId = account?.user.id;
    if (!activeSession || !modelCatalog || !userId || pendingSessionId || cancellationPending || creatingSession) return;
    const selectedModel = modelCatalog.models.find((model) => model.id === modelId);
    const retryingFailedSync = activeSession.modelId === modelId && modelSyncFailures.current.has(activeSession.id);
    if (!selectedModel || (activeSession.modelId === modelId && !retryingFailedSync)) return;

    const nextSession: ChatSession = retryingFailedSync
      ? activeSession
      : { ...activeSession, modelId, updatedAt: timestamp() };
    const selectionVersion = (modelSelectionVersions.current.get(nextSession.id) ?? 0) + 1;
    modelSelectionVersions.current.set(nextSession.id, selectionVersion);
    if (!retryingFailedSync) updateSession(activeSession.id, () => nextSession);
    setRequestError(null);
    setComposerNotice("");

    try {
      await modelPersistence.current.enqueue(nextSession.id, () => persistSessionModelSelection(
        async ({ values, sessionId, userId: ownerId }) => {
          if (process.env.NODE_ENV === "development" && uiPreview.current) {
            return { found: true, error: null };
          }
          const { data, error } = await createBrowserSupabaseClient()
            .from("chat_sessions")
            .update(values)
            .eq("id", sessionId)
            .eq("user_id", ownerId)
            .select("id")
            .maybeSingle();
          return { found: Boolean(data), error: error?.message ?? null };
        },
        userId,
        nextSession.id,
        modelId,
      ));
      if (modelSelectionVersions.current.get(nextSession.id) !== selectionVersion) return;
      modelSelectionVersions.current.delete(nextSession.id);
      modelSyncFailures.current.delete(nextSession.id);
    } catch (caught) {
      if (modelSelectionVersions.current.get(nextSession.id) !== selectionVersion) return;
      modelSelectionVersions.current.delete(nextSession.id);
      modelSyncFailures.current.add(nextSession.id);
      if (activeSessionIdRef.current === nextSession.id) {
        setComposerNotice(`已在当前页面选择 ${selectedModel.label}，但云端同步失败；再次选择当前模型即可重试。`);
      }
      setRequestError({
        sessionId: nextSession.id,
        message: caught instanceof Error ? caught.message : "模型选择暂时无法同步到云端。",
      });
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
    await saveCloudChartProfile({ ...buildSelfChartRecord(nextProfile), updatedAt: timestamp() }).catch(() => null);
  }

  async function saveOtherChart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextProfile = { ...otherProfileDraft, name: otherProfileDraft.name.trim() };
    if (missingProfileStep(nextProfile)) {
      setAccountError("请补全其他星盘的称呼、出生时间和出生地点。");
      return;
    }
    if (!accountId) return;
    let record: ChartLibraryRecord = {
      id: globalThis.crypto.randomUUID(),
      role: "other",
      profile: nextProfile,
      updatedAt: timestamp(),
    };
    try {
      record = await saveCloudChartProfile(record);
    } catch {
      // Keep local chart library usable when cloud sync is unavailable.
    }
    setChartLibrary((current) => {
      const next = [...upsertSelfChart(current, profile), record];
      localStorage.setItem(chartLibraryStorageKey(accountId), JSON.stringify(next));
      return next;
    });
    setOtherProfileDraft(emptyProfile);
    setAccountError("");
    setProfileNotice("已添加到星盘库。");
  }

  function deleteOtherChart(recordId: string) {
    if (!accountId) return;
    void deleteCloudChartProfile(recordId).catch(() => {
      // Local deletion should not be blocked by temporary cloud sync failures.
    });
    setChartLibrary((current) => {
      const next = current.filter((record) => record.id !== recordId || record.role === "self");
      localStorage.setItem(chartLibraryStorageKey(accountId), JSON.stringify(next));
      return next;
    });
  }

  async function makeDefaultChart(record: ChartLibraryRecord) {
    if (record.role !== "other" || profileSaving) return;
    setProfileSaving(true);
    setAccountError("");
    try {
      await persistProfile(record.profile);
      setProfile(record.profile);
      setProfileDraft(record.profile);
      setProfileNotice("已设为当前默认星盘。");
    } catch (caught) {
      setAccountError(friendlyError(caught instanceof Error ? caught.message : "默认星盘保存失败"));
    } finally {
      setProfileSaving(false);
    }
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

  function chooseSuggestedQuestion(question: string, theme?: Theme) {
    if (pendingSessionId || cancellationInFlight.current) return;
    setDraft(question);
    setDraftTheme(theme ?? null);
    setComposerNotice("");
    window.requestAnimationFrame(() => composerInput.current?.focus());
  }

  function draftDailyStarlanguageQuestion() {
    chooseSuggestedQuestion(buildDailyStarlanguageQuestion(profile), "timing");
  }

  function draftBirthTimeRectificationQuestion() {
    chooseSuggestedQuestion(buildBirthTimeRectificationQuestion(profile), "timing");
  }

  async function draftSynastryQuestionFromChart(record: ChartLibraryRecord) {
    if (record.role !== "other") return;
    const baseQuestion = buildSynastryQuestion(profile, record.profile);
    try {
      const response = await fetch("/api/synastry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ selfProfile: profile, partnerProfile: record.profile }),
      });
      const payload = await response.json().catch(() => null) as { status?: string; evidenceLayers?: string[]; synastry?: { total_score?: number; max_score?: number; assessment?: string }; relationshipReport?: { headline?: string; scoreBand?: string; strengths?: string[]; risks?: string[]; nextEvidence?: string[] } } | null;
      if (response.ok && payload?.status === "ok") {
        const score = payload.synastry?.total_score;
        const max = payload.synastry?.max_score;
        const assessment = payload.synastry?.assessment;
        const layers = (payload.evidenceLayers || []).join(" / ") || "Ashtakoot / Moon / D9";
        const reportCard: SynastryReportCard = {
          id: `${record.id}-${Date.now()}`,
          partnerName: record.profile.name || "对方",
          score,
          maxScore: max,
          assessment,
          headline: payload.relationshipReport?.headline,
          scoreBand: payload.relationshipReport?.scoreBand,
          strengths: payload.relationshipReport?.strengths,
          risks: payload.relationshipReport?.risks,
          nextEvidence: payload.relationshipReport?.nextEvidence,
          createdAt: Date.now(),
        };
        let savedReportCard = reportCard;
        if (accountId) {
          try {
            savedReportCard = await saveCloudSynastryReport(reportCard);
          } catch {
            // Local history remains the fallback when cloud persistence is unavailable.
          }
        }
        setSynastryReportCard(savedReportCard);
        if (accountId) {
          setSynastryHistory((current) => {
            const next = [savedReportCard, ...current.filter((item) => item.id !== savedReportCard.id)].slice(0, 10);
            writeSynastryHistory(accountId, next);
            return next;
          });
        }
        chooseSuggestedQuestion([
          baseQuestion,
          "",
          `已计算基础合盘证据：${layers}；Ashtakoot ${score ?? "?"}/${max ?? "?"}，初步评级：${assessment || "待解释"}。请基于这个证据包继续分析。`,
          payload.relationshipReport?.headline ? `结构化摘要：${payload.relationshipReport.headline}` : "",
        ].join("\n"), "marriage");
      } else {
        chooseSuggestedQuestion(baseQuestion, "marriage");
        setComposerNotice(payload?.status === "blocked" ? "合盘计算暂时不可用，已先生成问题草稿。" : "已生成合盘问题草稿。");
      }
    } catch {
      chooseSuggestedQuestion(baseQuestion, "marriage");
      setComposerNotice("合盘计算暂时不可用，已先生成问题草稿。");
    }
    setProfileOpen(false);
  }

  async function requestCancellation(requestId: string) {
    const existing = cancellationRequests.current.get(requestId);
    if (existing) return existing;

    const cancellation = (async () => {
      const response = await fetch("/api/consult/cancel", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ requestId }),
        keepalive: true,
      });
      const payload: unknown = await response.json().catch(() => null);
      if (!response.ok) {
        throw new CancellationResponseError(
          response.status,
          payloadMessage(payload, "暂时无法确认点数已退回"),
        );
      }
      if (!payload || typeof payload !== "object") return;
      const credits = "credits" in payload ? payload.credits : null;
      if (typeof credits === "number") {
        setAccount((current) => current ? { ...current, credits } : current);
      }
    })();
    cancellationRequests.current.set(requestId, cancellation);
    return cancellation;
  }

  async function confirmCancellation(requestId: string, sessionId: string, confirmedNotice: string) {
    try {
      await requestCancellation(requestId);
      if (cancellationFeedbackRequest.current === requestId && activeSessionIdRef.current === sessionId) {
        setComposerNotice(confirmedNotice);
      }
    } catch (error) {
      if (cancellationFeedbackRequest.current === requestId && activeSessionIdRef.current === sessionId) {
        setComposerNotice(error instanceof CancellationResponseError && error.status === 409
          ? "回答已完成结算，本次已计费；问题仍保留在输入框。"
          : "问题已放回输入框；暂时无法确认点数状态，请稍后在账户中核对。");
        setRequestError((current) => current?.sessionId === sessionId ? current : {
          sessionId,
          message: error instanceof Error ? error.message : "暂时无法确认点数状态。",
        });
      }
      void refreshAccount();
    }
  }

  async function stopResponse() {
    const pending = pendingConsultation.current;
    if (!pending || pending.cancelled) return;

    const isPreview = process.env.NODE_ENV === "development" && uiPreview.current;
    if (pending.phase === "streaming" && !isPreview) {
      stoppedRequestAwaitingSettlement.current = pending.requestId;
      cancellationInFlight.current = true;
      setCancellationPending(true);
    }
    pendingConsultation.current = { ...pending, cancelled: true };
    pending.controller.abort();

    if (pending.partialReply) {
      const stoppedSession: ChatSession = {
        ...pending.optimisticSession,
        messages: [...pending.optimisticSession.messages, { role: "assistant", text: pending.partialReply }],
        updatedAt: timestamp(),
      };
      updateSession(pending.sessionId, () => stoppedSession);
      setStreamingReply(null);
      setPendingSessionId(null);
      setConsultationPhase(null);
      setRequestError(null);
      setComposerNotice("已停止回答。模型已开始生成，本次将计费，现有内容已保留。");
      if (!isPreview) {
        const persistence = persistSession(stoppedSession).catch((error) => {
          setRequestError({
            sessionId: pending.sessionId,
            message: error instanceof Error ? error.message : "已停止的回答暂时无法同步。",
          });
        });
        stoppedSessionPersistence.current.set(pending.requestId, persistence);
      }
      if (!isPreview) {
        void refreshAccount();
      } else if (pendingConsultation.current?.requestId === pending.requestId) {
        pendingConsultation.current = null;
      }
      return;
    }

    updateSession(pending.sessionId, () => pending.previousSession);
    setOnboardingJustCompleted(pending.previousOnboardingState);
    setDraft(pending.question);
    setDraftTheme(pending.theme);
    setStreamingReply(null);
    setPendingSessionId(null);
    setConsultationPhase(null);
    setRequestError(null);
    cancellationFeedbackRequest.current = pending.requestId;
    setComposerNotice("已停止，问题已放回输入框，正在确认点数…");
    window.requestAnimationFrame(() => composerInput.current?.focus());

    if (pending.phase === "undo" || isPreview) {
      if (pendingConsultation.current?.requestId === pending.requestId) {
        pendingConsultation.current = null;
      }
      setComposerNotice("已停止，问题已放回输入框，本次未扣点。");
      return;
    }

    await confirmCancellation(
      pending.requestId,
      pending.sessionId,
      "已停止，问题已放回输入框，本次未扣点。",
    );
  }

  async function send(text: string, requestedTheme?: Theme) {
    const originalQuestion = text;
    const question = text.trim();
    if (!question || !activeSession || !modelCatalog || pendingSessionId || cancellationInFlight.current || pendingConsultation.current || !account) return;

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
      title: currentSession.title,
      theme,
      messages: [...preservedMessages, { role: "user", text: question }],
      updatedAt: timestamp(),
    };
    const requestId = globalThis.crypto.randomUUID();
    const controller = new AbortController();
    const previousOnboardingState = onboardingJustCompleted;
    cancellationFeedbackRequest.current = null;
    setRequestError(null);
    setComposerNotice("");
    setPendingSessionId(sessionId);
    setConsultationPhase("undo");
    pendingConsultation.current = {
      requestId,
      sessionId,
      question: originalQuestion,
      theme,
      previousSession: currentSession,
      optimisticSession: userSession,
      previousOnboardingState,
      controller,
      cancelled: false,
      phase: "undo",
      partialReply: "",
    };
    setOnboardingJustCompleted(false);
    updateSession(sessionId, () => userSession);
    setDraft("");
    setDraftTheme(null);

    if (process.env.NODE_ENV === "development" && uiPreview.current) {
      setStreamingReply({ sessionId, text: "" });
      if (uiPreviewMode.current === "partial") {
        const partialReply = "已开始查看事业方向与关键时间，先给你一个阶段性的判断。";
        if (pendingConsultation.current?.requestId === requestId) {
          pendingConsultation.current = {
            ...pendingConsultation.current,
            phase: "streaming",
            partialReply,
          };
        }
        setConsultationPhase("streaming");
        setStreamingReply({ sessionId, text: partialReply });
      }
      await new Promise((resolve) => window.setTimeout(resolve, uiPreviewMode.current === "streaming" || uiPreviewMode.current === "partial" ? 15_000 : 800));
      if (controller.signal.aborted) {
        if (pendingConsultation.current?.requestId === requestId) pendingConsultation.current = null;
        return;
      }
      const previewReply = parseAgentReply([
        "这是本地交互预览。正式对话会结合你的星盘证据继续分析。",
        '<!--AYANAM_SUGGESTIONS:["继续梳理方向","查看时间窗口","评估现实行动"]-->',
        "<!--AYANAM_TITLE:事业方向与时间选择-->",
      ].join("\n"), theme);
      const previewSession: ChatSession = {
        ...userSession,
        title: currentSession.messages.length === 0 && previewReply.title ? previewReply.title : userSession.title,
        messages: [...userSession.messages, {
          role: "assistant",
          text: previewReply.text,
          suggestions: previewReply.suggestions,
        }],
        updatedAt: timestamp(),
      };
      updateSession(sessionId, () => previewSession);
      setStreamingReply(null);
      setPendingSessionId(null);
      setConsultationPhase(null);
      pendingConsultation.current = null;
      return;
    }

    await waitForUndoWindow(controller.signal);
    if (controller.signal.aborted) return;
    if (pendingConsultation.current?.requestId === requestId) {
      pendingConsultation.current = {
        ...pendingConsultation.current,
        phase: "streaming",
      };
      setConsultationPhase("streaming");
    }
    setStreamingReply({ sessionId, text: "" });
    let latestPartialReply = "";
    try {
      const response = await fetch("/api/consult", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          requestId,
          modelId: currentSession.modelId,
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
        signal: controller.signal,
      });
      if (!response.ok) {
        const contentType = response.headers.get("content-type") ?? "";
        const errorPayload = contentType.includes("application/json") ? await response.json() : { message: await response.text() };
        if (response.status === 401) window.location.assign("/login");
        if (response.status === 402) openAccount(true);
        throw new Error(payloadMessage(errorPayload, "服务暂时不可用"));
      }
      if (!response.body) throw new Error("浏览器未收到可读取的回答流");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let answer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        answer += decoder.decode(value, { stream: true });
        const partialReply = parseAgentReply(answer, theme).text;
        latestPartialReply = partialReply;
        setStreamingReply({ sessionId, text: partialReply });
        if (partialReply && pendingConsultation.current?.requestId === requestId) {
          pendingConsultation.current = {
            ...pendingConsultation.current,
            partialReply,
          };
        }
      }
      answer += decoder.decode();
      if (controller.signal.aborted) return;
      if (!answer.trim()) throw new Error("Agent 没有返回内容，请重试。");
      const reply = parseAgentReply(answer, theme);
      if (!reply.text) throw new Error("Agent 没有返回可显示的回答，请重试。");

      const completedSession: ChatSession = {
        ...userSession,
        title: currentSession.messages.length === 0 && reply.title ? reply.title : userSession.title,
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
      const cancelled = controller.signal.aborted;
      const ownsInterface = pendingConsultation.current?.requestId === requestId;
      const partialReply = latestPartialReply;
      if (ownsInterface && !partialReply) {
        updateSession(sessionId, () => currentSession);
        setOnboardingJustCompleted(previousOnboardingState);
        if (activeSessionIdRef.current === sessionId) {
          setDraft(originalQuestion);
          setDraftTheme(theme);
        }
        if (!cancelled) {
          setRequestError({
            sessionId,
            message: `${caught instanceof Error ? caught.message : "服务暂时不可用，请稍后重试。"} 问题已放回输入框。`,
          });
          cancellationFeedbackRequest.current = requestId;
          if (activeSessionIdRef.current === sessionId) {
            setComposerNotice("问题已放回输入框，正在确认点数…");
          }
        }
      }
      if (ownsInterface && !partialReply) {
        await confirmCancellation(
          requestId,
          sessionId,
          "问题已放回输入框，本次未扣点。",
        );
      } else if (!cancelled && ownsInterface) {
        const interruptedSession: ChatSession = {
          ...userSession,
          messages: [...userSession.messages, { role: "assistant", text: partialReply }],
          updatedAt: timestamp(),
        };
        updateSession(sessionId, () => interruptedSession);
        try {
          await persistSession(interruptedSession);
          setRequestError({
            sessionId,
            message: "回答中途断开，已保留生成内容；本次已开始生成并计费。",
          });
        } catch (persistError) {
          setRequestError({
            sessionId,
            message: `${persistError instanceof Error ? persistError.message : "云端同步失败"} 已计费的部分回答仍保留在当前页面，请复制保存。`,
          });
        }
        if (activeSessionIdRef.current === sessionId) {
          setComposerNotice("回答中途断开，已保留现有内容，本次已计费。");
        }
      }
    } finally {
      cancellationRequests.current.delete(requestId);
      if (pendingConsultation.current?.requestId === requestId) {
        pendingConsultation.current = null;
        setStreamingReply(null);
        setPendingSessionId(null);
        setConsultationPhase(null);
      }
      if (stoppedRequestAwaitingSettlement.current === requestId) {
        const persistence = stoppedSessionPersistence.current.get(requestId);
        if (persistence) {
          await persistence;
          stoppedSessionPersistence.current.delete(requestId);
        }
        stoppedRequestAwaitingSettlement.current = null;
        cancellationInFlight.current = false;
        setCancellationPending(false);
      }
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profileComplete) {
      if (onboardingStep === "name" && presetMessageFinished) void saveOnboardingName();
      return;
    }
    void send(draft, draftTheme ?? undefined);
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
        <button className="new-chat" type="button" onClick={() => void startNewChat()} disabled={!hydrated || !account || !modelCatalog || creatingSession || Boolean(pendingSessionId) || cancellationPending}><Plus aria-hidden="true" /> {creatingSession ? "正在创建" : "新对话"}</button>
        <nav className="session-nav" aria-label="聊天记录">
          <span className="sidebar-label">聊天记录</span>
          <div className="session-list">
            {sessions.map((session) => (
              <button
                className={session.id === activeSession?.id ? "is-active" : ""}
                key={session.id}
                type="button"
                onClick={() => {
                  setActiveSessionId(session.id);
                  setDraft("");
                  setComposerNotice("");
                  setMobileSidebarOpen(false);
                }}
                disabled={Boolean(pendingSessionId) || cancellationPending}
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
            <span><i className={`status ${isLoading ? "status-loading" : "status-idle"}`} />{isLoading ? (consultationPhase === "undo" ? "即将发送，可撤回" : activeStreamingText ? "正在回答" : "正在核对星盘信息") : "基于星盘证据回答"}</span>
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

              {profileComplete && presetMessageFinished && !draft.trim() && (onboardingPending ? (
                <div className="starter-loading" role="status">正在准备三个入门问题…</div>
              ) : (
                <div className="starter-list" aria-label="Jyotisha 推荐的初始问题">
                  {(onboarding?.suggestions ?? themes.map((item) => ({ theme: item.id, text: item.prompt }))).map((item) => {
                    const theme = themes.find((candidate) => candidate.id === item.theme);
                    return (
                      <button key={`${item.theme}-${item.text}`} type="button" disabled={!hydrated || Boolean(pendingSessionId) || cancellationPending || !account || !modelCatalog} onClick={() => chooseSuggestedQuestion(item.text, item.theme)}>
                        <span className="starter-content"><b>{theme?.label || "开始"}</b><span>{item.text}</span></span>
                        <ArrowUpRight className="starter-arrow" aria-hidden="true" />
                      </button>
                    );
                  })}
                  {onboardingError && <p className="starter-note">Agent 的个性化入门问题暂时不可用，已显示安全的默认问题。</p>}
                  <div className="product-entrypoints" aria-label="常用占星入口">
                    <button type="button" disabled={!hydrated || Boolean(pendingSessionId) || cancellationPending || !account || !modelCatalog} onClick={draftDailyStarlanguageQuestion}>
                      <span><b>今日星语</b><small>基于默认星盘生成今日趋势；探索性日提示，不是确定预测。</small></span>
                      <ArrowUpRight className="starter-arrow" aria-hidden="true" />
                    </button>
                    <button type="button" disabled={!hydrated || Boolean(pendingSessionId) || cancellationPending || !account || !modelCatalog} onClick={draftBirthTimeRectificationQuestion}>
                      <span><b>生时校正</b><small>收集事件证据并给候选出生时间段，不能直接改写默认星盘。</small></span>
                      <ArrowUpRight className="starter-arrow" aria-hidden="true" />
                    </button>
                  </div>
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
          {activeSuggestions.length > 0 && !draft.trim() && !isLoading && !cancellationPending && (
            <div className="composer-suggestions" aria-label="推荐继续提问">
              {activeSuggestions.map((question) => (
                <button key={question} type="button" disabled={!account || !modelCatalog || cancellationPending} onClick={() => chooseSuggestedQuestion(question)}>{question}</button>
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
              disabled={isLoading || cancellationPending || (!profileComplete && (onboardingStep !== "name" || !presetMessageFinished || profileSaving))}
              value={draft}
              onChange={(event) => {
                setDraft(event.target.value);
                setDraftTheme(null);
                setComposerNotice("");
              }}
              onKeyDown={handleComposerKeyDown}
            />
            {isLoading ? (
              <Button
                className="composer-stop"
                aria-label={consultationPhase === "undo" ? "撤回发送，本次不扣点" : activeStreamingText ? "停止回答，保留已生成内容" : "停止回答并申请退回本次点数"}
                title={consultationPhase === "undo" ? "撤回发送，本次不扣点" : activeStreamingText ? "停止回答，本次已开始计费" : "停止回答"}
                size="icon"
                type="button"
                onClick={() => void stopResponse()}
              >
                <Square aria-hidden="true" />
              </Button>
            ) : (
              <Button aria-label={!profileComplete ? "确认称呼" : "发送"} disabled={!draft.trim() || Boolean(pendingSessionId) || cancellationPending || !account || !modelCatalog || (!profileComplete && (onboardingStep !== "name" || !presetMessageFinished || profileSaving))} size="icon" type="submit">
                <ArrowUp aria-hidden="true" />
              </Button>
            )}
          </form>
          <div className="composer-footer">
            <ModelSelector
              models={modelCatalog?.models ?? []}
              selectedModelId={activeSession?.modelId ?? ""}
              disabled={!activeSession || isLoading || cancellationPending || creatingSession}
              onSelect={(modelId) => void selectSessionModel(modelId)}
            />
            <p className={composerNotice || consultationPhase === "undo" ? "composer-notice" : undefined} role={composerNotice || consultationPhase === "undo" ? "status" : undefined}>{composerNotice || (consultationPhase === "undo" ? "已加入发送队列，2.5 秒内可免费撤回。" : !profileComplete && onboardingStep === "name" ? "Enter 确认称呼" : "Enter 发送 · Shift + Enter 换行")}</p>
          </div>
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
            <div className="default-chart-card" aria-label="当前默认星盘">
              <div>
                <span>当前默认星盘</span>
                <strong>{profileDraft.name.trim() || "未命名"}</strong>
                <small>角色：本人</small>
              </div>
              <button className="button-secondary" type="button" onClick={() => setChartLibraryOpen((current) => !current)}>管理星盘库</button>
            </div>
            {chartLibraryOpen && (
              <div className="chart-library-panel" aria-label="星盘库">
                <div className="chart-library-group">
                  <b>本人</b>
                  {chartLibrary.filter((record) => record.role === "self").map((record) => (
                    <article className="chart-library-item" key={record.id}>
                      <div>
                        <strong>{record.profile.name || "未命名"}</strong>
                        <small>{record.profile.date} {record.profile.time} · {profilePlaceLabel(record.profile)}</small>
                      </div>
                      <span>当前默认</span>
                    </article>
                  ))}
                </div>
                <div className="chart-library-group">
                  <b>其他</b>
                  {chartLibrary.filter((record) => record.role === "other").length === 0 && <p className="empty-library-copy">还没有其他星盘。</p>}
                  {chartLibrary.filter((record) => record.role === "other").map((record) => (
                    <article className="chart-library-item" key={record.id}>
                      <div>
                        <strong>{record.profile.name || "未命名"}</strong>
                        <small>{record.profile.date} {record.profile.time} · {profilePlaceLabel(record.profile)}</small>
                      </div>
                      <div className="chart-library-actions">
                        <button className="button-secondary" type="button" onClick={() => void draftSynastryQuestionFromChart(record)}>用于合盘</button>
                        <button className="button-secondary" type="button" onClick={() => void makeDefaultChart(record)} disabled={profileSaving}>设为默认</button>
                        <button className="button-secondary danger-button" type="button" onClick={() => deleteOtherChart(record.id)}>删除</button>
                      </div>
                    </article>
                  ))}
                </div>
                {synastryReportCard && (
                  <article className="synastry-report-card" aria-label="合盘结果摘要">
                    <div>
                      <span>合盘结果摘要</span>
                      <strong>{synastryReportCard.partnerName}</strong>
                      <small>Ashtakoot {synastryReportCard.score ?? "?"}/{synastryReportCard.maxScore ?? "?"} · {synastryReportCard.assessment || synastryReportCard.scoreBand || "待解释"}</small>
                    </div>
                    {synastryReportCard.headline && <p>{synastryReportCard.headline}</p>}
                    <details>
                      <summary>查看证据</summary>
                      <ul>
                        {(synastryReportCard.strengths || []).map((item) => <li key={item}>{item}</li>)}
                        {(synastryReportCard.risks || []).map((item) => <li key={item}>{item}</li>)}
                      </ul>
                      <small>下一步证据：{(synastryReportCard.nextEvidence || []).join(" / ") || "双方 Dasha / UL-DK / D9 7宫"}</small>
                    </details>
                  </article>
                )}
                {synastryHistory.length > 0 && (
                  <div className="synastry-history-list" aria-label="合盘历史">
                    <b>合盘历史</b>
                    {synastryHistory.slice(0, 5).map((item) => (
                      <button key={item.id} type="button" className="synastry-history-item" onClick={() => setSynastryReportCard(item)}>
                        <span>{item.partnerName}</span>
                        <small>Ashtakoot {item.score ?? "?"}/{item.maxScore ?? "?"} · {item.assessment || item.scoreBand || "待解释"}</small>
                      </button>
                    ))}
                  </div>
                )}
                <form className="profile-form chart-library-form" onSubmit={saveOtherChart}>
                  <div className="section-heading"><b>添加其他星盘</b><small>用于合盘、亲友盘或客户盘。</small></div>
                  <ProfileFields value={otherProfileDraft} onChange={setOtherProfileDraft} nameInputId="other-profile-name" />
                  <button className="button-primary save-profile" type="submit" disabled={!account}>添加到星盘库</button>
                </form>
              </div>
            )}
            {profileNotice && <p className="form-success" role="status">{profileNotice}</p>}
            <form className="profile-form" onSubmit={saveProfile}>
              <ProfileFields value={profileDraft} onChange={setProfileDraft} nameInputId="profile-name" />
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
