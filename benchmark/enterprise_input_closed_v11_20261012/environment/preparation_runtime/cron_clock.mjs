// Explicit benchmark replay clock, only for pinned OpenClaw Node processes.
// Schedulers remain globally disabled; no actual trigger is part of evaluation.
import { performance } from 'node:perf_hooks';
import fs from 'node:fs';
import crypto from 'node:crypto';
const target = process.env.SKILLLOOP_CRON_CLOCK_EPOCH;
const clockFile = process.env.SKILLLOOP_CRON_CLOCK_FILE;
if ((target || clockFile) && (process.argv[1] || '').includes('/opt/openclaw/')) {
  const RealDate = globalThis.Date;
  const guardModule = '/opt/openclaw/lib/node_modules/openclaw/dist/cron-YMfXhcUO.mjs';
  const expected = '8dd343ea1ffa703fbf286d53d286d35dc1164287997947f030d26bb71fb40559';
  if (crypto.createHash('sha256').update(fs.readFileSync(guardModule)).digest('hex') !== expected)
    throw new Error('Pinned OpenClaw cron timestamp guard changed');
  const start = performance.now();
  const realNow = RealDate.now.bind(RealDate);
  // Alter only the timestamp guard's reference clock. Gateway ownership,
  // authentication, timeout clocks and actual record timestamps stay native.
  RealDate.now = function benchmarkCronTimestampNow() {
    const stack = new Error().stack || '';
    if (stack.includes('validateScheduleTimestamp') && stack.includes(guardModule)) {
      const declared = clockFile ? JSON.parse(fs.readFileSync(clockFile, 'utf8')).epoch : target;
      const epoch = RealDate.parse(declared);
      if (!Number.isFinite(epoch)) throw new Error('Invalid declared cron replay epoch');
      return epoch + Math.floor(performance.now() - start);
    }
    return realNow();
  };
}
