import { Link } from "@/lib/router";
import { FOOTER_CAMPUSES, FOOTER_SOCIAL } from "@/data/site";
import { EnvelopeIcon, LockIcon } from "@/components/Icons";
import { LOGO } from "@/lib/assets";

export default function Footer() {
  return (
    <footer className="site-footer" role="contentinfo">
      <div className="wrap">
        <div className="footer-inner">
          <div className="footer-info">
            <Link
              to="/"
              className="footer-logo"
              style={{ backgroundImage: `url(${LOGO})` }}
            >
              Corravale University
            </Link>
            <nav aria-label="Our Campuses">
              <ul className="campuses">
                {FOOTER_CAMPUSES.map((c) => (
                  <li key={c.label}>
                    <Link
                      to={c.href}
                      onClick={(e) => c.href === "/_404.html" && e.preventDefault()}
                    >
                      <span>{c.label}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
            <ul className="contact">
              <li>
                © 2026{" "}
                <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                  <span>The Board of Regents of Corravale University</span>
                </Link>{" "}
                1240 Larkspur Ave., Fairhaven, MI 48211-1044
              </li>
              <li>
                <Link to="/about/privacy/">
                  <span>
                    <span className="icon">
                      <LockIcon />
                    </span>
                    Privacy Notice
                  </span>
                </Link>
              </li>
              <li className="phone">
                <span className="icon">
                  <span className="sr-only">Phone</span>
                  <PhoneGlyph />
                </span>
                <a href="tel:+1-734-764-1817">+1 (734) 764-1817</a>
              </li>
              <li>
                <Link to="/contact/">
                  <span>
                    <span className="icon">
                      <EnvelopeIcon />
                    </span>
                    Contact us
                  </span>
                </Link>
              </li>
            </ul>
          </div>

          <div className="footer-language">
            <nav aria-label="Careers and Region Specific Websites">
              <ul className="careers">
                <li>
                  <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                    <span>Careers</span>
                  </Link>
                </li>
              </ul>
            </nav>
            <nav aria-label="Social Feeds">
              <ul className="social">
                {FOOTER_SOCIAL.map((s) => (
                  <li key={s.label}>
                    <Link
                      to={s.href}
                      title={s.label}
                      onClick={(e) => e.preventDefault()}
                    >
                      <span className="glyph" aria-hidden="true">
                        {s.glyph}
                      </span>
                      <span>{s.label}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </div>

          <div className="footer-mandatory">
            <nav aria-label="Regulatory Compliance Requirements">
              <ul>
                <li>
                  <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                    <span className="compliance-badge">
                      <strong>TRANSPARENCY</strong>
                      <span>BUDGET &amp; SALARY</span>
                    </span>
                  </Link>
                </li>
                <li>
                  <Link to="/_404.html" onClick={(e) => e.preventDefault()}>
                    <span className="compliance-badge">
                      <strong>CAMPUS SAFETY</strong>
                      <span>Information and Resources</span>
                    </span>
                  </Link>
                </li>
              </ul>
            </nav>
          </div>
        </div>
      </div>
    </footer>
  );
}

function PhoneGlyph() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M5 4h4l2 5-3 2a12 12 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"
        fill="currentColor"
      />
    </svg>
  );
}
