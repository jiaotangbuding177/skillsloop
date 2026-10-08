import { DownloadIcon } from "@/components/icons";
import { cn } from "@/utils/cn";

type Props = {
  /** Human-readable output size, e.g. "862 kB". */
  size: string;
  /** Percentage of the original size retained, 0-100. */
  ratio: number;
  /** Which side of the compare view this bubble anchors to. */
  side: "a" | "b";
  /** True for the untouched original, which shows a neutral badge. */
  original?: boolean;
  /** Disabled state used while an encode is in flight. */
  busy?: boolean;
  onDownload: () => void;
};

function splitSize(size: string): { amount: string; unit: string } {
  const match = size.match(/^([\d.]+)\s*(.*)$/);
  if (!match) return { amount: size, unit: "" };
  return { amount: match[1], unit: match[2] };
}

const BUBBLE_OUTLINE =
  "url(\"data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='186.5' height='280.3'%3E%3Cpath fill='rgba(30,31,29,0.69)' d='M181.5 0H16.4a5 5 0 00-5 5v134L0 146.5h11.4v128.8a5 5 0 005 5h165.1a5 5 0 005-5V5a5 5 0 00-5-5z'/%3E%3C/svg%3E\")";

export function ResultsBubble({
  size,
  ratio,
  side,
  original = false,
  busy = false,
  onDownload,
}: Props) {
  const { amount, unit } = splitSize(size);
  const direction = original || ratio >= 100 ? "" : "↓";
  const shownPercent = original ? "0" : String(Math.max(0, Math.round(ratio)));

  return (
    <div
      className={cn("results", side === "b" && "side-b-results", original && "is-original")}
    >
      <a
        className={cn("dl-btn", busy && "is-busy")}
        href="#"
        role="button"
        aria-label="Download"
        aria-disabled={busy}
        onClick={(e) => {
          e.preventDefault();
          if (!busy) onDownload();
        }}
      >
        <svg
          className="dl-blob"
          viewBox="-1.25 -1.25 2.5 2.5"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        >
          <path d="M1.0083 -0.0115C1.0034 0.2739 0.7441 0.6708 0.5382 0.8371C0.3323 1.0034 0.0071 1.0423 -0.2271 0.9864C-0.4613 0.9305 -0.751 0.7461 -0.867 0.5016C-0.9831 0.2571 -1.0166 -0.2433 -0.9234 -0.4807C-0.8301 -0.7181 -0.556 -0.8567 -0.3076 -0.9226C-0.0591 -0.9884 0.3481 -1.0274 0.5674 -0.8756C0.7867 -0.7238 1.0132 -0.297 1.0083 -0.0115Z" />
        </svg>
        <span className="dl-icon">
          <DownloadIcon />
        </span>
      </a>

      <div className="bubble">
        <div className={cn("bubble-inner", side === "b" && "row-reverse")}>
          <span className="size-tag">
            {amount} <span className="size-unit">{unit}</span>
          </span>
          <span
            className={cn("percent-tag", side === "b" && "points-right")}
          >
            <span className="percent-dir">{direction}</span>
            <span className="percent-val">{shownPercent}</span>
            <span className="percent-char">%</span>
          </span>
        </div>
      </div>
    </div>
  );
}

export { BUBBLE_OUTLINE };
