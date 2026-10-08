import { useState } from "react";
import { Link, useRouter } from "@/lib/router";
import {
  AUDEINCE_LINKS,
  MISCONDUCT_LABEL,
  QUICK_LINKS,
} from "@/data/site";
import { HamburgerIcon, HomeIcon, SearchIcon } from "@/components/Icons";
import { LOGO } from "@/lib/assets";

export default function Header() {
  const { path } = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (href: string) =>
    href === "/" ? path === "/" : path.startsWith(href);

  return (
    <header className="site-header" role="banner">
      <div className="wrap">
        <div className="brand-row">
          <Link
            to="/"
            className="brand-logo"
            aria-label="Corravale University home"
            style={{ backgroundImage: `url(${LOGO})` }}
          >
            Corravale University
          </Link>

          <div className="utility-bar">
            <div className="sexual-misconduct">
              <Link
                to="/_404.html"
                className="misconduct-link"
                onClick={(e) => e.preventDefault()}
              >
                {MISCONDUCT_LABEL}
                <span className="icon" aria-hidden="true">
                  <ArrowSpan />
                </span>
              </Link>
            </div>
            <div className="search">
              <form
                className="site-search"
                role="search"
                onSubmit={(e) => e.preventDefault()}
              >
                <label htmlFor="keywords">
                  <span className="sr-only">Search for:</span>
                  <input
                    id="keywords"
                    name="keywords"
                    type="search"
                    placeholder="Search"
                    title="Search for:"
                  />
                </label>
                <button type="submit">
                  <span className="sr-only">Search</span>
                  <SearchIcon />
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="audience-zone">
          <div className="audience-nav" role="navigation" aria-label="Audiences">
            <ul>
              <li aria-hidden="true" style={{ color: "#ffcb0b" }}>
                For:
              </li>
              {AUDEINCE_LINKS.map((a) => (
                <li key={a.href} className={isActive(a.href) ? "is-active" : ""}>
                  <Link to={a.href}>{a.label}</Link>
                </li>
              ))}
            </ul>
          </div>

          <details className="quick-links">
            <summary>
              Quick Links
              <span className="toggle" aria-hidden="true">
                <span />
              </span>
            </summary>
            <nav aria-label="Quick Links">
              <ul>
                {QUICK_LINKS.map((q) => (
                  <li key={q.label}>
                    <Link
                      to={q.href}
                      onClick={(e) => q.href === "/_404.html" && e.preventDefault()}
                    >
                      {q.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </details>
        </div>

        <nav className="main-nav-zone" aria-label="Main Menu">
          <div className="main-nav">
            <button
              className="hamburger"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((v) => !v)}
            >
              <HamburgerIcon />
              Main Menu
            </button>
            <ul className={"menu" + (menuOpen ? " open" : "")}>
              <li className={isActive("/") ? "is-active" : ""}>
                <Link to="/" aria-label="Home">
                  <span className="home-icon">
                    <HomeIcon />
                  </span>
                </Link>
              </li>
              {MAIN_ITEMS.map((item) => (
                <li
                  key={item.href}
                  className={isActive(item.href) ? "is-active" : ""}
                >
                  <Link to={item.href}>{item.label}</Link>
                </li>
              ))}
            </ul>
          </div>
        </nav>
      </div>
    </header>
  );
}

const MAIN_ITEMS = [
  { label: "About", href: "/about/" },
  { label: "Academics", href: "/academics/" },
  { label: "Life at Corravale", href: "/life-at-michigan/" },
  { label: "Athletics", href: "/athletics/" },
  { label: "Research", href: "/research/" },
  { label: "Health & Medicine", href: "/health-medicine/" },
  { label: "Initiatives", href: "/initiatives/" },
  { label: "Giving", href: "/giving/" },
];

function ArrowSpan() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="10" fill="currentColor" />
      <path
        d="M9 12h6M12 9l3 3-3 3"
        stroke="#002c5a"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
