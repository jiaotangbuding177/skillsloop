import { cn } from "@/utils/cn";

/** Builds a smooth closed band-wave path across the full width. */
function bandPath(opts: {
  width: number;
  height: number;
  baseline: number;
  amplitude: number;
  cycles: number;
  phase: number;
}): string {
  const { width, height, baseline, amplitude, cycles, phase } = opts;
  const steps = cycles * 12;
  const pts: Array<[number, number]> = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    pts.push([
      width * t,
      baseline - amplitude * Math.sin(2 * Math.PI * cycles * t + phase),
    ]);
  }
  const f = (v: number) => (Math.round(v * 10) / 10).toString();
  let d = `M${f(pts[0][0])} ${f(pts[0][1])}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(i - 1, 0)];
    const p1 = pts[i];
    const p2 = pts[i + 1];
    const p3 = pts[Math.min(i + 2, pts.length - 1)];
    const c1x = p1[0] + (p2[0] - p0[0]) / 6;
    const c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6;
    const c2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += `C${f(c1x)} ${f(c1y)} ${f(c2x)} ${f(c2y)} ${f(p2[0])} ${f(p2[1])}`;
  }
  d += `L${width} ${height}L0 ${height}Z`;
  return d;
}

/**
 * The two-tone wave that caps the blue "try one of these" band.
 * Rendered flipped above the band, matching the reference's overhang curve.
 */
export function BandWave({ className }: { className?: string }) {
  return (
    <svg
      className={cn("band-wave", className)}
      viewBox="0 0 1920 140"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        className="wave-sub"
        d={bandPath({
          width: 1920,
          height: 140,
          baseline: 62,
          amplitude: 34,
          cycles: 1,
          phase: -0.15,
        })}
      />
      <path
        className="wave-main"
        d={bandPath({
          width: 1920,
          height: 140,
          baseline: 88,
          amplitude: 38,
          cycles: 1,
          phase: -0.4,
        })}
      />
    </svg>
  );
}

/** Single-tone wave used to fade a band into the section below it. */
export function EdgeWave({
  className,
  color,
  amplitude = 22,
  baseline = 44,
  phase = 0.6,
}: {
  className?: string;
  color: "info" | "footer";
  amplitude?: number;
  baseline?: number;
  phase?: number;
}) {
  return (
    <svg
      className={cn(className)}
      viewBox="0 0 1920 79"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path
        className={color === "info" ? "wave-info" : "wave-footer"}
        d={bandPath({
          width: 1920,
          height: 79,
          baseline,
          amplitude,
          cycles: 1,
          phase,
        })}
      />
    </svg>
  );
}
