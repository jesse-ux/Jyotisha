import { z } from "zod";

const POSTGRES_JSON_MAX_DECIMAL_PLACES = 6;
const POSTGRES_JSON_MIN_FRACTION = 0.000001;
const POSTGRES_JSON_MAX_FRACTION_MAGNITUDE = 1_000_000;

function canonicalJsonDecimalPlaces(value: number): number | null {
  const serialized = JSON.stringify(value);
  const match = /^-?\d+(?:\.(\d+))?(?:e([+-]?\d+))?$/i.exec(serialized);
  if (!match) return null;
  const fractionLength = match[1]?.length ?? 0;
  const exponent = Number(match[2] ?? 0);
  return Math.max(0, fractionLength - exponent);
}

function postgresStableJsonNumber(value: number): boolean {
  if (!Number.isFinite(value)) return false;
  if (Number.isSafeInteger(value)) return true;
  const magnitude = Math.abs(value);
  const decimalPlaces = canonicalJsonDecimalPlaces(value);
  return magnitude >= POSTGRES_JSON_MIN_FRACTION
    && magnitude <= POSTGRES_JSON_MAX_FRACTION_MAGNITUDE
    && decimalPlaces !== null
    && decimalPlaces <= POSTGRES_JSON_MAX_DECIMAL_PLACES;
}

function postgresJsonNumbersAreStable(
  value: unknown,
  ancestors: Set<object> = new Set<object>(),
): boolean {
  if (typeof value === "number") return postgresStableJsonNumber(value);
  if (value === null || typeof value !== "object") return true;
  if (ancestors.has(value)) return false;
  ancestors.add(value);
  const values = Array.isArray(value) ? value : Object.values(value);
  const stable = values.every((item) => postgresJsonNumbersAreStable(item, ancestors));
  ancestors.delete(value);
  return stable;
}

function postgresSeparatorBytes(value: unknown): number {
  if (Array.isArray(value)) {
    return Math.max(0, value.length - 1)
      + value.reduce((total, item) => total + postgresSeparatorBytes(item), 0);
  }
  if (value !== null && typeof value === "object") {
    const values = Object.values(value);
    return (values.length === 0 ? 0 : (2 * values.length) - 1)
      + values.reduce((total, item) => total + postgresSeparatorBytes(item), 0);
  }
  return 0;
}

/**
 * Matches PostgreSQL jsonb::text for the durable numeric contract: safe
 * integers or nonzero decimals with at most six places and magnitude <= 1e6.
 * PostgreSQL expands exponent-form numerics, so values outside that contract
 * return Infinity instead of undercounting their durable representation.
 */
export function postgresJsonbTextBytes(value: unknown): number {
  try {
    if (!postgresJsonNumbersAreStable(value)) return Number.POSITIVE_INFINITY;
    const compact = JSON.stringify(value);
    if (compact === undefined) return Number.POSITIVE_INFINITY;
    const serializedValue: unknown = JSON.parse(compact);
    return new TextEncoder().encode(compact).byteLength
      + postgresSeparatorBytes(serializedValue);
  } catch {
    return Number.POSITIVE_INFINITY;
  }
}

export function boundedJson<T>(schema: z.ZodType<T>, maximumBytes: number): z.ZodType<T> {
  return schema.superRefine((value, context) => {
    if (postgresJsonbTextBytes(value) > maximumBytes) {
      context.addIssue({
        code: "custom",
        message: `PostgreSQL JSON exceeds ${maximumBytes} UTF-8 bytes`,
      });
    }
  });
}
