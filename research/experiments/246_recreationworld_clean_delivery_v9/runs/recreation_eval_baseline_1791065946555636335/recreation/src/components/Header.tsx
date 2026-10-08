import { useState } from "react";
import { Link, useRouter } from "@/router";
import { audiences, mainNav, quickLinks } from "@/data/site";
import { asset } from "@/assets";
import { HomeIcon, SearchIcon } from "./Icons";

export function Header({ reportLabel, overlay = false }: { reportLabel: string; overlay?: boolean }) {
  const { path } = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [quickOpen, setQuickOpen] = useState(false);

  const isActive = (to: string) => {
    const base = to === "/" ? "/" : to;
    return to === "/" ? path === "/" : path === base;
  };

  return (
    <header
      className={`z-30 bg-[rgba(0,50,106,0.80)] ${overlay ? "absolute left-0 top-0 w-full" : "relative"}`}
    >
      <div className="mx-auto max-w-[1440px]">
        {/* Brand + utility bar */}
        <div className="relative flex flex-wrap items-start lg:block">
          <h1 className="m-0 shrink-0 lg:float-left">
            <Link
              to="/"
              className="block h-[138px] w-[132px] bg-[#00274c] bg-[length:100%_100%]"
              style={{ textIndent: "-9000px", backgroundImage: `url(${asset("/skins/um2013/media/images/umich-logo.png")})` }}
            >
              Corravale University
            </Link>
          </h1>
          <div className="min-w-0 flex-1 bg-[#003e78] py-[10px] text-right lg:block">
            <div className="inline-block align-top pr-[15px]">
              <Link
                to="/_404.html"
                className="relative inline-block rounded-[2px] bg-[#ffcb0b] px-[32px] py-[8px] text-[12px] leading-[15px] text-[#002c5a] no-underline transition-all duration-200 hover:bg-[#fddd67]"
              >
                <span>{reportLabel}</span>
                <span className="absolute right-[10px] top-1/2 -mt-[0.5em] text-[14px]">›</span>
              </Link>
            </div>
            <div className="inline-block align-top">
              <form
                role="search"
                className="relative text-right"
                onSubmit={(e) => {
                  e.preventDefault();
                  window.location.href = "/_404.html";
                }}
              >
                <label className="block">
                  <span className="hidden-label">Search for:</span>
                  <input
                    type="search"
                    placeholder="Search"
                    aria-label="Search for:"
                    className="w-[186px] rounded-[2px] border-none px-[10px] py-[8px] pr-[28px] font-[Roboto] text-[12px] outline-none"
                  />
                </label>
                <button
                  type="submit"
                  className="absolute right-[6px] top-1/2 -mt-[7px] -ml-[17px] cursor-pointer border-none bg-transparent p-0 text-[14px] text-black"
                >
                  <span className="hidden-label">Search</span>
                  <SearchIcon className="align-middle" />
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Audiences + quick links */}
        <div className="clear-both pb-[10px] pt-[16px] font-['Roboto_Condensed'] font-bold tracking-[1px] lg:pt-[30px]">
          <div className="mx-auto flex max-w-[1200px] flex-col items-start justify-between gap-[10px] px-[10px] lg:flex-row lg:gap-0">
            <nav aria-label="Audiences" className="w-full text-[11px] uppercase lg:order-1 lg:ml-[30px] lg:w-[690px]">
              <ul className="m-0 grid list-none grid-cols-2 p-0 lg:flex">
                <li aria-hidden="true" className="border-y border-l border-r border-[#567daa] bg-[#002c5a] px-[10px] py-[10px] text-[#ffcb0b] lg:border-r-0">
                  For:
                </li>
                {audiences.map((a) => (
                  <li
                    key={a.to}
                    className="border-y border-l border-r border-t-0 border-[#567daa] bg-[#002c5a] lg:border-l-0 lg:border-t"
                  >
                    <Link
                      to={a.to}
                      className="block px-[10px] py-[10px] text-[#ffcb0b] no-underline transition-all duration-200 hover:bg-[#0d57aa]"
                    >
                      {a.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
            <details className="relative z-10 text-[12px] lg:order-2" open={quickOpen} onToggle={(e) => setQuickOpen((e.target as HTMLDetailsElement).open)}>
              <summary className="relative block w-[166px] cursor-pointer list-none rounded-[2px_3px_3px_2px] bg-[#ffcb0b] p-[10px] uppercase leading-none text-[#002c5a] transition-all duration-200">
                Quick Links
                <span className="absolute right-0 top-0 rounded-[0_2px_2px_0] bg-[#444] p-[4px] text-[16px] text-white">+</span>
              </summary>
              <nav aria-label="Quick Links" className="absolute right-0 w-[230px] border border-[#4b4b4b] bg-[#002c5a] p-[10px] shadow-lg">
                <ul className="m-0 list-none p-0 text-[12px] normal-case tracking-normal">
                  {quickLinks.map((q) => (
                    <li key={q.label} className="border-b border-dotted border-[#8e8c8c] last:border-b-0">
                      <Link to={q.to} className="block py-[6px] font-normal text-white no-underline hover:text-[#ffcb0b]">
                        <span className="hover:border-b hover:border-dotted hover:border-[#ffcb0b]">{q.label}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            </details>
          </div>
        </div>

        {/* Main nav */}
        <nav aria-label="Main Menu" className="clear-both mt-[10px] border-y border-[#567daa]">
          <div className="font-[Georgia,'Times_New_Roman',Times,serif] text-[16px]">
            <div className="lg:hidden">
              <button
                type="button"
                onClick={() => setMenuOpen((v) => !v)}
                className="flex w-full items-center justify-between bg-transparent px-[15px] py-[12px] text-white"
              >
                <span className="text-[16px] font-bold">Main Menu</span>
                <span className="text-[18px]">{menuOpen ? "×" : "≡"}</span>
              </button>
            </div>
            <ul
              className={`${menuOpen ? "block" : "hidden"} m-0 list-none border-r border-[#567daa] p-0 lg:flex`}
            >
              <li className="relative border-l border-[#567daa] text-center lg:flex-[0_0_5%]">
                <Link
                  to="/"
                  aria-current={isActive("/") ? "page" : undefined}
                  className={`group relative flex w-full items-center justify-center px-0 py-[10px] no-underline transition-all duration-200 ${
                    isActive("/") ? "bg-[#0d57aa] text-[#ffcb0b]" : "text-white"
                  }`}
                >
                  <span className="hidden-label">Home</span>
                  <HomeIcon className="h-[16px] w-[16px] group-hover:text-[#ffcb0b]" />
                </Link>
              </li>
              {mainNav.map((item) => (
                <li key={item.to} className="relative grow border-l border-[#567daa] text-center">
                  <Link
                    to={item.to}
                    aria-current={isActive(item.to) ? "page" : undefined}
                    className={`block w-full whitespace-nowrap px-[10px] py-[10px] no-underline transition-all duration-200 ${
                      isActive(item.to) ? "bg-[#0d57aa] text-[#ffcb0b]" : "text-white hover:text-[#ffcb0b]"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </nav>
      </div>
    </header>
  );
}
