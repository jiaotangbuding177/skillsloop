import { Link } from "@/router";
import { privacyBlocks } from "@/data/privacy";
import { navGroups } from "@/data/navGroups";
import { contactLinks, contactRows } from "@/data/site";
import { ChevronCircle, MailIcon } from "@/components/Icons";


function PanelShell({
  title,
  tone = "dark",
  intro,
  children,
}: {
  title: string;
  tone?: "dark" | "light";
  intro?: string;
  children?: React.ReactNode;
}) {
  return (
    <>
      <div className="px-[10px] pt-[10px] text-center text-[15px] uppercase tracking-[6px]">
        <h2 className={`font-['Roboto_Condensed'] text-[30px] font-normal ${tone === "dark" ? "text-[#3f6ea6]" : "text-[#3f6ea6]"}`}>
          {title}
        </h2>
      </div>
      <hr className="mx-auto my-[10px] max-w-[1200px] border-[#9a9a9a]" />
      {intro ? (
        <p className="mx-auto max-w-[1100px] px-[10px] py-[10px] text-center text-[16px] leading-[1.6] text-[#333]">{intro}</p>
      ) : null}
      {children}
    </>
  );
}

export function SchoolsCollegesPage() {
  const groups = navGroups["/schools-colleges/"] ?? [];
  return (
    <div className="bg-white pb-[40px]">
      <div className="mx-auto max-w-[1200px]">
        <PanelShell
          title="Schools & Colleges"
          intro="Students discover their passions and chart their futures across our 19 nationally recognized schools and colleges — the heart and soul of the Corravale experience at our flagship campus. Meanwhile, our Corravale Westgate and Corravale Alden campuses offer inspiration and direction to more than 15,000 students."
        />
        <div className="flex flex-wrap gap-[10px] px-[10px]">
          {groups.map((g) => (
            <div key={g.title} className="w-full sm:w-[calc(50%-5px)] lg:w-[calc(33.333%-7px)]">
              <div className="h-full rounded-[2px] border border-[#e1e1e1] bg-[#f6f6f6] p-[15px]">
                <h4 className="m-0 border-b border-[#c9c9c9] pb-[10px] text-[16px] font-bold uppercase text-[#00274c]">{g.title}</h4>
                <ul className="m-0 list-none p-0">
                  {g.items.map((it, i) => (
                    <li key={it.label + i} className="py-[8px] text-[16px]">
                      <Link to={it.to} className="flex items-start justify-between gap-[8px] text-[#0d57aa] no-underline hover:underline">
                        <span>{it.label}</span>
                        <ChevronCircle className="mt-[3px] shrink-0 text-[#ffcb0b]" />
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ContactPage() {
  return (
    <div className="bg-white pb-[40px]">
      <div className="mx-auto max-w-[1200px]">
        <PanelShell
          title="Contact Us"
          intro="Have a question but unsure where to start or whom to reach? To point you in the right direction, we've gathered some of the most frequently contacted Corravale departments in the table below. Should you not find the office tied to your particular need, please try our site search to locate the right resource."
        />
        <div className="px-[10px]">
          <h3 className="py-[16px] text-center text-[24px] font-normal text-[#00274c]">Most Frequently Reached Campus</h3>
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="border border-[#c9c9c9] bg-[#00274c] px-[12px] py-[10px] text-left text-[16px] text-white">Department</th>
                <th className="border border-[#c9c9c9] bg-[#00274c] px-[12px] py-[10px] text-left text-[16px] text-white">Phone</th>
              </tr>
            </thead>
            <tbody>
              {contactRows.map((r, i) => (
                <tr key={r.dept} className={i % 2 ? "bg-[#f4f6f9]" : "bg-white"}>
                  <td className="border border-[#c9c9c9] px-[12px] py-[10px] text-[16px] text-[#333]">
                    <span className="block text-[12px] uppercase text-[#777]">Department</span>
                    {r.dept}
                  </td>
                  <td className="border border-[#c9c9c9] px-[12px] py-[10px] text-[16px] text-[#333]">
                    {r.phone ? (
                      <>
                        <span className="block text-[12px] uppercase text-[#777]">Phone</span>
                        <a href={`tel:${r.phone}`} className="text-[#0d57aa] no-underline hover:underline">
                          {r.phone}
                        </a>
                      </>
                    ) : null}
                    {r.email ? (
                      <a href={`mailto:${r.email}`} className="mt-[4px] block text-[#0d57aa] no-underline hover:underline">
                        {r.email}
                      </a>
                    ) : null}
                    {r.chat ? (
                      <Link to="/_404.html" className="mt-[4px] block text-[#0d57aa] no-underline hover:underline">
                        <MailIcon className="mr-[5px] inline" />
                        {r.chat}
                      </Link>
                    ) : null}
                    {r.website ? (
                      <Link to="/_404.html" className="text-[#0d57aa] no-underline hover:underline">
                        {r.website}
                      </Link>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3 className="py-[16px] text-[24px] font-normal text-[#00274c]">More Contact Options and Links</h3>
          <ul className="m-0 list-disc pl-[24px]">
            {contactLinks.map((l) => (
              <li key={l} className="py-[4px] text-[16px]">
                <Link to="/_404.html" className="text-[#0d57aa] no-underline hover:underline">
                  {l}
                </Link>
              </li>
            ))}
          </ul>

          <h3 className="py-[16px] text-[24px] font-normal text-[#00274c]">Mailing Addresses</h3>
          <p className="text-[16px] leading-[1.6] text-[#333]">
            Every campus office at Corravale maintains a unique mailing address. Please{" "}
            <Link to="/_404.html" className="text-[#0d57aa] no-underline hover:underline">
              browse
            </Link>{" "}
            our website for a college or unit page to locate the mailing addresses for specific offices.
          </p>
          <h3 className="py-[16px] text-[24px] font-normal text-[#00274c]">Getting Here/Maps/Directions</h3>
          <p className="text-[16px] leading-[1.6] text-[#333]">
            1240 Larkspur Ave., Fairhaven, MI 48211-1044 ·{" "}
            <Link to="/_404.html" className="text-[#0d57aa] no-underline hover:underline">
              Maps &amp; Directions
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export function PrivacyPage() {
  const nodes: React.ReactNode[] = [];
  let listBuffer: string[] = [];
  const flush = (key: string) => {
    if (listBuffer.length) {
      nodes.push(
        <ul key={key} className="my-[10px] list-disc pl-[24px]">
          {listBuffer.map((t, i) => (
            <li key={i} className="py-[4px]">
              {t}
            </li>
          ))}
        </ul>
      );
      listBuffer = [];
    }
  };
  privacyBlocks.forEach((b, i) => {
    if (b.tag === "li") {
      listBuffer.push(b.text);
      return;
    }
    flush("ul" + i);
    if (b.tag === "h2") {
      nodes.push(
        <h2 key={i} className="py-[20px] font-['Roboto_Condensed'] text-[32px] font-normal text-[#00274c]">
          {b.text}
        </h2>
      );
    } else if (b.tag === "h4") {
      nodes.push(
        <h4 key={i} className="py-[16px] text-[20px] font-bold text-[#00274c]">
          {b.text}
        </h4>
      );
    } else {
      nodes.push(
        <p key={i} className="py-[8px] leading-[1.7]">
          {b.text}
        </p>
      );
    }
  });
  flush("ul-end");
  return (
    <div className="bg-white pb-[40px]">
      <div className="mx-auto max-w-[900px] px-[10px] text-[16px] text-[#333]">{nodes}</div>
    </div>
  );
}

export function NotFoundPage() {
  return (
    <div className="flex min-h-[600px] flex-col items-center justify-center bg-[#f7f8fa] px-[20px] py-[60px] text-center">
      <p className="text-[80px] font-bold leading-none text-[#c9ced6]">404</p>
      <h1 className="py-[10px] text-[26px] font-bold text-[#1f2b3a]">Page Not Available</h1>
      <p className="max-w-[520px] text-[16px] leading-[1.6] text-[#555]">
        This page could not be downloaded for offline viewing. It may be an external link, a backend-dependent feature, or a page that
        requires authentication.
      </p>
      <div className="mt-[24px] max-w-[520px] rounded-[6px] border border-[#e3e6ea] bg-white p-[16px] text-left">
        <p className="font-bold text-[#1f2b3a]">Why am I seeing this?</p>
        <p className="text-[15px] text-[#666]">
          This site is served as a self-contained offline preview. Some pages cannot be fully replicated in offline mode.
        </p>
      </div>
      <div className="mt-[24px] flex items-center gap-[16px]">
        <button
          type="button"
          onClick={() => window.history.back()}
          className="rounded-[6px] bg-[#1f3a5f] px-[20px] py-[10px] text-[15px] font-medium text-white"
        >
          Go Back
        </button>
        <Link to="/" className="text-[15px] font-medium text-[#1f3a5f] no-underline hover:underline">
          Home
        </Link>
      </div>
    </div>
  );
}
