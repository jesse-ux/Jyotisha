import type { JourneyEventScoreInput } from "./birth-time-journey-service.ts";

export function eventScorePayload(input: JourneyEventScoreInput) {
  return {
    birth_date: input.birthDate,
    start_time: input.startTime,
    end_time: input.endTime,
    lat: input.lat,
    lon: input.lon,
    tz: input.tz,
    events: input.events.map((event) => ({
      id: event.id,
      domain: event.domain,
      date: event.date,
      precision: event.precision,
    })),
  } as const;
}
