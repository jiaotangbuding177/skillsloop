import type { ReactElement } from "react";
import { Link } from "@/lib/router";
import { footerCampuses, socialFeeds } from "@/data/site";
import { img } from "@/data/assets";
import {
  BarChart,
  BrandFacebook,
  BrandInstagram,
  BrandLinkedIn,
  BrandTikTok,
  BrandX,
  BrandYouTube,
  Envelope,
  Lock,
  Phone,
} from "./Icons";

const socialGlyphs: Record<string, (p: { size?: number }) => ReactElement> = {
  z: ({ size }) => <BrandX size={size} />,
  streamly: ({ size }) => <BrandFacebook size={size} />,
  skylark: ({ size }) => <BrandTikTok size={size} />,
  vidcast: ({ size }) => <BrandYouTube size={size} />,
  photogram: ({ size }) => <BrandInstagram size={size} />,
  loopit: ({ size }) => <BrandTikTok size={size} />,
  careerly: ({ size }) => <BrandLinkedIn size={size} />,
};

export function Footer() {
  return (
    <footer className="bg-navy text-white">
      <div className="mx-auto grid max-w-[1440px] gap-8 px-6 py-8 lg:grid-cols-[300px_1fr_auto] lg:gap-12">
        <div className="flex flex-col gap-4">
          <div className="flex items-start gap-4">
            <Link to="/" aria-label="Corravale University" className="shrink-0">
              <img src={img.logo} alt="Corravale University" className="w-[96px]" />
            </Link>
            <div className="min-w-0 text-[13px] leading-relaxed text-white/90">
              <nav aria-label="Our Campuses">
                <ul className="mb-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[13px]">
                  {footerCampuses.map((c, i) => (
                    <li key={c.label} className="flex items-center gap-2">
                      {i > 0 && <span className="text-white/40">|</span>}
                      <Link to={c.to} className="hover:text-maize">
                        {c.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
              <ul className="space-y-1">
                <li>
                  © 2026{" "}
                  <Link to="/_404.html" className="hover:text-maize">
                    The Board of Regents of Corravale University
                  </Link>{" "}
                  1240 Larkspur Ave., Fairhaven, MI 48211-1044
                </li>
                <li>
                  <Link to="/about/privacy/" className="flex items-center gap-2 hover:text-maize">
                    <Lock size={12} />
                    Privacy Notice
                  </Link>
                </li>
                <li className="flex items-center gap-2">
                  <Phone size={12} />
                  <span className="sr-only">Phone</span>
                  <Link to="tel:+1-734-764-1817" className="hover:text-maize">
                    +1 (734) 764-1817
                  </Link>
                </li>
                <li>
                  <Link to="/contact/" className="flex items-center gap-2 hover:text-maize">
                    <Envelope size={12} />
                    Contact us
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <nav aria-label="Careers and Region Specific Websites">
            <ul>
              <li>
                <Link
                  to="/_404.html"
                  className="inline-block border-b border-white/30 pb-3 text-[14px] hover:text-maize"
                >
                  Careers
                </Link>
              </li>
            </ul>
          </nav>
          <nav aria-label="Social Feeds">
            <ul className="flex flex-wrap gap-3">
              {socialFeeds.map((s) => {
                const Glyph = socialGlyphs[s.icon];
                return (
                  <li key={s.label}>
                    <Link
                      to="/_404.html"
                      aria-label={s.label}
                      className="grid h-[34px] w-[34px] place-items-center rounded-full bg-white/15 text-white hover:bg-white/25"
                    >
                      <Glyph size={16} />
                      <span className="sr-only">{s.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>

        <nav aria-label="Regulatory Compliance Requirements" className="flex items-center gap-6">
          <ul className="flex items-center gap-5">
            <li>
              <Link to="/_404.html" aria-label="Budget and Financial Transparency Disclosures">
                <BadgeTop />
              </Link>
            </li>
            <li>
              <Link to="/_404.html" aria-label="Campus Security Information and Resources" className="flex flex-col items-center">
                <span className="grid h-[80px] w-[72px] place-items-center text-maize">
                  <svg viewBox="0 0 24 24" className="h-[78px] w-[70px]" fill="#2f7fd0">
                    <path d="M12 1.5 3.5 4.2v7.2c0 5.3 3.6 9.9 8.5 11.1 4.9-1.2 8.5-5.8 8.5-11.1V4.2L12 1.5z" stroke="#ffcb05" strokeWidth="1.2" />
                  </svg>
                </span>
                <span className="-mt-1 font-cond text-[12px] tracking-[0.1em] text-white">
                  CAMPUS SAFETY
                </span>
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </footer>
  );
}

function BadgeTop() {
  return (
    <span className="flex flex-col items-center">
      <span className="relative grid h-[80px] w-[80px] place-items-center rounded-full border-[3px] border-maize bg-[#2f7fd0] text-center">
        <span className="absolute top-2 font-cond text-[9px] tracking-[0.08em] text-white">
          TRANSPARENCY
        </span>
        <BarChart size={26} className="text-maize" />
        <span className="absolute bottom-2 font-cond text-[9px] tracking-[0.06em] text-white">
          BUDGET &amp; SALARY
        </span>
      </span>
    </span>
  );
}
