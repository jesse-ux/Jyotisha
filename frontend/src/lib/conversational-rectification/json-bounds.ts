import { z } from "zod";

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

/** Matches PostgreSQL jsonb::text, which adds one space after each comma and colon. */
export function postgresJsonbTextBytes(value: unknown): number {
  try {
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
