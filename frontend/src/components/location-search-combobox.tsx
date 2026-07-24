"use client";

import { Check, LoaderCircle, MapPin, Search, X } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

export type ResolvedBirthLocation = {
  id: string;
  label: string;
  placeType: string;
  provider: string;
  providerPlaceId: string;
  countryCode: string;
  countryName: string;
  admin1: string;
  admin2: string;
  locality: string;
  latitude: number;
  longitude: number;
  timezoneId: string;
  timezoneOffset: number | null;
  timezoneSource: string;
};

type LocationSearchComboboxProps = {
  value: ResolvedBirthLocation | null;
  birthDate?: string;
  birthTime?: string;
  disabled?: boolean;
  onChange: (location: ResolvedBirthLocation | null) => void;
};

type SearchState = "idle" | "loading" | "ready" | "empty" | "error";

function cleanString(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

export function parseLocationSearchResults(payload: unknown): ResolvedBirthLocation[] {
  const rawResults = Array.isArray(payload)
    ? payload
    : payload && typeof payload === "object" && Array.isArray((payload as { results?: unknown }).results)
      ? (payload as { results: unknown[] }).results
      : payload && typeof payload === "object" && Array.isArray((payload as { locations?: unknown }).locations)
        ? (payload as { locations: unknown[] }).locations
      : [];

  return rawResults.flatMap((candidate): ResolvedBirthLocation[] => {
    if (!candidate || typeof candidate !== "object") return [];
    const item = candidate as Record<string, unknown>;
    const latitude = typeof item.latitude === "number" ? item.latitude : Number.NaN;
    const longitude = typeof item.longitude === "number" ? item.longitude : Number.NaN;
    const timezoneOffset = item.timezoneOffset === null
      ? null
      : typeof item.timezoneOffset === "number"
        ? item.timezoneOffset
        : Number.NaN;
    const provider = cleanString(item.provider);
    const providerPlaceId = cleanString(item.providerPlaceId);
    const id = cleanString(item.id) || (provider && providerPlaceId ? `${provider}:${providerPlaceId}` : "");
    const label = cleanString(item.label);
    const countryCode = cleanString(item.countryCode).toUpperCase();
    const timezoneId = cleanString(item.timezoneId);
    if (!id || !label || !countryCode || !timezoneId
      || !Number.isFinite(latitude) || latitude < -90 || latitude > 90
      || !Number.isFinite(longitude) || longitude < -180 || longitude > 180
      || (timezoneOffset !== null
        && (!Number.isFinite(timezoneOffset) || timezoneOffset < -12 || timezoneOffset > 14))) return [];

    return [{
      id,
      label,
      placeType: cleanString(item.placeType),
      provider,
      providerPlaceId,
      countryCode,
      countryName: cleanString(item.countryName),
      admin1: cleanString(item.admin1) || cleanString(item.regionName),
      admin2: cleanString(item.admin2) || cleanString(item.districtName),
      locality: cleanString(item.locality) || cleanString(item.localityName),
      latitude,
      longitude,
      timezoneId,
      timezoneOffset,
      timezoneSource: cleanString(item.timezoneSource),
    }];
  });
}

export function LocationSearchCombobox({
  value,
  birthDate = "",
  birthTime = "",
  disabled = false,
  onChange,
}: LocationSearchComboboxProps) {
  const inputId = useId();
  const listboxId = `${inputId}-listbox`;
  const statusId = `${inputId}-status`;
  const requestSequence = useRef(0);
  const [query, setQuery] = useState(value?.label ?? "");
  const [results, setResults] = useState<ResolvedBirthLocation[]>([]);
  const [state, setState] = useState<SearchState>("idle");
  const [expanded, setExpanded] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  useEffect(() => {
    const normalized = query.trim();
    if (disabled || value || normalized.length < 2) return;

    const sequence = requestSequence.current + 1;
    requestSequence.current = sequence;
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setState("loading");
      setExpanded(true);
      try {
        const search = new URLSearchParams({ q: normalized, locale: "zh-CN" });
        if (birthDate) search.set("birthDate", birthDate);
        if (birthDate && birthTime) search.set("birthTime", birthTime);
        const response = await fetch(`/api/locations/search?${search.toString()}`, {
          credentials: "same-origin",
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("location_search_failed");
        const nextResults = parseLocationSearchResults(await response.json());
        if (requestSequence.current !== sequence) return;
        setResults(nextResults);
        setState(nextResults.length > 0 ? "ready" : "empty");
        setActiveIndex(nextResults.length > 0 ? 0 : -1);
      } catch {
        if (controller.signal.aborted || requestSequence.current !== sequence) return;
        setResults([]);
        setState("error");
        setActiveIndex(-1);
      }
    }, 260);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [birthDate, birthTime, disabled, query, value]);

  function choose(location: ResolvedBirthLocation) {
    requestSequence.current += 1;
    setQuery(location.label);
    setExpanded(false);
    setResults([]);
    setState("idle");
    setActiveIndex(-1);
    onChange(location);
  }

  function clear() {
    requestSequence.current += 1;
    setQuery("");
    setExpanded(false);
    setResults([]);
    setState("idle");
    setActiveIndex(-1);
    onChange(null);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (value && (event.key === "Backspace" || event.key === "Delete")) {
      event.preventDefault();
      clear();
      return;
    }
    if (!expanded || results.length === 0) {
      if (event.key === "ArrowDown" && results.length > 0) setExpanded(true);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((current) => (current + 1) % results.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((current) => (current <= 0 ? results.length - 1 : current - 1));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      choose(results[activeIndex]);
    } else if (event.key === "Escape") {
      event.preventDefault();
      setExpanded(false);
      setActiveIndex(-1);
    }
  }

  const isExpanded = expanded && !disabled && !value && query.trim().length >= 2;
  const activeDescendant = isExpanded && activeIndex >= 0
    ? `${listboxId}-option-${activeIndex}`
    : undefined;
  const statusText = state === "loading"
    ? "正在搜索地点"
    : state === "empty"
      ? "没有找到匹配地点，请尝试城市、区县或英文地名"
      : state === "error"
        ? "地点搜索暂时不可用，请稍后重试"
        : state === "ready"
          ? `找到 ${results.length} 个地点`
          : value
            ? `已选择 ${value.label}`
            : "输入至少两个字开始搜索";

  return (
    <div className={`location-combobox${value ? " is-selected" : ""}`}>
      <label htmlFor={inputId}>搜索出生地点</label>
      <div className="location-combobox-input-wrap">
        {state === "loading" ? <LoaderCircle className="location-combobox-leading is-spinning" aria-hidden="true" /> : <Search className="location-combobox-leading" aria-hidden="true" />}
        <input
          id={inputId}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={isExpanded}
          aria-controls={listboxId}
          aria-activedescendant={activeDescendant}
          aria-describedby={statusId}
          autoComplete="off"
          disabled={disabled}
          placeholder="输入城市、区县或地标，例如：上海、Taipei"
          value={value?.label ?? query}
          onChange={(event) => {
            if (value) onChange(null);
            const nextQuery = event.target.value;
            setQuery(nextQuery);
            if (nextQuery.trim().length < 2) {
              requestSequence.current += 1;
              setExpanded(false);
              setResults([]);
              setState("idle");
              setActiveIndex(-1);
            }
          }}
          onFocus={() => {
            if (!value && (results.length > 0 || state === "loading" || state === "empty" || state === "error")) setExpanded(true);
          }}
          onKeyDown={handleKeyDown}
        />
        {(query || value) && (
          <button className="location-combobox-clear" type="button" onClick={clear} disabled={disabled} aria-label="清除出生地点">
            <X aria-hidden="true" />
          </button>
        )}
      </div>

      <p id={statusId} className={`location-combobox-status${state === "error" ? " is-error" : ""}`} role="status" aria-live="polite">
        {value ? <Check aria-hidden="true" /> : <MapPin aria-hidden="true" />}
        <span>{statusText}</span>
      </p>

      {isExpanded && (
        <ul id={listboxId} className="location-combobox-results" role="listbox" aria-label="地点搜索结果">
          {state === "loading" && <li className="location-combobox-feedback">正在查找与出生日期对应的地点和时区…</li>}
          {state === "empty" && <li className="location-combobox-feedback">没有匹配结果。可以尝试更完整的城市名或英文拼写。</li>}
          {state === "error" && <li className="location-combobox-feedback is-error">搜索暂时失败，请检查网络后修改关键词重试。</li>}
          {state === "ready" && results.map((location, index) => (
            <li
              id={`${listboxId}-option-${index}`}
              key={location.id}
              role="option"
              aria-selected={index === activeIndex}
              className={index === activeIndex ? "is-active" : undefined}
            >
              <button
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => choose(location)}
              >
                <MapPin aria-hidden="true" />
                <span><b>{location.label}</b><small>{[location.countryName, location.timezoneId].filter(Boolean).join(" · ")}</small></span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
