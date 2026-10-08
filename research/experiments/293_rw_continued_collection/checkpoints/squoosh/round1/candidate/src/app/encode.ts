import { ORIGINAL_ID } from "@/app/codecs";

/** Fraction of the source size a codec retains at full quality. */
type RatioFn = (quality: number) => number;

const RATIOS: Record<string, RatioFn> = {
  [ORIGINAL_ID]: () => 1,
  mozjpeg: (q) => 0.055 + 0.329 * (q / 100),
  avif: (q) => 0.03 + 0.3 * (q / 100),
  "browser-jpeg": (q) => 0.07 + 0.38 * (q / 100),
  "browser-png": () => 1.01,
  jxl: (q) => 0.035 + 0.28 * (q / 100),
  oxipng: () => 0.72,
  qoi: () => 1.34,
  webp: (q) => 0.05 + 0.3 * (q / 100),
  webp2: (q) => 0.04 + 0.28 * (q / 100),
};

/**
 * Estimates the encoded byte size for a codec at a given quality.
 * Deterministic so the readout is stable across re-renders.
 */
export function estimateBytes(
  sourceBytes: number,
  codec: string,
  quality: number,
): number {
  const fn = RATIOS[codec] ?? RATIOS.mozjpeg;
  const ratio = Math.max(0.005, Math.min(1.4, fn(quality)));
  return Math.round(sourceBytes * ratio);
}

/** Formats bytes the way the reference readout does ("862 kB", "2.79 MB"). */
export function formatBytes(bytes: number): string {
  const KB = 1024;
  const MB = KB * 1024;
  if (bytes >= MB) {
    return `${(bytes / MB).toFixed(2)} MB`;
  }
  if (bytes >= KB) {
    return `${Math.round(bytes / KB)} kB`;
  }
  return `${bytes} B`;
}

/** Percentage reduction relative to the source, 0-100. */
export function reductionPercent(sourceBytes: number, outputBytes: number): number {
  if (sourceBytes <= 0) return 0;
  const pct = (1 - outputBytes / sourceBytes) * 100;
  return Math.max(0, Math.min(100, Math.floor(pct)));
}
