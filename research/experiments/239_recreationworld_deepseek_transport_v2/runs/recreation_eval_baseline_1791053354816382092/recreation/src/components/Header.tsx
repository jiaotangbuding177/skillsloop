import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ArrowCircleRight, Search, Home } from "./Icons";
import { cn } from "@/utils/cn";

const AUDIENCE_LINKS = [
  { href: "/prospective-students/", label: "Prospective Students" },
  { href: "/current-students/", label: "Current Students" },
  { href: "/faculty-staff/", label: "Faculty & Staff" },
  { href: "/parents/", label: "Parents" },
  { href: "/alumni/", label: "Alumni" },
];

const QUICK_LINKS: { href: string; label: string }[] = [
  { href: "/_404", label: "Academic Calendar" },
  { href: "/_404", label: "Courses" },
  { href: "/_404", label: "Directory" },
  { href: "/_404", label: "Email" },
  { href: "/_404", label: "Health Email" },
  { href: "/_404", label: "Library Catalog" },
  { href: "/_404", label: "Maps & Directions" },
  { href: "/schools-colleges/", label: "Schools & Colleges" },
  { href: "/_404", label: "Corravale Access" },
];

const MAIN_NAV = [
  { href: "/", label: "Home", home: true },
  { href: "/about/", label: "About" },
  { href: "/academics/", label: "Academics" },
  { href: "/life-at-michigan/", label: "Life at Corravale" },
  { href: "/athletics/", label: "Athletics" },
  { href: "/research/", label: "Research" },
  { href: "/health-medicine/", label: "Health & Medicine" },
  { href: "/initiatives/", label: "Initiatives" },
  { href: "/giving/", label: "Giving" },
];

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const loc = useLocation();

  return (
    <div className="clear" id="header" role="banner">
      <a className="skip" href="#content">
        Skip to main content
      </a>
      <div id="zone-branding">
        <div className="cuv-wrap">
          <h1 className="logo">
            <Link to="/">Corravale University</Link>
          </h1>
        </div>
      </div>
      <div id="zone-utility-bar">
        <div className="cuv-wrap">
          <div className="sexual-misconduct">
            <Link to="/_404">
              Report Sexual Misconduct, Discrimination, and Bias Concerns{" "}
              <ArrowCircleRight className="smic-icon" />
            </Link>
          </div>
          <div className="search">
            <form action="/search/" role="search">
              <label htmlFor="keywords">
                <span className="hidden-vis">Search for:</span>
                <input
                  id="keywords"
                  name="keywords"
                  placeholder="Search"
                  title="Search for:"
                  type="search"
                />
              </label>
              <button type="submit">
                <span className="hidden-vis">Search</span>
                <Search aria-hidden="true" />
              </button>
            </form>
          </div>
        </div>
      </div>
      <div id="zone-audience-quick-links">
        <div className="cuv-wrap">
          <details id="quick-links">
            <summary>Quick Links</summary>
            <nav>
              <ul id="quick-links-content">
                {QUICK_LINKS.map((l) => (
                  <li key={l.label}>
                    <Link to={l.href}>{l.label}</Link>
                  </li>
                ))}
              </ul>
            </nav>
          </details>
          <div aria-label="Audiences" className="clear" id="audience-nav" role="navigation">
            <ul className="clear">
              <li aria-hidden="true">For:</li>
              {AUDIENCE_LINKS.map((l) => (
                <li key={l.href}>
                  <Link to={l.href}>{l.label}</Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
      <div aria-labelledby="main-menu-header" id="zone-main-nav" role="navigation">
        <div className="cuv-wrap">
          <div id="main-nav">
            <button
              type="button"
              className="hamburger-header"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((o) => !o)}
            >
              <h3 id="main-menu-header">Main Menu</h3>
            </button>
            <ul aria-hidden={!menuOpen} className={cn("clear", menuOpen && "menu-open")}>
              {MAIN_NAV.map((item) => {
                const active =
                  loc.pathname === item.href ||
                  (item.href !== "/" && loc.pathname.startsWith(item.href));
                return (
                  <li
                    key={item.href}
                    className={cn(item.home && "home-item", active && "active")}
                  >
                    <Link aria-current={active ? "page" : undefined} to={item.href}>
                      {item.home ? (
                        <>
                          <Home className="nav-home-icon" />
                          <span className="hidden-vis">Home</span>
                        </>
                      ) : (
                        item.label
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      </div>
      {menuOpen && (
        <div className="menu-panel">
          <nav aria-label="Main">
            <ul>
              {MAIN_NAV.map((item) => (
                <li key={item.href}>
                  <Link to={item.href} onClick={() => setMenuOpen(false)}>
                    {item.home ? "Home" : item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      )}
    </div>
  );
}
