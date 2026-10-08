/** Original graffiti-style badge mark for the editor logo. */
export function LogoBadge({ size = 30 }: { size?: number }) {
  return (
    <svg
      className="mp-logo-badge"
      width={size}
      height={size}
      viewBox="0 0 60 60"
      role="img"
      aria-label="miniPaint"
    >
      <defs>
        <linearGradient id="mp-logo-g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#e9ffee" />
          <stop offset="1" stopColor="#b7e7c0" />
        </linearGradient>
      </defs>
      <rect x="2" y="6" width="56" height="48" rx="4" fill="url(#mp-logo-g)" stroke="#0d0d0d" strokeWidth="3" />
      <path
        d="M8 40c6-16 12 4 20-10s16 2 24-14"
        fill="none"
        stroke="#0d0d0d"
        strokeWidth="5"
        strokeLinecap="round"
      />
      <path d="M40 12l10 2-4 9" fill="none" stroke="#0d0d0d" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M10 14l9 4" stroke="#ff3b30" strokeWidth="5" strokeLinecap="round" />
      <path d="M14 22l9 4" stroke="#34c759" strokeWidth="5" strokeLinecap="round" />
      <path d="M18 30l9 4" stroke="#0a84ff" strokeWidth="5" strokeLinecap="round" />
    </svg>
  );
}
