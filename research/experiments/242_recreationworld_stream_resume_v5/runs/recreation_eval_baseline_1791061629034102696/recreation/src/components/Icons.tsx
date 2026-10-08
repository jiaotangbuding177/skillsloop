import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function base({ size = 14, ...rest }: IconProps, children: React.ReactNode) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {children}
    </svg>
  );
}

export function ArrowCircleRight(props: IconProps) {
  return base(
    props,
    <>
      <circle cx="12" cy="12" r="10" />
      <path d="M9 12h6M12 9l3 3-3 3" />
    </>,
  );
}

export function SearchIcon(props: IconProps) {
  return base(
    { ...props, size: props.size ?? 14 },
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>,
  );
}

export function HomeIcon(props: IconProps) {
  return base(
    { ...props, size: props.size ?? 14 },
    <>
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5 9.5V21h14V9.5" />
    </>,
  );
}

export function PlayIcon(props: IconProps) {
  return base(
    { ...props, size: props.size ?? 18 },
    <path d="M6 4l14 8-14 8z" fill="currentColor" stroke="none" />,
  );
}

export function ChevronLeft(props: IconProps) {
  return base(props, <path d="m15 6-6 6 6 6" />);
}

export function ChevronRight(props: IconProps) {
  return base(props, <path d="m9 6 6 6-6 6" />);
}

export function ChevronUp(props: IconProps) {
  return base(props, <path d="m6 15 6-6 6 6" />);
}

export function LockIcon(props: IconProps) {
  return base(
    { ...props, size: props.size ?? 11 },
    <>
      <rect x="4" y="10" width="16" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </>,
  );
}

export function EnvelopeIcon(props: IconProps) {
  return base(
    { ...props, size: props.size ?? 11 },
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 7 9 6 9-6" />
    </>,
  );
}

export function PhoneIcon(props: IconProps) {
  return base(
    { ...props, size: props.size ?? 11 },
    <path d="M5 4h4l2 5-3 2a12 12 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z" />,
  );
}

export function HamburgerIcon(props: IconProps) {
  return base(
    { ...props, size: props.size ?? 20 },
    <>
      <path d="M3 6h18M3 12h18M3 18h18" />
    </>,
  );
}
