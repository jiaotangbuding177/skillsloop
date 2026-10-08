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
export function reductionPercent(
  sourceBytes: number,
  outputBytes: number,
): number {
  if (sourceBytes <= 0) return 0;
  const pct = (1 - outputBytes / sourceBytes) * 100;
  return Math.max(0, Math.min(100, Math.floor(pct)));
}
