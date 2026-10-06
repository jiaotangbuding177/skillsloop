/** Asia/Shanghai calendar helpers for period-end midnight evaluation. */

const SHANGHAI_OFFSET_MS = 8 * 60 * 60 * 1000;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

export function toShanghaiDateKey(date: Date = new Date()): string {
  const shanghai = new Date(date.getTime() + SHANGHAI_OFFSET_MS);
  const y = shanghai.getUTCFullYear();
  const m = String(shanghai.getUTCMonth() + 1).padStart(2, "0");
  const d = String(shanghai.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function shanghaiDayStartUtc(dateKey: string): Date {
  const [y, m, d] = dateKey.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d, 0, 0, 0) - SHANGHAI_OFFSET_MS);
}

export function addShanghaiDateKey(dateKey: string, delta: number): string {
  const start = shanghaiDayStartUtc(dateKey);
  return toShanghaiDateKey(new Date(start.getTime() + delta * ONE_DAY_MS));
}

/**
 * Period length = intervalDays. Anchor calendar day is day 1;
 * trigger at Shanghai 00:00 of day N.
 * Example: from 2026-09-12, N=7 → 2026-09-18 00:00 Shanghai.
 * If that midnight is already past (e.g. N=1 enabled in the afternoon),
 * advance by full periods until the next future Shanghai midnight.
 */
export function nextPeriodEndMidnightUtc(from: Date, intervalDays: number): Date {
  const days = Math.max(1, Math.floor(intervalDays));
  const startKey = toShanghaiDateKey(from);
  let endKey = addShanghaiDateKey(startKey, days - 1);
  let target = shanghaiDayStartUtc(endKey);
  while (target.getTime() <= from.getTime()) {
    endKey = addShanghaiDateKey(endKey, days);
    target = shanghaiDayStartUtc(endKey);
  }
  return target;
}

/** Ms until the next Asia/Shanghai clock time (hour:minute). */
export function msUntilNextShanghaiTime(hour: number, minute: number, now = Date.now()): number {
  const today = toShanghaiDateKey(new Date(now));
  const [y, m, d] = today.split("-").map(Number);
  const targetUtc = Date.UTC(y, m - 1, d, hour, minute, 0) - SHANGHAI_OFFSET_MS;
  if (targetUtc > now) return targetUtc - now;
  return targetUtc + ONE_DAY_MS - now;
}
