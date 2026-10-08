import { useState, type FormEvent } from "react";
import { Link, useRouter } from "@/lib/router";
import { cn } from "@/utils/cn";
import { audiences, chromeFor, mainMenu } from "@/data/site";
import { img } from "@/data/assets";
import {
  Bars,
  ChevronDown,
  ChevronRight,
  Close,
  Home,
} from "./Icons";

/** Normalize a route to a trailing-slash form so label lookups stay stable. */
function withTrailingSlash(path: string) {
  if (path === "/" || path.endsWith("/")) return path;
  return path + "/";
}

export function Header({ path }: { path: string }) {
  const [quickOpen, setQuickOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const route = withTrailingSlash(path);
  const chrome = chromeFor(route);
  const { navigate } = useRouter();

  function onSearch(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const value = new FormData(e.currentTarget).get("keywords");
    const q = typeof value === "string" ? value.trim() : "";
    navigate(q ? `/search/?keywords=${encodeURIComponent(q)}` : "/search/");
  }
  const activeIndex = mainMenu.findIndex(
    (item) => item.to !== "/" && (route === item.to || route.startsWith(item.to))
  );

  return (
    <header className="relative z-30 bg-navy">
      <div className="mx-auto flex max-w-[1440px] items-start px-4 lg:px-0">
        <Link
          to="/"
          className="relative z-40 mt-0 block shrink-0"
          aria-label="Corravale University"
        >
          <img src={img.logo} alt="Corravale University" className="w-[130px] shadow-lg lg:w-[170px]" />
        </Link>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex flex-col gap-2 py-2 lg:flex-row lg:items-center lg:justify-end lg:gap-3 lg:pt-3">
            <Link
              to="/_404.html"
              className="flex items-center justify-center gap-2 bg-maize px-3 py-[6px] text-center font-cond text-[13px] text-[#0b1b2b] hover:bg-[#ffd633] lg:text-[14px]"
            >
              <span className="hidden sm:inline">{chrome.report}</span>
              <span className="sm:hidden">Report Misconduct</span>
              <span className="grid h-[14px] w-[14px] shrink-0 place-items-center rounded-full border border-[#0b1b2b] text-[9px] leading-none">
                i
              </span>
            </Link>
            <form className="flex items-center" onSubmit={onSearch} role="search">
              <label className="sr-only" htmlFor="header-search">
                {chrome.searchLabel}
              </label>
              <span className="flex h-[30px] w-full items-center rounded-[3px] bg-white pl-3 lg:w-[300px]">
                <input
                  id="header-search"
                  name="keywords"
                  type="search"
                  placeholder="Search"
                  className="h-full w-full bg-transparent text-[13px] text-[#333] outline-none"
                />
                <button
                  type="submit"
                  aria-label="Search"
                  className="grid h-full w-[30px] shrink-0 place-items-center text-[#333]"
                >
                  <SearchGlyph />
                </button>
              </span>
            </form>
          </div>

          <div className="flex flex-col gap-2 pb-2 lg:flex-row lg:items-stretch lg:justify-between lg:pb-3">
            <nav aria-label={chrome.audienceLabel}>
              <ul className="grid grid-cols-2 border-t border-l border-white/25 sm:grid-cols-3 lg:flex lg:border-0">
                <li className="border-r border-b border-white/25 px-3 py-[7px] font-cond text-[12px] tracking-[0.1em] text-white uppercase lg:border-0 lg:bg-white/10">
                  For:
                </li>
                {audiences.map((a) => (
                  <li key={a.to} className="border-r border-b border-white/25 lg:border-0">
                    <Link
                      to={a.to}
                      className="block h-full px-3 py-[7px] font-cond text-[12px] tracking-[0.08em] text-white uppercase hover:bg-white/15"
                    >
                      {a.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
            <div className="relative shrink-0">
              <button
                onClick={() => setQuickOpen((v) => !v)}
                aria-expanded={quickOpen}
                className="block w-full bg-maize px-4 py-[6px] font-cond text-[13px] tracking-[0.12em] text-[#0b1b2b] uppercase hover:bg-[#ffd633] lg:w-auto"
              >
                {chrome.quickTitle}
              </button>
              {quickOpen && (
                <div className="absolute top-[calc(100%+8px)] right-0 z-50 w-[220px] bg-band py-3 shadow-xl">
                  <ul className="divide-y divide-white/10">
                    {chrome.quick.map(([label, to]) => (
                      <li key={label}>
                        <Link
                          to={to}
                          onClick={() => setQuickOpen(false)}
                          className="block px-4 py-[7px] text-[14px] text-white/90 hover:bg-white/10 hover:text-white"
                        >
                          {label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <nav aria-label={chrome.menuLabel} className="bg-nav">
        <div className="mx-auto flex max-w-[1440px] items-stretch">
          <ul className="hidden flex-1 items-stretch lg:flex">
            {mainMenu.map((item, i) => (
              <li key={item.to} className="flex-1">
                <Link
                  to={item.to}
                  className={cn(
                    "flex h-full items-center justify-center gap-2 border-r border-white/15 px-2 py-[12px] font-cond text-[15px] text-white hover:bg-navhover",
                    i === activeIndex && "bg-navy"
                  )}
                >
                  {item.label === "Home" ? (
                    <>
                      <Home size={15} />
                      <span className="sr-only">Home</span>
                    </>
                  ) : (
                    item.label
                  )}
                </Link>
              </li>
            ))}
          </ul>
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex w-full items-center justify-between gap-3 bg-nav px-4 py-3 font-cond text-[15px] tracking-[0.1em] text-white uppercase lg:hidden"
            aria-expanded={menuOpen}
          >
            <span className="flex items-center gap-2">
              <Bars size={16} /> Main Menu
            </span>
            {menuOpen ? <Close size={16} /> : <ChevronDown size={14} />}
          </button>
        </div>
        {menuOpen && (
          <ul className="lg:hidden">
            {mainMenu.map((item) => (
              <li key={item.to}>
                <Link
                  to={item.to}
                  onClick={() => setMenuOpen(false)}
                  className="flex items-center justify-between border-b border-white/15 bg-nav px-5 py-3 font-cond text-[16px] text-white"
                >
                  {item.label}
                  <ChevronRight size={14} />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </nav>
    </header>
  );
}

export function SearchGlyph() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4">
      <circle cx="11" cy="11" r="6.5" />
      <path d="M20 20l-4.2-4.2" strokeLinecap="round" />
    </svg>
  );
}
