import { useState, type ReactNode } from "react";
import { Link } from "@/lib/router";
import { cn } from "@/utils/cn";
import { ChevronRight, CircleArrowRight } from "./Icons";

export function PageTitle({ children }: { children: ReactNode }) {
  return (
    <div className="bg-band py-6 text-center">
      <h2 className="section-title text-[26px] text-white md:text-[30px]">{children}</h2>
    </div>
  );
}

export type SidebarEntry =
  | { kind?: "link"; label: string; to: string; note?: string }
  | { kind: "group"; label: string; items: { label: string; to: string }[] };

export type SidebarGroup = {
  heading: string;
  links: SidebarEntry[];
};

/** One entry inside a side panel: a plain link, or an expandable group. */
function PanelEntry({ entry }: { entry: SidebarEntry }) {
  const [open, setOpen] = useState(false);

  if (entry.kind === "group") {
    return (
      <li>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          className="flex w-full items-center justify-between gap-2 px-4 py-[7px] text-left text-[13.5px] text-maize hover:bg-white/5"
        >
          <span>{entry.label}</span>
          <ChevronRight
            size={13}
            className={cn("shrink-0 transition-transform", open && "rotate-90")}
          />
        </button>
        {open && (
          <ul className="bg-[#3a3a3a] py-1">
            {entry.items.map((it) => (
              <li key={it.label}>
                <Link
                  to={it.to}
                  className="block px-6 py-[5px] text-[13px] text-white/85 hover:text-maize"
                >
                  {it.label}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </li>
    );
  }

  return (
    <li>
      <Link
        to={entry.to}
        className="group flex items-center justify-between gap-2 px-4 py-[7px] text-[13.5px] text-white/90 hover:text-maize"
      >
        <span>
          {entry.label}
          {entry.note && (
            <em className="ml-1 text-[11px] text-white/50 uppercase not-italic">
              {entry.note}
            </em>
          )}
        </span>
        <CircleArrowRight
          size={13}
          className="shrink-0 text-maize opacity-70 group-hover:opacity-100"
        />
      </Link>
    </li>
  );
}

export function LinkPanel({
  group,
  className,
}: {
  group: SidebarGroup;
  className?: string;
}) {
  return (
    <nav className={cn("bg-navy-panel", className)}>
      <h4 className="bg-[#123a66] px-4 py-2 font-cond text-[13px] font-normal tracking-[0.1em] text-maize uppercase">
        {group.heading}
      </h4>
      <ul className="py-1">
        {group.links.map((l) => (
          <PanelEntry key={l.label} entry={l} />
        ))}
      </ul>
    </nav>
  );
}

export function SidebarPage({
  title,
  intro,
  groups,
  sidebarImage,
  sidebarCaption,
  sidebarImageAlt,
  sidebarLink,
}: {
  title: string;
  intro: string;
  groups: SidebarGroup[];
  sidebarImage?: string;
  sidebarCaption?: string;
  sidebarImageAlt?: string;
  sidebarLink?: { label: string; to: string };
}) {
  return (
    <>
      <PageTitle>{title}</PageTitle>
      <section className="bg-[#333] py-8">
        <div className="mx-auto max-w-[1180px] px-5">
          <p className="mx-auto mb-8 max-w-[900px] text-center text-[15px] leading-relaxed text-white/85">
            {intro}
          </p>
          <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {groups.map((g) => (
                <LinkPanel key={g.heading} group={g} />
              ))}
            </div>
            {sidebarImage && (
              <figure className="self-start" aria-label={sidebarCaption ?? sidebarImageAlt}>
                <img
                  src={sidebarImage}
                  alt={sidebarImageAlt ?? sidebarCaption ?? ""}
                  className="w-full object-cover"
                  loading="lazy"
                />
                {sidebarCaption && (
                  <figcaption className="mt-2 text-[13px] leading-snug text-maize/90">
                    {sidebarCaption}
                    {sidebarLink && (
                      <>
                        {" "}
                        <Link
                          to={sidebarLink.to}
                          className="inline-flex items-center gap-1 underline hover:text-white"
                        >
                          {sidebarLink.label}
                          <CircleArrowRight size={12} />
                        </Link>
                      </>
                    )}
                  </figcaption>
                )}
              </figure>
            )}
          </div>
        </div>
      </section>
    </>
  );
}

export function Voices({
  label,
  image,
  caption,
  alt,
}: {
  label: string;
  image: string;
  caption: string;
  alt?: string;
}) {
  return (
    <section aria-label={label} className="relative">
      <img src={image} alt={alt ?? caption} className="h-[420px] w-full object-cover md:h-[540px]" />
      <div className="absolute bottom-8 left-1/2 w-[min(92%,680px)] -translate-x-1/2 bg-[#1c1c1c]/80 px-5 py-4 md:left-16 md:translate-x-0">
        <p className="flex items-start gap-3 text-[13px] leading-snug text-white/85">
          <span className="mt-[3px] text-maize">
            <ChevronRight size={12} />
          </span>
          {caption}
        </p>
      </div>
    </section>
  );
}

export function ProsePage({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <>
      <PageTitle>{title}</PageTitle>
      <section className="bg-[#f4f4f4] py-10">
        <div className="prose-page mx-auto max-w-[820px] px-5 text-[14px] leading-relaxed text-[#333]">
          {children}
        </div>
      </section>
    </>
  );
}
