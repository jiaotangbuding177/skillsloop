import { type FormEvent } from "react";
import { Link, useRouter } from "@/lib/router";
import { img } from "@/data/assets";
import { ProsePage, PageTitle } from "@/components/Layout";
import { CircleArrowRight } from "@/components/Icons";
import { SearchGlyph } from "@/components/Header";

type GalleryItem = { src: string; alt: string; time?: string };

/* ---------------- Gallery section (Onward Now / Seize the Day) ---------------- */
export function HomeGallery({
  title,
  items,
  heading = "All Corravale, all the time",
  blurb = "There's always something remarkable unfolding at Corravale. Whether it's across our campuses or somewhere far beyond them, our students, faculty, staff and alumni are busy chasing what's next. A selection of moments gathered over the years fills the gallery below.",
}: {
  title: string;
  items: GalleryItem[];
  heading?: string;
  blurb?: string;
}) {
  return (
    <section aria-label={title} className="bg-white py-10">
      <h2 className="mb-8 text-center font-cond text-[26px] tracking-[0.22em] text-[#555] uppercase">
        {title}
      </h2>
      <div className="mx-auto max-w-[1180px] px-5">
        <div className="mb-8 grid items-center gap-6 md:grid-cols-[220px_1fr]">
          <div className="flex items-center gap-6">
            <img src={img.blockm} alt="Block C" className="h-[96px] w-[96px] object-contain" />
            <img src={img.hours24} alt="24 Hours" className="h-[96px] w-[96px] object-contain" />
          </div>
          <div>
            <h3 className="mb-3 font-cond text-[22px] tracking-[0.08em] text-navy uppercase">
              {heading}
            </h3>
            <p className="text-[14px] leading-relaxed text-[#333]">{blurb}</p>
          </div>
        </div>
        <ul className="grid grid-cols-2 gap-[3px] md:grid-cols-4 lg:grid-cols-6">
          {items.map((g) => (
            <li key={(g.time ?? "") + g.src} className="group relative cursor-pointer overflow-hidden">
              <img src={g.src} alt={g.alt} className="h-[150px] w-full object-cover transition group-hover:scale-105" loading="lazy" />
              {g.time && (
                <span className="absolute bottom-0 left-0 bg-[#0b1b2b]/75 px-2 py-1 font-cond text-[12px] text-white">
                  {g.time}
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

/* ---------------- Contact ---------------- */
const departments: {
  name: string;
  to?: string;
  phone?: string;
  email?: string;
  website?: string;
  chat?: string;
}[] = [
  { name: "Operators", phone: "734-764-1817" },
  { name: "Undergraduate Admissions", to: "/_404.html", phone: "734-764-7433" },
  { name: "Graduate Admissions", to: "/_404.html", phone: "734-764-8129", email: "admissions@corravale.edu" },
  { name: "Central Information Desk", to: "/_404.html", phone: "734-764-INFO (4636)", email: "info@corravale.edu" },
  { name: "Aid & Funding", to: "/_404.html", phone: "734-763-6600", email: "financial.aid@corravale.edu" },
  { name: "Housing & Residence", to: "/_404.html", phone: "734-763-3164", email: "housing@corravale.edu" },
  { name: "Technology Support Desk", to: "/_404.html", phone: "734-764-HELP (4357)", email: "ithelp@corravale.edu", chat: "Chat with a support agent" },
  { name: "Web Accessibility", to: "/_404.html", website: "Report a Web Accessibility Issue" },
  { name: "Corravale News", to: "/_404.html", phone: "734-764-7260" },
  { name: "Social Media Listings", to: "/_404.html" },
  { name: "Corravale Health", to: "/_404.html", phone: "734-936-6641" },
];

export function ContactPage() {
  return (
    <>
      <PageTitle>Contact Us</PageTitle>
      <section className="bg-[#333] py-8">
        <div className="mx-auto max-w-[1180px] px-5">
          <p className="mb-8 text-[14px] leading-relaxed text-white/85">
            Have a question but unsure where to start or whom to reach? To point you in the right direction,
            we've gathered some of the most frequently contacted Corravale departments in the table below.
            Should you not find the office tied to your particular need, please try our site search to locate
            the right resource.
          </p>
          <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
            <nav aria-label="Most Frequently Reached Campus" className="bg-navy-panel">
              <h4 className="bg-[#123a66] px-4 py-2 font-cond text-[13px] tracking-[0.1em] text-maize uppercase">
                Most Frequently Reached Campus
              </h4>
              <dl className="px-4">
                {departments.map((d) => (
                  <div
                    key={d.name}
                    className="grid gap-1 border-b border-white/15 py-[10px] sm:grid-cols-[1fr_auto] sm:items-center"
                  >
                    <dt className="sr-only">Department</dt>
                    <dd className="text-[13.5px] text-maize">
                      {d.to ? <Link to={d.to} className="hover:underline">{d.name}</Link> : d.name}
                    </dd>
                    <dd className="flex flex-wrap justify-end gap-x-5 text-[13px] text-white/85">
                      {d.phone && <span>{d.phone}</span>}
                      {d.email && <span>{d.email}</span>}
                      {d.website && <Link to="/_404.html" className="text-maize hover:underline">{d.website}</Link>}
                      {d.chat && <Link to="/_404.html" className="text-maize hover:underline">{d.chat}</Link>}
                    </dd>
                  </div>
                ))}
              </dl>
            </nav>
            <nav aria-label="More Contact Options and Links">
              <h4 className="mb-3 font-cond text-[13px] tracking-[0.1em] text-white uppercase">
                More Contact Options and Links
              </h4>
              <ul className="mb-6 space-y-1">
                {[
                  ["Find a Department or Unit", "/schools-colleges/"],
                  ["Find People on Campus", "/_404.html"],
                  ["Request Transcripts", "/_404.html"],
                  ["Public Records Requests", "/_404.html"],
                ].map(([l, to]) => (
                  <li key={l}>
                    <Link to={to} className="flex items-center justify-between gap-2 text-[14px] text-maize hover:underline">
                      {l} <CircleArrowRight size={13} />
                    </Link>
                  </li>
                ))}
              </ul>
              <h4 className="mb-2 font-cond text-[13px] tracking-[0.1em] text-maize uppercase">Mailing Addresses</h4>
              <p className="mb-6 text-[13.5px] leading-relaxed text-white/85">
                Every campus office at Corravale maintains a unique mailing address. Please{" "}
                <Link to="/search/" className="text-maize underline">browse</Link> our website for a college or
                unit page to locate the mailing addresses for specific offices.
              </p>
              <h4>
                <Link to="/_404.html" className="flex items-center justify-between gap-2 font-cond text-[13px] tracking-[0.1em] text-white uppercase hover:underline">
                  Getting Here/Maps/Directions <CircleArrowRight size={13} className="text-maize" />
                </Link>
              </h4>
            </nav>
          </div>
        </div>
      </section>
    </>
  );
}

/* ---------------- Search ---------------- */
export function SearchPage() {
  const { navigate } = useRouter();

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const value = new FormData(e.currentTarget).get("keywords");
    const q = typeof value === "string" ? value.trim() : "";
    navigate(q ? `/search/?keywords=${encodeURIComponent(q)}` : "/search/?keywords=");
  }

  return (
    <>
      <PageTitle>Search</PageTitle>
      <section className="min-h-[420px] bg-[#f4f4f4] py-10">
        <div className="mx-auto max-w-[1440px] px-4">
          <form onSubmit={onSubmit} role="search">
            <ul>
              <li className="flex items-center gap-3">
                <label htmlFor="site-search" className="text-[15px] text-[#333]">
                  Keywords
                </label>
                <span className="flex h-[26px] items-center border border-[#8a8a8a] bg-white pl-2">
                  <input
                    id="site-search"
                    name="keywords"
                    type="text"
                    className="h-full w-[218px] bg-transparent text-[14px] text-[#333] outline-none"
                  />
                  <button
                    type="submit"
                    aria-label="Search"
                    className="grid h-full w-[24px] place-items-center text-[#333]"
                  >
                    <SearchGlyph />
                  </button>
                </span>
              </li>
            </ul>
          </form>
        </div>
      </section>
    </>
  );
}

/* ---------------- Privacy Notice ---------------- */
export function PrivacyPage() {
  return (
    <ProsePage title="Corravale Privacy Notice">
      <p className="mb-4">Last Revision Date — May 12, 2024</p>
      <p className="mb-6">
        Corravale University recognizes and values the privacy of its community members and guests. We work
        to set the standard in the ways we handle your personal information. We are dedicated to transparency
        by helping you understand what personal information we gather, how we make use of it, and when we
        choose to share it.
      </p>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">At a Glance</h4>
      <p className="mb-3">If you don't have time for the full privacy notice below, here is what you should know:</p>
      <ul className="mb-6 list-disc space-y-2 pl-6">
        <li>Corravale University is a large institution that operates many different websites. This notice applies to our primary website, corravale.edu. Individual Corravale units and organizations may maintain their own privacy notices.</li>
        <li>Our aim is to limit the information we gather to only what we need to support our academic, research, and healthcare missions.</li>
        <li>We are committed to using your personal information only for the purposes for which it was originally gathered.</li>
        <li>We never sell your personal information, and when we share it beyond Corravale, we do so only to enable operations and services carried out on the university's behalf, to satisfy legal obligations, or to protect the safety, property, or rights of the university, its community and guests.</li>
        <li>We aim to provide you <Link to="/about/privacy/#choices" className="text-[#1a5fa8] underline">choices</Link> regarding the personal information gathered on our website.</li>
        <li>If you have questions or concerns about your privacy on the corravale.edu website, please contact the <Link to="/_404.html" className="text-[#1a5fa8] underline">Data Privacy Office</Link>.</li>
      </ul>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Reach</h4>
      <p className="mb-3">
        This privacy notice explains how we handle personal information gathered on the Corravale primary
        website (corravale.edu). The broader <Link to="/about/privacy-statement/" className="text-[#1a5fa8] underline">privacy overview</Link>{" "}
        outlines the activities carried out across Corravale that involve the gathering and processing of your
        personal information.
      </p>
      <p className="mb-6">
        Corravale schools, departments, units, clubs, labs, and other groups may keep privacy notices specific
        to their own collection and processing of your personal information, especially where it differs from
        the practices set out in this notice.
      </p>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Information That We Gather</h4>
      <p className="mb-3">The Corravale website gathers personal information through the following channels:</p>
      <ul className="mb-6 list-disc space-y-2 pl-6">
        <li>When you provide it to us directly, such as when you subscribe to a newsletter. This information may include your name and contact details.</li>
        <li>
          When technology records your information <em>in real time</em>, such as when a small file is stored
          on your device. Information gathered this way may include:
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>The network domain you use</li>
            <li>The device's IP address</li>
            <li>The browser you use</li>
            <li>The visit's date and time</li>
            <li>The address of the site that referred you to corravale.edu.</li>
          </ul>
        </li>
        <li>
          Once <em>external advertising and analytics partners</em>, such as PageMetrics, gather your
          information on our behalf. Examples of the details collected by these external service partners
          include:
          <ul className="mt-2 list-disc space-y-1 pl-6">
            <li>Pages viewed during the session</li>
            <li>Time and date of access</li>
            <li>Total time spent browsing the site</li>
            <li>Approximate location from IP address</li>
            <li>General demographic data</li>
            <li>Search queries typed into the site.</li>
          </ul>
        </li>
      </ul>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">How Your Information Is Used</h4>
      <ul className="mb-6 list-disc space-y-2 pl-6">
        <li>Keep our website running smoothly by tracking site performance and improving its functionality and overall user experience.</li>
        <li>Connect more effectively with prospective students and the wider global community by sharing relevant details about university services, events, and academic programs.</li>
        <li>On occasion we may use personal information for other legitimate and clearly defined purposes. When such cases arise, we will make every effort to notify you.</li>
      </ul>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Parties We Share Your Information With</h4>
      <p className="mb-3">
        We neither sell nor rent the personal information collected here. We may share it with service
        providers that help support our operations and activities. We ask every service provider to keep your
        personal information secure and to use or share it solely to deliver services on our behalf.
      </p>
      <p className="mb-6">
        We may also disclose your personal information when the law requires it, or when we believe doing so
        will help safeguard the safety, property, or rights of the university, members of the university
        community, and university guests.
      </p>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">The Choices You Are Able to Make About Your Data</h4>
      <p className="mb-3">
        When you browse corravale.edu, "cookies" are stored on your computer or device. Cookies are small
        files that record information about your visits and interactions with the site.
      </p>
      <h5 className="mt-4 mb-2 font-cond text-[16px] text-[#444]">Our Cookies</h5>
      <table className="mb-6 w-full border-collapse text-[13px]">
        <thead>
          <tr className="bg-[#e6e6e6] text-left">
            <th className="border border-[#ccc] p-2">Cookie label</th>
            <th className="border border-[#ccc] p-2">Function</th>
            <th className="border border-[#ccc] p-2">Lifespan</th>
          </tr>
        </thead>
        <tbody>
          {[
            ["alerts-collapsed", "Stores whether the user has dismissed the alert bar.", "Session (cleared once you close your browser)"],
            ["cv_privacy_consent", "Saves the visitor's current consent choice.", "1 Year"],
            ["um_cookie_consent", "Saves the visitor's current consent choice. (deprecated)", "1 Year"],
          ].map((r) => (
            <tr key={r[0]}>
              {r.map((c, i) => (
                <td key={i} className="border border-[#ccc] p-2 align-top">{c}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <h5 className="mt-4 mb-2 font-cond text-[16px] text-[#444]">Third-Party Trackers</h5>
      <table className="mb-6 w-full border-collapse text-[13px]">
        <thead>
          <tr className="bg-[#e6e6e6] text-left">
            <th className="border border-[#ccc] p-2">Cookie type</th>
            <th className="border border-[#ccc] p-2">Purpose</th>
            <th className="border border-[#ccc] p-2">Opt-out</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="border border-[#ccc] p-2 align-top">Cloudvane Cookies</td>
            <td className="border border-[#ccc] p-2 align-top">
              Cloudvane relies on many <Link to="/_404.html" className="text-[#1a5fa8] underline">cookies</Link>{" "}
              to optimize network capacity, balance traffic loads, and shield sites from malicious requests.
              See Cloudvane's <Link to="/_404.html" className="text-[#1a5fa8] underline">privacy policy</Link>.
            </td>
            <td className="border border-[#ccc] p-2 align-top">
              These <Link to="/_404.html" className="text-[#1a5fa8] underline">cookies</Link> are treated as strictly essential.
            </td>
          </tr>
          <tr>
            <td className="border border-[#ccc] p-2 align-top">AdReach Ad Cookies</td>
            <td className="border border-[#ccc] p-2 align-top">
              AdReach, which is operated by Verano, uses cookies to refine advertising. These cookies gather
              information tied to your browsing activity and keep it linked to your unique cookie ID. See
              AdReach's <Link to="/_404.html" className="text-[#1a5fa8] underline">cookie policy</Link>.
            </td>
            <td className="border border-[#ccc] p-2 align-top">
              You can opt out of Verano's ad personalization within Verano Ads{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">Settings</Link>.
            </td>
          </tr>
          <tr>
            <td className="border border-[#ccc] p-2 align-top">Verano Analytics Cookies</td>
            <td className="border border-[#ccc] p-2 align-top">
              Verano Analytics cookies tally visits and referral sources so we can measure and improve how our
              website performs. See details about Verano Analytics'{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">use of cookies across websites</Link> and{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">privacy policy</Link>.
            </td>
            <td className="border border-[#ccc] p-2 align-top">
              Learn more about controlling{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">cookies within your browser</Link>.
            </td>
          </tr>
          <tr>
            <td className="border border-[#ccc] p-2 align-top">ClickMap Cookies</td>
            <td className="border border-[#ccc] p-2 align-top">
              ClickMap Cookies reveal insights into how visitors use our website. See here the{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">Privacy Policy</Link> and the{" "}
              <Link to="/_404.html" className="text-[#1a5fa8] underline">Cookie Policy</Link> of ClickMap.
            </td>
            <td className="border border-[#ccc] p-2 align-top">
              Learn here about how to <Link to="/_404.html" className="text-[#1a5fa8] underline">opt out</Link>.
            </td>
          </tr>
        </tbody>
      </table>
      <h5 className="mt-4 mb-2 font-cond text-[16px] text-[#444]">Adjust Privacy Preferences</h5>
      <p className="mb-2">Here you can control which categories of cookies our website places on your device.</p>
      <button className="mb-6 border border-[#999] bg-[#eee] px-4 py-2 text-[14px]">Privacy Preferences</button>
      <h5 className="mt-4 mb-2 font-cond text-[16px] text-[#444]">Social Sharing Tools</h5>
      <p className="mb-6">
        Several pages across our website include embedded buttons for sharing content on social media. When
        you use these buttons, the social media platforms may store cookies or apply other tracking
        technologies on your device. For details on how a particular platform uses cookies, please review the
        cookie policies of <Link to="/_404.html" className="text-[#1a5fa8] underline">Z</Link>,{" "}
        <Link to="/_404.html" className="text-[#1a5fa8] underline">Streamly</Link>,{" "}
        <Link to="/_404.html" className="text-[#1a5fa8] underline">Pinstack</Link>,{" "}
        <Link to="/_404.html" className="text-[#1a5fa8] underline">Careerly</Link>,{" "}
        <Link to="/_404.html" className="text-[#1a5fa8] underline">Photogram</Link> and{" "}
        <Link to="/_404.html" className="text-[#1a5fa8] underline">Vidcast</Link>.
      </p>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">How We Protect and Safeguard Your Data</h4>
      <p className="mb-6">
        Corravale University understands how vital it is to safeguard the information gathered across our
        community. We work diligently to shield your data from unauthorized access, loss, or misuse, and we
        maintain sensible safeguards designed to keep the personal information you share with us protected at
        all times.
      </p>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Changes to This Notice</h4>
      <p className="mb-6">
        We may revise this privacy notice periodically as our practices evolve. The date of the most recent
        revision will always appear near the top of this page for your reference.
      </p>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Who to Reach with Questions or Concerns</h4>
      <p className="mb-6">
        If you have concerns or questions about how your personal information is handled, please reach out to
        the <Link to="/_404.html" className="text-[#1a5fa8] underline">Data Privacy Office</Link>.
      </p>
      <h4 className="mt-6 mb-2 font-cond text-[18px] text-[#00274c]">Specific Notices</h4>
      <ul className="list-disc space-y-2 pl-6">
        <li><Link to="/about/privacy-statement/#coppa" className="text-[#1a5fa8] underline">Individuals under the age of 13 or their parents or guardians</Link></li>
        <li><Link to="/about/privacy-statement/#eu" className="text-[#1a5fa8] underline">Individuals within the European Union</Link></li>
      </ul>
    </ProsePage>
  );
}
