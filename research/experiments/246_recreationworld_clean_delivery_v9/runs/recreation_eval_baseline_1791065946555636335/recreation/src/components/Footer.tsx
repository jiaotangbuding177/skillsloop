import { Link } from "@/router";
import { campuses, socialFeeds } from "@/data/site";
import { asset } from "@/assets";
import { Brand, LockIcon, MailIcon, PhoneIcon } from "./Icons";

export function Footer() {
  return (
    <footer className="border-t-[20px] border-black bg-[#00274c] py-[20px] font-[Roboto] text-[11px] leading-[16px] text-white">
      <div className="mx-auto flex max-w-[1200px] flex-wrap px-[10px]">
        <div className="w-full pb-[10px] lg:w-1/2">
          <div className="float-left">
            <h4 className="m-0">
              <Link
                to="/"
                className="block h-[92px] w-[87px] border border-white bg-[#00274c] bg-[length:100%_100%]"
                style={{ textIndent: "-9000px", backgroundImage: `url(${asset("/skins/um2013/media/images/umich-logo.png")})` }}
              >
                Corravale University
              </Link>
            </h4>
          </div>
          <ul className="ml-[106px] list-none p-0">
            <li className="mb-[5px] flex flex-wrap gap-x-[10px]">
              {campuses.map((c, i) => (
                <span key={c.label} className={`${i < campuses.length - 1 ? "border-r border-white pr-[10px]" : ""}`}>
                  <Link to={c.to} className="inline text-white no-underline hover:text-[#ffcb0b]">
                    {c.label}
                  </Link>
                </span>
              ))}
            </li>
            <li>
              <span>© 2026 </span>
              <Link to="/_404.html" className="inline text-white no-underline hover:text-[#ffcb0b]">
                The Board of Regents of Corravale University
              </Link>
              <span> 1240 Larkspur Ave., Fairhaven, MI 48211-1044</span>
            </li>
            <li>
              <Link to="/about/privacy/" className="inline text-white no-underline hover:text-[#ffcb0b]">
                <LockIcon className="mr-[5px] inline text-[#ffcb0b]" />
                <span className="hover:border-b hover:border-dotted hover:border-[#ffcb0b]">Privacy Notice</span>
              </Link>
            </li>
            <li className="flex items-center">
              <PhoneIcon className="mr-[5px] text-[#ffcb0b]" />
              <span>Phone</span>
              <Link to="tel:+1-734-764-1817" className="ml-[6px] inline text-white no-underline hover:text-[#ffcb0b]">
                +1 (734) 764-1817
              </Link>
            </li>
            <li>
              <Link to="/contact/" className="inline text-white no-underline hover:text-[#ffcb0b]">
                <MailIcon className="mr-[5px] inline text-[#ffcb0b]" />
                <span className="hover:border-b hover:border-dotted hover:border-[#ffcb0b]">Contact us</span>
              </Link>
            </li>
          </ul>
        </div>

        <div className="w-full pb-[10px] lg:w-1/2">
          <nav aria-label="Careers">
            <ul className="m-0 list-none p-0">
              <li className="break-inside-avoid border-b border-dotted border-[#8e8c8c] py-[10px]">
                <Link to="/_404.html" className="block text-white no-underline hover:text-[#ffcb0b]">
                  <span className="hover:border-b hover:border-dotted hover:border-[#ffcb0b]">Careers</span>
                </Link>
              </li>
            </ul>
          </nav>
          <nav aria-label="Social Feeds" className="mt-[10px]">
            <ul className="m-0 flex list-none flex-wrap justify-center gap-[8px] p-0 lg:justify-start">
              {socialFeeds.map((s) => (
                <li key={s}>
                  <Link
                    to="/_404.html"
                    className="flex h-[26px] w-[26px] items-center justify-center rounded-full bg-white/10 text-white no-underline hover:bg-[#ffcb0b] hover:text-[#00274c]"
                  >
                    <span className="hidden-label">{s}</span>
                    <Brand name={s} />
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <nav aria-label="Regulatory Compliance Requirements" className="w-full pt-[10px]">
          <ul className="m-0 flex list-none flex-wrap justify-center gap-[20px] p-0 lg:justify-start">
            <li>
              <Link to="/_404.html" className="block text-white no-underline">
                <span className="flex h-[130px] w-[130px] flex-col items-center justify-center rounded-full border-[5px] border-[#ffcb0b] bg-[#1c4f8f] text-center">
                  <span className="text-[13px] font-bold leading-[15px] tracking-[0.5px]">TRANSPARENCY</span>
                  <span className="mt-[6px] text-[26px] leading-none text-[#ffcb0b]">▮▮▮</span>
                  <span className="mt-[6px] text-[12px] font-bold leading-[15px] text-[#ffcb0b]">BUDGET &amp; SALARY</span>
                </span>
              </Link>
            </li>
            <li>
              <Link to="/_404.html" className="flex flex-col items-center text-white no-underline">
                <span
                  className="flex h-[120px] w-[110px] items-center justify-center bg-[#1c4f8f]"
                  style={{ clipPath: "polygon(50% 0%, 100% 14%, 100% 62%, 50% 100%, 0% 62%, 0% 14%)" }}
                >
                  <span className="text-[54px] leading-none text-white">✓</span>
                </span>
                <span className="mt-[6px] text-[12px] font-bold tracking-[0.5px]">CAMPUS SAFETY</span>
              </Link>
            </li>
          </ul>
        </nav>
      </div>
    </footer>
  );
}
