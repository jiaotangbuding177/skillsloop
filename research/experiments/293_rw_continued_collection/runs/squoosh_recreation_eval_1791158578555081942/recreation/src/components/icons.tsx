import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

/** Image-with-plus glyph used by the big pink drop target. */
export function AddImageIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M19 7v3h-2V7h-3V5h3V2h2v3h3v2h-3zm-3 4V8h-3V5H5a2 2 0 0 0-2 2v12c0 1.1.9 2 2 2h12a2 2 0 0 0 2-2v-8h-3zM5 19l3-4 2 3 3-4 4 5H5z" />
    </svg>
  );
}

/** Download tray glyph. */
export function DownloadIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M5 20h14v-2H5v2zM19 9h-4V3H9v6H5l7 7 7-7z" />
    </svg>
  );
}

/** Chevron used for selects / expanders. */
export function CaretIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 10 6" aria-hidden="true" {...props}>
      <path d="M0 0h10L5 6z" />
    </svg>
  );
}

/** Rotate-icon for the flip / rotate toolbar button. */
export function RotateIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M12 5V1L7 6l5 5V7a5 5 0 0 1 5 5 5 5 0 0 1-5 5v2a7 7 0 0 0 0-14z" />
    </svg>
  );
}

/** Smoothing icon (anti-aliased circle). */
export function SmoothingIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zm0 2a7 7 0 0 1 6.9 5.8A9.2 9.2 0 0 0 12 13a9.2 9.2 0 0 0-6.9-2.2A7 7 0 0 1 12 5zm0 14a7 7 0 0 1-6.9-5.8A9.2 9.2 0 0 1 12 11c2.7 0 5.1.8 6.9 2.2A7 7 0 0 1 12 19z" />
    </svg>
  );
}

/** Checkerboard toggle. */
export function BackgroundIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M3 3h6v6H3V3zm6 6h6v6H9V9zm6-6h6v6h-6V3zM3 15h6v6H3v-6zm12 0h6v6h-6v-6z" />
    </svg>
  );
}

/** Zoom out / in. */
export function MinusIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M5 11h14v2H5z" />
    </svg>
  );
}
export function PlusIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6z" />
    </svg>
  );
}

/** Two-up comparison knob. */
export function SplitKnobIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 40 40" aria-hidden="true" {...props}>
      <circle cx="20" cy="20" r="19" fill="#1d1d1d" />
      <path d="M16 12l-6 8 6 8z" fill="#ff3385" />
      <path d="M24 12l6 8-6 8z" fill="#5fb4e4" />
    </svg>
  );
}

/** Copy-to-other-side arrow. */
export function CopyOverIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path d="M4 4h10l-4-4v3H3a1 1 0 0 0-1 1v6h2V4zm16 16H10l4 4v-3h7a1 1 0 0 0 1-1v-6h-2v6z" />
    </svg>
  );
}

/** Save side settings. */
export function SaveSideIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props} fill="none" strokeWidth="2">
      <circle cx="12" cy="12" r="3.2" />
      <path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.2 5.2l2.1 2.1M16.7 16.7l2.1 2.1M18.8 5.2l-2.1 2.1M7.3 16.7l-2.1 2.1" />
    </svg>
  );
}

/** Import/paste saved settings. */
export function ImportSideIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props} fill="none" strokeWidth="2">
      <rect x="3" y="5" width="18" height="15" rx="2" />
      <path d="M8 3v4M16 3v4M7 13l3.5 3.5L17 10" />
    </svg>
  );
}
