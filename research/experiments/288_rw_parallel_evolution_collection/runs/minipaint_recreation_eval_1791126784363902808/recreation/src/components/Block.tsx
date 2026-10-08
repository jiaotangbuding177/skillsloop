import { useState, type ReactNode } from "react";
import { cn } from "@/utils/cn";

interface Props {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
}

export function Block({ title, children, defaultOpen = true, className }: Props) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className={cn("mp-block", !open && "collapsed", className)}>
      <h2 className="mp-block-heading" onClick={() => setOpen((o) => !o)}>
        <span>{title}</span>
        <span className={cn("mp-caret", open && "up")} aria-hidden="true">
          &#9650;
        </span>
      </h2>
      <div className="mp-block-body">{children}</div>
    </section>
  );
}
