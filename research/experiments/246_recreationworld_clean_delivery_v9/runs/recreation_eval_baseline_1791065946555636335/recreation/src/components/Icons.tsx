import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

export function ChevronCircle(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true" {...props}>
      <circle cx="12" cy="12" r="10" fill="currentColor" />
      <path d="M10.4 7.2 15.2 12l-4.8 4.8" fill="none" stroke="#00274c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function ArrowRightCircle(props: IconProps) {
  return <ChevronCircle {...props} />;
}

export function SearchIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" {...props}>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m15.5 15.5 5 5" />
    </svg>
  );
}

export function HomeIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true" fill="currentColor" {...props}>
      <path d="M12 3 2 11h3v9h6v-6h2v6h6v-9h3z" />
    </svg>
  );
}

export function PlayCircle(props: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="1em" height="1em" aria-hidden="true" {...props}>
      <circle cx="32" cy="32" r="30" fill="rgba(0,0,0,0.25)" stroke="#fff" strokeWidth="2.5" />
      <path d="M26 20.5 44 32 26 43.5z" fill="#fff" />
    </svg>
  );
}

export function PhoneIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true" fill="currentColor" {...props}>
      <path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.24 11.4 11.4 0 0 0 3.6.58 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1 11.4 11.4 0 0 0 .58 3.6 1 1 0 0 1-.25 1z" />
    </svg>
  );
}

export function MailIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true" fill="currentColor" {...props}>
      <path d="M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Zm9 8.2 8-5.2H4z" />
    </svg>
  );
}

export function LockIcon(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true" fill="currentColor" {...props}>
      <path d="M17 9h-1V7a4 4 0 0 0-8 0v2H7a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1V10a1 1 0 0 0-1-1Zm-7-2a2 2 0 0 1 4 0v2h-4Z" />
    </svg>
  );
}

export function Brand({ name }: { name: string }) {
  const paths: Record<string, string> = {
    Streamly: "M13.5 2h-3v9.6a2.6 2.6 0 1 1-2.1-2.55V5.9A5.7 5.7 0 1 0 13.5 11.6V6.9a6.6 6.6 0 0 0 3.9 1.25V5.05A4 4 0 0 1 13.5 2Z",
    Z: "M3 3h11l-8 8h8v3H3l8-8H3Z",
    Skylark: "M12 2 3 20l9-4 9 4Z",
    Vidcast: "M3 6h12v12H3Zm13 3.5 5-3v9l-5-3Z",
    Photogram: "M8 3h8a5 5 0 0 1 5 5v8a5 5 0 0 1-5 5H8a5 5 0 0 1-5-5V8a5 5 0 0 1 5-5Zm4 4.6A4.4 4.4 0 1 0 16.4 12 4.4 4.4 0 0 0 12 7.6Zm5-1.4a1.1 1.1 0 1 0 1.1 1.1A1.1 1.1 0 0 0 17 6.2Z",
    Loopit: "M12 3a9 9 0 1 0 9 9h-3a6 6 0 1 1-6-6Z",
    Careerly: "M4 7h16v13H4Zm4-4h8v3H8Z",
  };
  return (
    <svg viewBox="0 0 24 24" width="1em" height="1em" aria-hidden="true" fill="currentColor">
      <path d={paths[name] ?? paths.Streamly} />
    </svg>
  );
}
