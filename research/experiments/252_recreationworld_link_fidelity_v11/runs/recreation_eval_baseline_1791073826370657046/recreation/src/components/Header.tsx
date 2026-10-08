import { useState } from "react";
import { Link } from "@/lib/router";
import { cn } from "@/utils/cn";
import { audiences, mainMenu } from "@/data/site";
import { img } from "@/data/assets";
import {
  Bars,
  ChevronDown,
  ChevronRight,
  Close,
  Home,
} from "./Icons";

function searchLabel(path: string) {
  switch (path) {
    case "/life-at-michigan/":
      return "Search site:";
    case "/athletics/":
    case "/faculty-staff/":
    case "/contact/":
      return "Find pages:";
    case "/health-medicine/":
    case "/parents/":
    case "/prospective-students/":
      return "Search here:";
    default:
      return "Search for:";
  }
}

function reportLabel(path: string) {
  switch (path) {
    case "/about/":
      return "Report Sexual Misconduct, Discrimination, and Harassment";
    case "/academics/":
      return "Report Misconduct, Bias, Discrimination and Harassment";
    case "/life-at-michigan/":
      return "Report Misconduct, Discrimination, and Bias Incidents";
    case "/athletics/":
      return "Report Misconduct, Bias, Discrimination and Harassment";
    case "/research/":
      return "Report Misconduct, Discrimination and Harassment Concerns";
    case "/health-medicine/":
      return "Report Misconduct, Discrimination and Bias Incidents";
    case "/initiatives/":
      return "Report Sexual Misconduct, Discrimination and Harassment";
    case "/giving/":
      return "Report Misconduct, Bias, Discrimination and Harassment";
    case "/prospective-students/":
      return "Report Misconduct, Discrimination, and Harassment Concerns";
    case "/current-students/":
      return "Report Misconduct, Discrimination, Bias and Harassment";
    case "/faculty-staff/":
      return "Report Misconduct, Bias, Discrimination and Harassment";
    case "/parents/":
      return "Report Misconduct, Discrimination, and Harassment Concerns";
    case "/alumni/":
      return "Report Sexual Misconduct, Discrimination and Harassment";
    case "/contact/":
      return "Report Misconduct, Bias Incidents and Harassment Here";
    default:
      return "Report Sexual Misconduct, Discrimination, and Bias Concerns";
  }
}

export function Header({ path }: { path: string }) {
  const [audOpen, setAudOpen] = useState(false);
  const [quickOpen, setQuickOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const activeIndex = mainMenu.findIndex(
    (item) =>
      item.to !== "/" &&
      (path === item.to || path.startsWith(item.to.replace(/\/$/, "") + "/"))
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
          <div className="flex items-center justify-between gap-2 py-2 lg:pt-3">
            <div className="hidden lg:block" />
            <div className="flex flex-1 flex-wrap items-center justify-end gap-3">
              <Link
                to="/_404.html"
                className={cn(
                  "flex items-center gap-2 bg-maize px-3 py-[6px] font-cond text-[13px] text-[#0b1b2b] hover:bg-[#ffd633]",
                  "lg:text-[14px]"
                )}
              >
                <span className="hidden sm:inline">{reportLabel(path)}</span>
                <span className="sm:hidden">Report Misconduct</span>
                <span className="grid h-[14px] w-[14px] place-items-center rounded-full border border-[#0b1b2b] text-[9px] leading-none">
                  i
                </span>
              </Link>
              <form
                className="hidden items-center gap-2 md:flex"
                onSubmit={(e) => e.preventDefault()}
                role="search"
              >
                <label className="sr-only" htmlFor="header-search">
                  {searchLabel(path)}
                </label>
                <input
                  id="header-search"
                  type="search"
                  placeholder="Search"
                  className="h-[30px] w-[190px] rounded-sm border border-[#c7d2de] bg-white px-3 text-[13px] text-[#333] outline-none"
                />
                <button
                  type="submit"
                  aria-label="Search"
                  className="grid h-[30px] w-[34px] place-items-center text-white"
                >
                  <SearchGlyph />
                </button>
              </form>
            </div>
          </div>

          <div className="flex items-stretch justify-between gap-3 pb-2 lg:pb-3">
            <div className="hidden items-center gap-2 lg:flex">
              <button
                onClick={() => setAudOpen((v) => !v)}
                className="flex items-center gap-2 border border-white/40 bg-white/10 px-3 py-[6px] font-cond text-[12px] tracking-[0.12em] text-white uppercase"
              >
                For:
              </button>
              <nav aria-label="Audiences" className="flex">
                <ul className="flex flex-wrap">
                  {audiences.map((a) => (
                    <li key={a.to}>
                      <Link
                        to={a.to}
                        className="block border border-white/20 bg-[#1a4d80]/70 px-3 py-[6px] font-cond text-[12px] tracking-[0.08em] text-white uppercase hover:bg-[#1a4d80]"
                      >
                        {a.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
            <button
              onClick={() => setAudOpen((v) => !v)}
              className="flex items-center gap-2 border border-white/40 px-3 py-[6px] font-cond text-[12px] tracking-[0.1em] text-white uppercase lg:hidden"
            >
              For Audiences <ChevronDown size={12} />
            </button>
            <button
              onClick={() => setQuickOpen((v) => !v)}
              className="hidden shrink-0 bg-maize px-4 py-[6px] font-cond text-[13px] tracking-[0.12em] text-[#0b1b2b] uppercase hover:bg-[#ffd633] lg:block"
            >
              Quick Links
            </button>
          </div>
        </div>
      </div>

      {audOpen && (
        <ul className="mx-auto flex max-w-[1440px] flex-wrap gap-2 px-4 pb-3 lg:hidden">
          {audiences.map((a) => (
            <li key={a.to}>
              <Link
                to={a.to}
                onClick={() => setAudOpen(false)}
                className="block border border-white/20 bg-[#1a4d80]/70 px-3 py-[6px] font-cond text-[12px] tracking-[0.08em] text-white uppercase"
              >
                {a.label}
              </Link>
            </li>
          ))}
        </ul>
      )}

      {quickOpen && (
        <div className="bg-navy-deep">
          <ul className="mx-auto grid max-w-[1440px] grid-cols-2 gap-x-8 gap-y-2 px-6 py-4 md:grid-cols-3 lg:grid-cols-4">
            {[
              ["Corravale Access", "/_404.html"],
              ["Email", "/_404.html"],
              ["Nimbus", "/_404.html"],
              ["Library Catalog", "/_404.html"],
              ["Academic Calendar", "/_404.html"],
              ["Costs & Financial Aid", "/_404.html"],
              ["Maps & Directions", "/_404.html"],
              ["Contact Us", "/contact/"],
            ].map(([label, to]) => (
              <li key={label}>
                <Link
                  to={to}
                  onClick={() => setQuickOpen(false)}
                  className="text-[14px] text-white/90 hover:text-maize"
                >
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      <nav aria-label="Main Menu" className="bg-nav">
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
