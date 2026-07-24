import { z } from "zod";

function isIsoCalendarDate(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return false;
  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
  return date.getUTCFullYear() === Number(match[1])
    && date.getUTCMonth() === Number(match[2]) - 1
    && date.getUTCDate() === Number(match[3]);
}

export const birthLocationSearchQuerySchema = z.object({
  q: z.string().trim().min(2).max(160),
  birthDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  birthTime: z.string().regex(/^(?:[01]\d|2[0-3]):[0-5]\d$/).optional(),
  locale: z.string().trim().min(2).max(16).default("zh"),
  limit: z.coerce.number().int().min(1).max(8).default(5),
}).superRefine((value, context) => {
  if (value.birthTime && !value.birthDate) context.addIssue({
    code: z.ZodIssueCode.custom,
    path: ["birthDate"],
    message: "birthTime requires birthDate",
  });
  if (value.birthDate && !isIsoCalendarDate(value.birthDate)) {
    context.addIssue({ code: z.ZodIssueCode.custom, path: ["birthDate"], message: "invalid birthDate" });
  }
});

export const normalizedBirthLocationSchema = z.object({
  provider: z.enum(["geoapify", "china_locations", "mapbox", "geonames"]),
  providerPlaceId: z.string().min(1),
  placeType: z.string().min(1),
  label: z.string().min(1),
  countryCode: z.string().nullable(),
  countryName: z.string().nullable(),
  regionCode: z.string().nullable(),
  regionName: z.string().nullable(),
  localityName: z.string().nullable(),
  districtName: z.string().nullable(),
  latitude: z.number().finite().min(-90).max(90),
  longitude: z.number().finite().min(-180).max(180),
  timezoneId: z.string().min(1),
  timezoneOffset: z.number().finite().min(-12).max(14).nullable(),
  timezoneSource: z.literal("iana_historical"),
  localTimeStatus: z.enum(["resolved", "not_provided", "ambiguous", "nonexistent"]),
});

export type BirthLocationSearchQuery = z.infer<typeof birthLocationSearchQuerySchema>;
export type NormalizedBirthLocation = z.infer<typeof normalizedBirthLocationSchema>;

export type BirthLocationSearchResult =
  | { status: "ok"; locations: NormalizedBirthLocation[] }
  | { status: "unavailable"; reason: "geoapify_not_configured" | "timezone_service_unavailable" | "provider_unavailable" };
