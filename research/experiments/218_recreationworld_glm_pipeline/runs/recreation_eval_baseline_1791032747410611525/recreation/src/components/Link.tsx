import { type MouseEvent, type ReactNode } from 'react';

export function navigate(to: string) {
  window.history.pushState({}, '', to);
  window.dispatchEvent(new Event('popstate'));
  window.scrollTo(0, 0);
}

interface LinkProps {
  to: string;
  children: ReactNode;
  className?: string;
  ariaLabel?: string;
}

export default function Link({ to, children, className, ariaLabel }: LinkProps) {
  const onClick = (e: MouseEvent<HTMLAnchorElement>) => {
    if (to.startsWith('/') && !to.startsWith('//')) {
      e.preventDefault();
      navigate(to);
    }
  };
  return (
    <a href={to} onClick={onClick} className={className} aria-label={ariaLabel}>
      {children}
    </a>
  );
}
