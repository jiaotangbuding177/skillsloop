import { Link } from "react-router-dom";
import {
  Lock,
  Phone,
  Envelope,
  Facebook,
  XTwitter,
  Bluesky,
  YouTube,
  Instagram,
  TikTok,
  LinkedIn,
} from "./Icons";

const SOCIAL = [
  { title: "Streamly", Icon: Facebook },
  { title: "Z", Icon: XTwitter },
  { title: "Skylark", Icon: Bluesky },
  { title: "Vidcast", Icon: YouTube },
  { title: "Photogram", Icon: Instagram },
  { title: "Loopit", Icon: TikTok },
  { title: "Careerly", Icon: LinkedIn },
];

export function Footer() {
  return (
    <div className="clear" id="footer" role="contentinfo">
      <div className="cuv-wrap clear">
        <div className="column info">
          <h1 className="logo">
            <Link to="/">Corravale University</Link>
          </h1>
          <nav aria-label="Our Campuses">
            <ul className="campuses">
              <li>
                <Link to="/">
                  <span>Fairhaven</span>
                </Link>
              </li>
              <li>
                <Link to="/_404">
                  <span>Westgate</span>
                </Link>
              </li>
              <li>
                <Link to="/_404">
                  <span>Alden</span>
                </Link>
              </li>
            </ul>
          </nav>
          <ul className="contact">
            <li>
              © 2026{" "}
              <Link to="/_404">
                <span>The Board of Regents of Corravale University</span>
              </Link>{" "}
              1240 Larkspur Ave., Fairhaven, MI 48211-1044
            </li>
            <li>
              <Link to="/about/privacy/">
                <span>
                  <Lock aria-hidden="true" /> Privacy Notice
                </span>
              </Link>
            </li>
            <li className="phone">
              <Phone aria-hidden="true" />
              <span className="hidden-vis">Phone</span>
              <a href="tel:+1-734-764-1817">+1 (734) 764-1817</a>
            </li>
            <li>
              <Link to="/contact/">
                <span>
                  <Envelope aria-hidden="true" /> Contact us
                </span>
              </Link>
            </li>
          </ul>
        </div>
        <div className="column language-social">
          <nav aria-label="Careers and Region Specific Websites">
            <ul className="careers-languages clear">
              <li>
                <Link to="/_404">
                  <span>Careers</span>
                </Link>
              </li>
            </ul>
          </nav>
          <nav aria-label="Social Feeds">
            <ul className="social-icons clear">
              {SOCIAL.map(({ title, Icon }) => (
                <li key={title}>
                  <Link to="/_404" title={title}>
                    <Icon />
                    <span className="hidden-vis">{title}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
        <div className="column mandatory">
          <nav aria-label="Regulatory Compliance Requirements">
            <ul className="clear">
              <li>
                <Link to="/_404" title="Budget and Financial Transparency Disclosures">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 150 150"
                    width="150"
                    height="150"
                    role="img"
                    aria-label="Budget and Financial Transparency Disclosures"
                  >
                    <title>Budget and Financial Transparency Disclosures</title>
                    <circle cx="75" cy="75" r="70" fill="#2b8de0" stroke="#f2a900" strokeWidth="6" />
                    <text
                      x="75"
                      y="45"
                      textAnchor="middle"
                      fontFamily="Arial, Helvetica, sans-serif"
                      fontWeight="700"
                      fontSize="13"
                      fill="#ffffff"
                    >
                      TRANSPARENCY
                    </text>
                    <g fill="#f2a900">
                      <rect x="60" y="80" width="10" height="14" rx="1.5" />
                      <rect x="71" y="72" width="10" height="22" rx="1.5" />
                      <rect x="82" y="64" width="10" height="30" rx="1.5" />
                    </g>
                    <text
                      x="75"
                      y="115"
                      textAnchor="middle"
                      fontFamily="Arial, Helvetica, sans-serif"
                      fontWeight="700"
                      fontSize="12"
                      fill="#f2a900"
                    >
                      BUDGET &amp; SALARY
                    </text>
                  </svg>
                </Link>
              </li>
              <li>
                <Link to="/_404" title="Campus Security Information and Resources">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 150 150"
                    width="150"
                    height="150"
                    role="img"
                    aria-label="Campus Security Information and Resources"
                  >
                    <title>Campus Security Information and Resources</title>
                    <path
                      d="M75 18 L120 34 L120 74 C120 100 100 118 75 128 C50 118 30 100 30 74 L30 34 Z"
                      fill="#2b8de0"
                      stroke="#f2a900"
                      strokeWidth="5"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M52 74 L68 90 L100 54"
                      fill="none"
                      stroke="#ffffff"
                      strokeWidth="9"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <text
                      x="75"
                      y="146"
                      textAnchor="middle"
                      fontFamily="Arial, Helvetica, sans-serif"
                      fontWeight="700"
                      fontSize="15"
                      fill="#ffffff"
                    >
                      CAMPUS SAFETY
                    </text>
                  </svg>
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </div>
  );
}
