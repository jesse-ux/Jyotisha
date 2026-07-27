import type { DatePrecision, EventDateRange } from "./contracts.ts";

const dayMs = 86_400_000;

function isoDate(year: number, month: number, day: number): string {
  const value = new Date(Date.UTC(year, month - 1, day));
  if (value.getUTCFullYear() !== year || value.getUTCMonth() !== month - 1 || value.getUTCDate() !== day) {
    throw new Error("invalid_calendar_date");
  }
  return value.toISOString().slice(0, 10);
}

function monthEnd(year: number, month: number): string {
  return new Date(Date.UTC(year, month, 0)).toISOString().slice(0, 10);
}

export function dateRangeFromDeclared(value: string, precision: Exclude<DatePrecision, "range">): EventDateRange {
  if (precision === "day") {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error("invalid_day");
    const [year, month, day] = value.split("-").map(Number);
    const date = isoDate(year!, month!, day!);
    return { start: date, end: date, precision, label: value };
  }
  if (precision === "month") {
    if (!/^\d{4}-\d{2}$/.test(value)) throw new Error("invalid_month");
    const [year, month] = value.split("-").map(Number);
    const start = isoDate(year!, month!, 1);
    return { start, end: monthEnd(year!, month!), precision, label: value };
  }
  if (precision === "quarter") {
    const matched = /^(\d{4})-Q([1-4])$/.exec(value);
    if (!matched) throw new Error("invalid_quarter");
    const year = Number(matched[1]);
    const firstMonth = (Number(matched[2]) - 1) * 3 + 1;
    return {
      start: isoDate(year, firstMonth, 1),
      end: monthEnd(year, firstMonth + 2),
      precision,
      label: value,
    };
  }
  if (!/^\d{4}$/.test(value)) throw new Error("invalid_year");
  const year = Number(value);
  return { start: isoDate(year, 1, 1), end: isoDate(year, 12, 31), precision, label: value };
}

export function explicitDateRange(start: string, end: string, label = `${start}–${end}`): EventDateRange {
  const normalizedStart = dateRangeFromDeclared(start, "day").start;
  const normalizedEnd = dateRangeFromDeclared(end, "day").end;
  if (normalizedStart > normalizedEnd) throw new Error("invalid_date_range");
  return { start: normalizedStart, end: normalizedEnd, precision: "range", label };
}

export function sampledDates(range: EventDateRange): readonly string[] {
  if (range.start === range.end) return [range.start];
  const start = Date.parse(`${range.start}T00:00:00Z`);
  const end = Date.parse(`${range.end}T00:00:00Z`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || start > end) throw new Error("invalid_date_range");

  const values = new Set<string>([range.start, range.end]);
  for (let cursor = start; cursor <= end; cursor += 31 * dayMs) {
    const current = new Date(cursor);
    values.add(new Date(Date.UTC(current.getUTCFullYear(), current.getUTCMonth(), 1)).toISOString().slice(0, 10));
  }
  return [...values].filter((value) => value >= range.start && value <= range.end).sort();
}
